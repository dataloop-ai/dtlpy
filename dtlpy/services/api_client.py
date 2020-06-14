"""
Dataloop platform calls
"""
import aiohttp.client_exceptions
import requests_toolbelt
import multiprocessing
import threading
import traceback
import datetime
import requests
import aiohttp
import logging
import asyncio
import time
import tqdm
import json
import jwt
import os
import io
from multiprocessing.pool import ThreadPool
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from functools import wraps
import numpy as np

from .calls_counter import CallsCounter
from .cookie import CookieIO
from .logins import login, login_secret
from .async_utils import AsyncResponse, AsyncUploadStream, AsyncResponseError, AsyncThreadEventLoop
from .default_environments import DEFAULT_ENVIRONMENT
from .aihttp_retry import RetryClient
from .. import miscellaneous, exceptions, __version__

logger = logging.getLogger(name=__name__)
threadLock = threading.Lock()


class PlatformError(Exception):
    """
    Error handling for api calls
    """

    def __init__(self, resp):
        msg = ''
        if hasattr(resp, 'status_code'):
            msg += '<Response [{}]>'.format(resp.status_code)
        if hasattr(resp, 'reason'):
            msg += '<Reason [{}]>'.format(resp.reason)
        elif hasattr(resp, 'text'):
            msg += '<Reason [{}]>'.format(resp.text)
        super().__init__(msg)


class Verbose:
    __DEFAULT_LOGGING_LEVEL = 'warning'
    __DEFAULT_DISABLE_PROGRESS_BAR = False
    __DEFAULT_PRINT_ALL_RESPONSES = False

    def __init__(self, cookie):
        self.cookie = cookie
        dictionary = self.cookie.get('verbose')
        if isinstance(dictionary, dict):
            self.from_cookie(dictionary)
        else:
            self._logging_level = self.__DEFAULT_LOGGING_LEVEL
            self._disable_progress_bar = self.__DEFAULT_DISABLE_PROGRESS_BAR
            self._print_all_responses = self.__DEFAULT_PRINT_ALL_RESPONSES
            self.to_cookie()

    def to_cookie(self):
        dictionary = {'logging_level': self._logging_level,
                      'disable_progress_bar': self._disable_progress_bar,
                      'print_all_responses': self._print_all_responses}
        self.cookie.put(key='verbose', value=dictionary)

    def from_cookie(self, dictionary):
        self._logging_level = dictionary.get('logging_level', self.__DEFAULT_LOGGING_LEVEL)
        self._disable_progress_bar = dictionary.get('disable_progress_bar', self.__DEFAULT_DISABLE_PROGRESS_BAR)
        self._print_all_responses = dictionary.get('print_all_responses', self.__DEFAULT_PRINT_ALL_RESPONSES)

    @property
    def disable_progress_bar(self):
        return self._disable_progress_bar

    @disable_progress_bar.setter
    def disable_progress_bar(self, val):
        self._disable_progress_bar = val
        self.to_cookie()

    @property
    def logging_level(self):
        return self._logging_level

    @logging_level.setter
    def logging_level(self, val):
        self._logging_level = val
        # set log level
        logging.getLogger('dtlpy').handlers[0].setLevel(logging._nameToLevel[self._logging_level.upper()])
        # write to cookie
        self.to_cookie()

    @property
    def print_all_responses(self):
        return self._print_all_responses

    @print_all_responses.setter
    def print_all_responses(self, val):
        self._print_all_responses = val
        self.to_cookie()


class Decorators:
    @staticmethod
    def token_expired_decorator(method):
        @wraps(method)
        def decorated_method(inst, *args, **kwargs):
            # before the method call
            if inst.token_expired():
                if inst.renew_token_method() is False:
                    raise exceptions.PlatformException('600', 'Token expired, Please login.'
                                                              '\nSDK login options: dl.login(), dl.login_token(), '
                                                              'dl.login_secret()'
                                                              '\nCLI login options: dlp login, dlp login-token, '
                                                              'dlp login-secret')
            # the actual method call
            result = method(inst, *args, **kwargs)
            # after the method call
            return result

        return decorated_method


class ApiClient:
    """
    API calls to Dataloop gate
    """

    def __init__(self, token=None, num_processes=None, cookie_filepath=None):
        ############
        # Initiate #
        ############
        # define local params - read only once from cookie file
        self.renew_token_method = self.renew_token
        self.is_cli = False
        self.session = None
        self._token = None
        self._environments = None
        self._environment = None
        self._environments = None
        self._verbose = None
        self._fetch_entities = None
        # define other params
        self.last_response = None
        self.last_request = None
        self.platform_exception = None
        self.last_curl = None
        self.minimal_print = True
        # start refresh token
        self.refresh_token_active = True
        # event and pools
        self._thread_pools = dict()
        self._event_loops_dict = dict()

        # TODO- remove before release - only for debugging
        self._stopped_pools = list()

        if cookie_filepath is None:
            self.cookie_io = CookieIO.init()
        else:
            self.cookie_io = CookieIO(path=cookie_filepath)
        assert isinstance(self.cookie_io, CookieIO)
        self.state_io = CookieIO.init_local_cookie(create=False)
        assert isinstance(self.state_io, CookieIO)

        ##################
        # configurations #
        ##################
        # read URL
        environment = self.environment
        if environment is None:
            self.setenv('prod')

        # check for proxies in connection
        self.check_proxy()

        # set token if input
        if token is not None:
            self.token = token

        # validate token
        self.token_expired()

        # STDOUT
        self.remove_keys_list = ['contributors', 'url', 'annotations', 'items', 'export', 'directoryTree',
                                 'attributes', 'partitions', 'metadata', 'stream', 'createdAt', 'updatedAt', 'arch']

        # API calls counter
        counter_filepath = os.path.join(os.path.dirname(self.cookie_io.COOKIE), 'calls_counter.json')
        self.calls_counter = CallsCounter(filepath=counter_filepath)

        # create a global thread pool to run multi threading
        if num_processes is None:
            num_processes = 4 * multiprocessing.cpu_count()
        self._num_processes = num_processes
        self._thread_pools_names = {'item.download': num_processes,
                                    'item.status_update': num_processes,
                                    'item.page': num_processes,
                                    'annotation.upload': num_processes,
                                    'annotation.download': num_processes,
                                    'annotation.update': num_processes,
                                    'entity.create': num_processes}
        # set logging level
        logging.getLogger('dtlpy').handlers[0].setLevel(logging._nameToLevel[self.verbose.logging_level.upper()])

    def __del__(self):
        for name, pool in self._thread_pools.items():
            pool.close()
            pool.terminate()
        for name, thread in self._event_loops_dict.items():
            thread.stop()

    @property
    def num_processes(self):
        return self._num_processes

    @num_processes.setter
    def num_processes(self, num_processes):
        if num_processes == self._num_processes:
            # same number. no need to do anything
            return
        self._num_processes = num_processes
        for pool_name in self._thread_pools_names:
            self._thread_pools_names[pool_name] = num_processes

        for pool in self._thread_pools:
            # close the pool
            self._thread_pools[pool].close()
            # wait for all processes to finish
            self._thread_pools[pool].join()
            # terminate pool
            self._thread_pools[pool].terminate()
        for name, thread in self._event_loops_dict:
            thread.stop()
        self._event_loops_dict = dict()
        self._thread_pools = dict()

    def create_event_loop_thread(self, name):
        loop = asyncio.new_event_loop()
        event_loop = AsyncThreadEventLoop(loop=loop,
                                          n=self._num_processes,
                                          name=name)
        event_loop.daemon = True
        event_loop.start()
        time.sleep(1)
        return event_loop

    def event_loops(self, name):
        if name not in self._event_loops_dict:
            self._event_loops_dict[name] = self.create_event_loop_thread(name=name)
        if not self._event_loops_dict[name].loop.is_running():
            if self._event_loops_dict[name].is_alive():
                self._event_loops_dict[name].stop()
            self._event_loops_dict[name] = self.create_event_loop_thread(name=name)
        return self._event_loops_dict[name]

    def thread_pools(self, pool_name):
        if pool_name not in self._thread_pools_names:
            raise ValueError('unknown thread pool name: {}. known name: {}'.format(pool_name,
                                                                                   list(
                                                                                       self._thread_pools_names.keys())))
        num_processes = self._thread_pools_names[pool_name]
        if pool_name not in self._thread_pools:
            self._thread_pools[pool_name] = ThreadPool(processes=num_processes)
        pool = self._thread_pools[pool_name]
        assert isinstance(pool, multiprocessing.pool.ThreadPool)
        if pool._state != multiprocessing.pool.RUN:
            # pool is closed, open a new one
            self._stopped_pools.append(pool)
            logger.debug('Global ThreadPool is not running. Creating a new one')
            pool = ThreadPool(processes=num_processes)
            self._thread_pools[pool_name] = pool
        return pool

    @property
    def verify(self):
        environments = self.environments
        verify = True
        if self.environment in environments:
            if 'verify_ssl' in environments[self.environment]:
                verify = environments[self.environment]['verify_ssl']
        return verify

    @property
    def auth(self):
        return {'authorization': 'Bearer ' + self.token}

    @property
    def environment(self):
        _environment = self._environment
        if _environment is None:
            _environment = self.cookie_io.get('url')
            self._environment = _environment
        return _environment

    @environment.setter
    def environment(self, env):
        self._environment = env
        self.cookie_io.put('url', env)

    @property
    def fetch_entities(self):
        if self._fetch_entities is None:
            self._fetch_entities = self.cookie_io.get('fetch_entities')
            if self._fetch_entities is None:
                self.fetch_entities = True  # default
        return self._fetch_entities

    @fetch_entities.setter
    def fetch_entities(self, val):
        self._fetch_entities = val
        self.cookie_io.put('fetch_entities', val)

    @property
    def environments(self):
        """
        List of known environments
        :return:
        """
        # get environment login parameters
        _environments = self._environments
        if _environments is None:
            # take from cookie
            _environments = self.cookie_io.get('login_parameters')
            # if cookie is None  - init with defaults
            if _environments is None:
                # default
                _environments = DEFAULT_ENVIRONMENT
                # save to local variable
                self.environments = _environments
            else:
                # save from cookie to ram
                self._environments = _environments
        return _environments

    @environments.setter
    def environments(self, env_dict):
        self._environments = env_dict
        self.cookie_io.put(key='login_parameters', value=self._environments)

    @property
    def verbose(self):
        if self._verbose is None:
            self._verbose = Verbose(cookie=self.cookie_io)
        assert isinstance(self._verbose, Verbose)
        return self._verbose

    @property
    def token(self):
        _token = self._token
        if _token is None:
            environments = self.environments
            if self.environment in environments:
                if 'token' in environments[self.environment]:
                    _token = environments[self.environment]['token']
        return _token

    @token.setter
    def token(self, token):
        # set to variable
        self._token = token
        self.refresh_token = None
        # set to cookie file
        environments = self.environments
        if self.environment in environments:
            environments[self.environment]['token'] = token
        else:
            environments[self.environment] = {'token': token}
        self.environments = environments

    @property
    def refresh_token(self):
        environments = self.environments
        refresh_token = None
        if self.environment in environments:
            if 'refresh_token' in environments[self.environment]:
                refresh_token = environments[self.environment]['refresh_token']
        return refresh_token

    @refresh_token.setter
    def refresh_token(self, token):
        environments = self.environments
        if self.environment in environments:
            environments[self.environment]['refresh_token'] = token
        else:
            environments[self.environment] = {'refresh_token': token}
        self.refresh_token_active = True
        self.environments = environments

    def add_environment(self, environment, audience, client_id, auth0_url,
                        verify_ssl=True, token=None, refresh_token=None, alias=None):
        environments = self.environments
        if environment in environments:
            logger.warning('Environment exists. Overwriting. env: {}'.format(environment))
        if token is None:
            token = None
        if alias is None:
            alias = None
        environments[environment] = {'audience': audience,
                                     'client_id': client_id,
                                     'auth0_url': auth0_url,
                                     'alias': alias,
                                     'token': token,
                                     'refresh_token': refresh_token,
                                     'verify_ssl': verify_ssl}
        self.environments = environments

    def info(self, with_token=True):
        """
        Return a dictionary with current information: env, user, token
        :param with_token:
        :return:
        """
        user_email = 'null'
        if self.token is not None:
            payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
            user_email = payload['email']
        information = {'environment': self.environment,
                       'user_email': user_email}
        if with_token:
            information['token'] = self.token
        return information

    @Decorators.token_expired_decorator
    def gen_request(self, req_type, path, data=None, json_req=None, files=None, stream=False, headers=None,
                    log_error=True):
        """
        Generic request from platform
        :param req_type:
        :param path:
        :param data:
        :param json_req:
        :param files:
        :param stream:
        :param headers:
        :param log_error:
        :return:
        """
        req_type = req_type.upper()
        valid_request_type = ['GET', 'DELETE', 'POST', 'PUT', 'PATCH']
        assert req_type in valid_request_type, '[ERROR] type: %s NOT in valid requests' % req_type

        # prepare request
        headers_req = self.auth
        headers_req['User-Agent'] = requests_toolbelt.user_agent('dtlpy', __version__.version)
        if headers is not None:
            if not isinstance(headers, dict):
                raise exceptions.PlatformException(error=400, message="Input 'headers' must be a dictionary")
            for k, v in headers.items():
                headers_req[k] = v
        req = requests.Request(method=req_type,
                               url=self.environment + path,
                               json=json_req,
                               files=files,
                               data=data,
                               headers=headers_req)
        # prepare to send
        prepared = req.prepare()
        # save curl for debug
        command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
        method = prepared.method
        uri = prepared.url
        data = prepared.body
        headers = ['"{0}: {1}"'.format(k, v) for k, v in prepared.headers.items()]
        headers = " -H ".join(headers)
        curl = command.format(method=method, headers=headers, data=data, uri=uri)
        self.last_curl = curl
        self.last_request = prepared
        # send request
        try:
            resp = self.send_session(prepared=prepared, stream=stream)
        except Exception:
            logger.error(self.print_request(req=prepared, to_return=True))
            raise
        self.last_response = resp
        # handle output
        if not resp.ok:
            self.print_bad_response(resp, log_error=log_error and not self.is_cli)
            return_type = False
        else:
            try:
                # print only what is printable (dont print get steam etc..)
                if not stream:
                    self.print_response(resp)
            except ValueError:
                # no JSON returned
                pass
            return_type = True
        return return_type, resp

    @Decorators.token_expired_decorator
    async def gen_async_request(self,
                                req_type,
                                path,
                                data=None,
                                json_req=None,
                                files=None,
                                stream=None,
                                headers=None,
                                log_error=True,
                                filepath=None,
                                chunk_size=8192,
                                pbar=None,
                                is_dataloop=True):
        req_type = req_type.upper()
        valid_request_type = ['GET', 'DELETE', 'POST', 'PUT', 'PATCH']
        assert req_type in valid_request_type, '[ERROR] type: %s NOT in valid requests' % req_type

        # prepare request
        if is_dataloop:
            full_url = self.environment + path
            headers_req = self.auth
            headers_req['User-Agent'] = requests_toolbelt.user_agent('dtlpy', __version__.version)
        else:
            full_url = path
            headers = dict()
            headers_req = headers

        if headers is not None:
            if not isinstance(headers, dict):
                raise exceptions.PlatformException(error=400, message="Input 'headers' must be a dictionary")
            for k, v in headers.items():
                headers_req[k] = v
        req = requests.Request(method=req_type,
                               url=full_url,
                               json=json_req,
                               files=files,
                               data=data,
                               headers=headers_req)
        # prepare to send
        prepared = req.prepare()
        # save curl for debug
        command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
        headers = ['"{0}: {1}"'.format(k, v) for k, v in prepared.headers.items()]
        headers = " -H ".join(headers)
        curl = command.format(method=prepared.method,
                              headers=headers,
                              data=prepared.body,
                              uri=prepared.url)
        self.last_curl = curl
        self.last_request = prepared
        # send request
        try:
            timeout = aiohttp.ClientTimeout(total=0)
            async with RetryClient(headers=headers_req,
                                   timeout=timeout) as session:
                try:
                    async with session._request(request=session._client.request,
                                                url=self.environment + path,
                                                method=req_type,
                                                json=json_req,
                                                data=data,
                                                headers=headers_req,
                                                chunked=stream,
                                                retry_attempts=5,
                                                retry_exceptions={aiohttp.client_exceptions.ClientOSError,
                                                                  aiohttp.client_exceptions.ServerDisconnectedError,
                                                                  aiohttp.client_exceptions.ClientPayloadError},
                                                raise_for_status=False) as request:
                        if stream:
                            pbar = self.__get_pbar(pbar=pbar,
                                                   total_length=request.headers.get("content-length"))
                            if filepath is not None:
                                to_close = False
                                if isinstance(filepath, str):
                                    to_close = True
                                    buffer = open(filepath, 'wb')
                                elif isinstance(filepath, io.BytesIO):
                                    pass
                                else:
                                    raise ValueError('unknown data type to write file: {}'.format(type(filepath)))
                                try:
                                    while True:
                                        chunk = await request.content.read(chunk_size)
                                        if not chunk:
                                            break
                                        buffer.write(chunk)
                                        if pbar is not None:
                                            pbar.update(len(chunk))
                                finally:
                                    if to_close:
                                        buffer.close()

                            if pbar is not None:
                                pbar.close()
                        text = await request.text()
                        try:
                            _json = await request.json()
                        except:
                            _json = dict()
                        response = AsyncResponse(text=text,
                                                 _json=_json,
                                                 async_resp=request)
                except Exception as err:
                    response = AsyncResponseError(error=err, trace=traceback.format_exc())
                finally:
                    with threadLock:
                        self.calls_counter.add()
        except Exception:
            logger.error(self.print_request(req=prepared, to_return=True))
            raise
        self.last_response = response
        # handle output
        if not response.ok:
            self.print_bad_response(response, log_error=log_error and not self.is_cli)
            return_type = False
        else:
            try:
                # print only what is printable (dont print get steam etc..)
                if not stream:
                    self.print_response(response)
            except ValueError:
                # no JSON returned
                pass
            return_type = True
        return return_type, response

    async def upload_file_async(self, to_upload, item_type, item_size, remote_url, uploaded_filename,
                                remote_path=None, callback=None, mode='skip', item_metadata=None):
        headers = self.auth
        headers['User-Agent'] = requests_toolbelt.user_agent('dtlpy', __version__.version)

        pbar = None
        if callback is None:
            if item_size > 10e6:
                # size larger than 10MB
                pbar = tqdm.tqdm(total=item_size,
                                 unit="B",
                                 unit_scale=True,
                                 unit_divisor=1024,
                                 position=1,
                                 disable=self.verbose.disable_progress_bar)

                def callback(bytes_read):
                    pbar.update(bytes_read)
            else:
                def callback(bytes_read):
                    pass

        timeout = aiohttp.ClientTimeout(total=0)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            try:
                form = aiohttp.FormData({})
                form.add_field('type', item_type)
                form.add_field('path', os.path.join(remote_path, uploaded_filename).replace('\\', '/'))
                if item_metadata is not None:
                    form.add_field('metadata', json.dumps(item_metadata))
                form.add_field('file', AsyncUploadStream(buffer=to_upload, callback=callback))
                url = '{}?mode={}'.format(self.environment + remote_url, mode)
                async with session.post(url, data=form, verify_ssl=self.verify) as resp:
                    text = await resp.text()
                    try:
                        _json = await resp.json()
                    except:
                        _json = dict()
                    response = AsyncResponse(text=text,
                                             _json=_json,
                                             async_resp=resp)
            except Exception as err:
                response = AsyncResponseError(error=err, trace=traceback.format_exc())
            finally:
                if pbar is not None:
                    pbar.close()
                with threadLock:
                    self.calls_counter.add()
        return response

    def __get_pbar(self, pbar, total_length):
        # decide if create progress bar for item
        if pbar:
            try:
                if total_length is not None and int(total_length) > 10e6:  # size larger than 10 MB:
                    pbar = tqdm.tqdm(total=int(total_length),
                                     unit='B',
                                     unit_scale=True,
                                     unit_divisor=1024,
                                     position=1,
                                     disable=self.verbose.disable_progress_bar)
                else:
                    pbar = None
            except Exception as err:
                pbar = None
                logger.debug('Cant decide downloaded file length, bar will not be presented: {}'.format(err))
        return pbar

    def send_session(self, prepared, stream=None):
        if self.session is None:
            self.session = requests.Session()
            retry = Retry(
                total=5,
                read=5,
                connect=5,
                backoff_factor=0.3,
                # use on any request type
                method_whitelist=False,
                # force retry on those status responses
                status_forcelist=(501, 502, 503, 504, 505, 506, 507, 508, 510, 511),
                raise_on_status=False
            )
            adapter = HTTPAdapter(max_retries=retry,
                                  pool_maxsize=np.sum(list(self._thread_pools_names.values())),
                                  pool_connections=np.sum(list(self._thread_pools_names.values())))
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
        resp = self.session.send(request=prepared, stream=stream, verify=self.verify, timeout=None)

        with threadLock:
            self.calls_counter.add()
        return resp

    @staticmethod
    def check_proxy():
        """
        Verify that dataloop urls are not blocked
        :return:
        """
        proxy_envs = ['HTTP', 'HTTPS', 'http', 'https']
        dataloop_urls = ['dev-gate.dataloop.ai',
                         'gate.dataloop.ai',
                         'dataloop-development.auth0.com',
                         'dataloop-production.auth0.com']
        if True in [env in os.environ for env in proxy_envs]:
            # check if proxy exists
            if True in [env in os.environ for env in ['no_proxy', 'NO_PROXY']]:
                # check if no_proxy exists
                if 'no_proxy' in os.environ:
                    # check if dataloop urls in no_proxy
                    if True not in [url in os.environ['no_proxy'] for url in dataloop_urls]:
                        # no dataloop url exists in no_proxy
                        logger.warning('Proxy is used, make sure dataloop urls are in "no_proxy" environment variable')
                else:
                    # check if dataloop urls in no_proxy
                    if True not in [url in os.environ['NO_PROXY'] for url in dataloop_urls]:
                        # no dataloop url exists in no_proxy
                        logger.warning('Proxy is used, make sure dataloop urls are in "no_proxy" environment variable')
            else:
                logger.warning('Proxy is used, make sure dataloop urls are in "no_proxy" environment variable')

    def token_expired(self, t=60):
        """
        Check token validation
        :param t: time ahead interval in seconds
        """
        try:
            if self.token is None or self.token == '':
                expired = True
            else:
                payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
                d = datetime.datetime.utcnow()
                epoch = datetime.datetime(1970, 1, 1)
                now = (d - epoch).total_seconds()
                exp = payload['exp']
                if now < (exp - t):
                    expired = False
                else:
                    expired = True
        except jwt.exceptions.DecodeError:
            logger.exception('Invalid token.')
            expired = True
        except Exception:
            logger.exception('Unknown error:')
            expired = True
        if expired:
            if self.renew_token_method():
                expired = False
        return expired

    @staticmethod
    def is_json_serializable(response):
        try:
            response_json = response.json()
            return True, response_json
        except ValueError:
            return False, None

    ##########
    # STDOUT #
    ##########
    def print_response(self, resp=None):
        """
        Print tabulate response
        :param resp: response from requests
        :return:
        """
        try:
            if resp is None:
                resp = self.last_response
            is_json_serializable, results = self.is_json_serializable(response=resp)
            if self.verbose.print_all_responses and is_json_serializable:
                if isinstance(results, dict):
                    to_print = miscellaneous.List([results])
                elif isinstance(results, list):
                    to_print = miscellaneous.List(results)
                else:
                    logger.debug('Unknown response type: {}. cant print'.format(type(results)))
                    return
                logger.debug('--- [Request] Start ---')
                logger.debug(self.print_request(req=resp.request, to_return=True))
                logger.debug('--- [Request] End ---')
                logger.debug('--- [Response] Start ---')
                to_print.print(show_all=False, level='debug')
                logger.debug('--- [Response] End ---')
        except Exception:
            logger.exception('Printing response from gate:')

    def print_bad_response(self, resp=None, log_error=True):
        """
        Print error from platform
        :param resp:
        :param log_error: print error log (to use when trying request more than once)
        :return:
        """
        if resp is None:
            resp = self.last_response
        msg = ''
        if hasattr(resp, 'status_code'):
            msg += '[Response <{val}>]'.format(val=resp.status_code)
        if hasattr(resp, 'reason'):
            msg += '[Reason: {val}]'.format(val=resp.reason)
        if hasattr(resp, 'text'):
            msg += '[Text: {val}]'.format(val=resp.text)

        logger.debug('--- [Request] Start ---')
        logger.debug(self.print_request(req=resp.request, to_return=True))
        logger.debug('--- [Request] End ---')
        logger.debug('--- [Response] Start ---')
        if log_error:
            logger.error(msg)
        else:
            logger.debug(msg)
        logger.debug('--- [Response] End ---')
        self.platform_exception = PlatformError(resp)

    def print_request(self, req=None, to_return=False, with_auth=False):
        """
        Print a request to the platform
        :param req:
        :param to_return: return string instead of printing
        :param with_auth: print authentication
        :return:
        """
        if not req:
            req = self.last_request

        headers = list()
        for k, v in req.headers.items():
            if k == 'authorization' and not with_auth:
                continue
            headers.append('{}: {}'.format(k, v))
        if hasattr(req, 'body'):
            body = req.body
        elif isinstance(req, aiohttp.RequestInfo):
            body = {'multipart': 'true'}
        else:
            body = dict()

        # remove secrets and passwords
        try:
            body = json.loads(body)
            if isinstance(body, dict):
                for key, value in body.items():
                    hide = any([field in key for field in ['secret', 'password']])
                    if hide:
                        body[key] = '*' * len(value)
        except Exception:
            pass

        msg = '{}\n{}\n{}'.format(
            req.method + ' ' + str(req.url),
            '\n'.join(headers),
            body,
        )
        if to_return:
            return msg
        else:
            print(msg)

    ################
    # Environments #
    ################
    def setenv(self, env):
        """
        Set environment
        :param env:
        :return:
        """
        environments = self.environments
        if env.startswith('http'):
            if env not in environments.keys():
                msg = 'Unknown environment. Please add environment to SDK ("add_environment" method)'
                logger.error(msg)
                raise ConnectionError(msg)
        else:
            matched_env = [env_url for env_url, env_dict in environments.items() if env_dict['alias'] == env]
            if len(matched_env) != 1:
                known_aliases = [env_dict['alias'] for env_url, env_dict in environments.items()]
                raise ConnectionError(
                    'Unknown platform environment: "{}". Known: {}'.format(env, ', '.join(known_aliases)))
            env = matched_env[0]
        if self.environment != env:
            self.environment = env
            # reset local token
            self._token = None
            self.refresh_token_active = True
        logger.info('Platform environment: {}'.format(self.environment))
        if self.token_expired():
            logger.info('Token expired, Please login.')

    ##########
    # Log in #
    ##########
    def login_secret(self, email, password, client_id, client_secret, force=False):
        """
        Login with email and password from environment variables
        :param email: user email. if already logged in with same user - login will NOT happen. see "force"
        :param password: user password
        :param client_id:
        :param client_secret:
        :param force: force login. in case login with same user but want to get a new JWT
        :return:
        """
        return login_secret(api_client=self,
                            email=email,
                            password=password,
                            client_id=client_id,
                            client_secret=client_secret,
                            force=force)

    def login_token(self, token):
        """
        Login using existing token
        :param token: a valid token
        :return:
        """
        self.token = token  # this will also set the refresh_token to None

    def login(self, audience=None, auth0_url=None, client_id=None):
        """
        Login using Auth0.
        :return:
        """
        return login(api_client=self,
                     audience=audience,
                     auth0_url=auth0_url,
                     client_id=client_id)

    def renew_token(self):
        renewed = False
        if self.refresh_token_active is False:
            return renewed
        logger.debug('RefreshToken: Started')
        if self.token is None or self.token == '':
            # token is missing
            logger.debug('RefreshToken: Missing token.')
            self.refresh_token_active = False
        if self.refresh_token is None or self.refresh_token == '':
            # missing refresh token
            logger.debug('RefreshToken: Missing "refresh_token"')
            self.refresh_token_active = False
        if self.environment not in self.environments.keys():
            # env params missing
            logger.error('RefreshToken: Missing environments params for refreshing token')
            self.refresh_token_active = False

        if self.refresh_token_active is False:
            return renewed

        refresh_token = self.refresh_token

        env_params = self.environments[self.environment]
        client_id = env_params['client_id']
        auth0_url = env_params['auth0_url']
        payload = {'grant_type': 'refresh_token',
                   'client_id': client_id,
                   'refresh_token': self.refresh_token}
        resp = requests.request("POST",
                                auth0_url + '/oauth/token',
                                json=payload,
                                headers={'content-type': 'application/json'})
        if not resp.ok:
            logger.debug('RefreshToken: Failed')
            self.print_bad_response(resp)
        else:
            response_dict = resp.json()
            # get new token
            final_token = response_dict['id_token']
            self.token = final_token
            self.refresh_token = refresh_token
            # set status back to pending
            logger.debug('RefreshToken: Success')
            renewed = True
        return renewed

    def set_api_counter(self, filepath):
        self.calls_counter = CallsCounter(filepath=filepath)

    def _get_resource_url(self,
                          resource_type,
                          project_id=None,
                          dataset_id=None,
                          item_id=None,
                          package_id=None,
                          service_id=None):

        env = self._environments[self._environment]['alias']
        if env == 'prod':
            head = 'https://console.dataloop.ai'
        elif env == 'dev':
            head = 'https://dev-con.dataloop.ai'
        elif env == 'rc':
            head = 'https://rc-con.dataloop.ai'
        elif env == 'local':
            head = 'https://localhost:8443/'
        else:
            raise exceptions.PlatformException(error='400', message='Unknown environment: {}'.format(env))

        if resource_type == 'project':
            url = head + '/projects/{}'.format(project_id)
        elif resource_type == 'dataset':
            url = head + '/projects/{}/datasets/{}'.format(project_id, dataset_id)
        elif resource_type == 'item':
            url = head + '/projects/{}/datasets/{}/items/{}'.format(project_id, dataset_id, item_id)
        elif resource_type == 'package':
            url = head + '/projects/{}/packages/{}'.format(project_id, package_id)
        elif resource_type == 'service':
            url = head + '/projects/{}/packages/{}/services/{}'.format(project_id, package_id, service_id)
        else:
            raise exceptions.PlatformException(error='400', message='Unknown resource_type: {}'.format(resource_type))
        return url

    def _open_in_web(self,
                     resource_type,
                     project_id=None,
                     dataset_id=None,
                     item_id=None,
                     package_id=None,
                     service_id=None):

        import webbrowser
        url = self._get_resource_url(resource_type=resource_type,
                                     project_id=project_id,
                                     dataset_id=dataset_id,
                                     item_id=item_id,
                                     package_id=package_id,
                                     service_id=service_id)
        webbrowser.open(url=url, new=2, autoraise=True)
