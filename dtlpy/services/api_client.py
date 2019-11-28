"""
Dataloop platform calls
"""
import requests_toolbelt
import multiprocessing
import threading
import traceback
import datetime
import requests
import aiohttp
import asyncio
import logging
import hashlib
import base64
import enum
import time
import tqdm
import json
import jwt
import os
from multiprocessing.pool import ThreadPool
from requests.adapters import HTTPAdapter
from urllib.parse import urlencode
from urllib3.util import Retry
from functools import wraps
import numpy as np

from .calls_counter import CallsCounter
from .cookie import CookieIO
from .async_entities import AsyncResponse, AsyncUploadStream
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
        logging.getLogger('dtlpy').handlers[1].setLevel(logging._nameToLevel[self._logging_level.upper()])
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
                raise exceptions.PlatformException('600', 'Token expired, Please login.')
            # the actual method call
            result = method(inst, *args, **kwargs)
            # after the method call
            return result

        return decorated_method


class ApiClient:
    """
    API calls to Dataloop gate
    """

    def __init__(self, token=None, num_processes=None):
        ############
        # Initiate #
        ############
        # define local params - read only once from cookie file
        self.is_cli = False
        self.session = None
        self._token = None
        self._environments = None
        self._environment = None
        self._environments = None
        self._verbose = None
        # define other params
        self.last_response = None
        self.last_request = None
        self.platform_exception = None
        self.last_curl = None
        self.cookie_io = CookieIO.init()
        assert isinstance(self.cookie_io, CookieIO)
        self.state_io = CookieIO.init_local_cookie(create=False)
        assert isinstance(self.state_io, CookieIO)

        ##################
        # configurations #
        ##################
        self.minimal_print = True

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

        # start refresh token thread
        self.refresh_token_thread = RefreshTimer(client_api=self)
        self.refresh_token_thread.daemon = True
        self.refresh_token_thread.start()

        # create a global thread pool to run multi threading
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()
        self._thread_pools = dict()
        self._thread_pools_names = {'item.upload': num_processes,
                                    'item.download': num_processes,
                                    'item.page': num_processes,
                                    'annotation.upload': num_processes,
                                    'annotation.download': num_processes,
                                    'annotation.update': num_processes,
                                    'entity.create': num_processes}
        # set logging level
        logging.getLogger('dtlpy').handlers[1].setLevel(logging._nameToLevel[self.verbose.logging_level.upper()])

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
                _environments = {
                    'https://dev-gate.dataloop.ai/api/v1':
                        {'alias': 'dev',
                         'audience': 'https://dataloop-development.auth0.com/api/v2/',
                         'client_id': 'I4Arr9ixs5RT4qIjOGtIZ30MVXzEM4w8',
                         'auth0_url': 'https://dataloop-development.auth0.com',
                         'token': None,
                         'refresh_token': None,
                         'verify_ssl': True},
                    'https://gate.dataloop.ai/api/v1': {'alias': 'prod',
                                                        'audience': 'https://dataloop-production.auth0.com/userinfo',
                                                        'client_id': 'FrG0HZga1CK5UVUSJJuDkSDqItPieWGW',
                                                        'auth0_url': 'https://dataloop-production.auth0.com',
                                                        'token': None,
                                                        'refresh_token': None,
                                                        'verify_ssl': True},
                    'https://localhost:8443/api/v1': {'alias': 'local',
                                                      'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                      'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                      'auth0_url': 'https://dataloop-local.auth0.com',
                                                      'token': None,
                                                      'refresh_token': None,
                                                      'verify_ssl': False},
                    'https://172.17.0.1:8443/api/v1': {'alias': 'docker_linux',
                                                       'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                       'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                       'auth0_url': 'https://dataloop-local.auth0.com',
                                                       'token': None,
                                                       'refresh_token': None,
                                                       'verify_ssl': False},
                    'https://host.docker.internal:8443/api/v1': {'alias': 'docker_windows',
                                                                 'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                                 'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                                 'auth0_url': 'https://dataloop-local.auth0.com',
                                                                 'token': None,
                                                                 'refresh_token': None,
                                                                 'verify_ssl': False}
                }
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
        self.environments = environments

    def add_environment(self, environment, audience, client_id, auth0_url,
                        verify_ssl=True, token=None, refresh_token=None, alias=None):
        environments = self.environments
        if environment in environments:
            logger.warning('Environment exists. Overwriting. env: %s' % environment)
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
        self.last_curl = command.format(method=method, headers=headers, data=data, uri=uri)
        self.last_request = prepared
        # send request
        resp = self.send_session(prepared=prepared, stream=stream)
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

    async def __upload_file_async(self, to_upload, item_type, item_size, remote_url, uploaded_filename,
                                  remote_path=None, callback=None, mode='skip', item_metadata=None):
        headers = self.auth
        headers['User-Agent'] = requests_toolbelt.user_agent('dtlpy', __version__.version)

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
                async with session.post(url, data=form) as resp:
                    text = await resp.text()
                    try:
                        _json = await resp.json()
                    except:
                        _json = dict()
                    response = AsyncResponse(text=text,
                                             _json=_json,
                                             async_resp=resp)
            except:
                logger.exception('Error in async upload')
        return response

    def upload_from_local(self, to_upload, item_type, item_size, remote_url, uploaded_filename, remote_path=None,
                          callback=None, log_error=True, mode='skip', item_metadata=None):
        def exception_handler(loop, context):
            logger.debug("[Asyc] Upload item caught the following exception: {}".format(context['message']))

        if remote_path is None:
            remote_path = '/'
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.__upload_file_async(to_upload=to_upload,
                                                                    item_type=item_type,
                                                                    item_size=item_size,
                                                                    item_metadata=item_metadata,
                                                                    remote_url=remote_url,
                                                                    uploaded_filename=uploaded_filename,
                                                                    remote_path=remote_path,
                                                                    callback=callback,
                                                                    mode=mode))
        loop.close()
        if not response.ok:
            self.print_bad_response(response, log_error)
            success = False
        else:
            try:
                # print only what is printable (don't print get steam etc..)
                self.print_response(response)
            except ValueError:
                # no JSON returned
                pass
            success = True
        return success, response

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

    def token_expired(self):
        """
        Check token validation
        :return:
        """
        try:
            if self.token is None or self.token == '':
                return True
            payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
            now = datetime.datetime.now().timestamp()
            exp = payload['exp']
            if now < exp:
                return False
            else:
                return True
        except jwt.exceptions.DecodeError as err:
            logger.exception('Invalid token.')
            return True
        except Exception as err:
            logger.exception('Unknown error:')
            return True

    @staticmethod
    def is_json_serializable(response):
        try:
            response_json = response.json()
            return True, response_json
        except json.decoder.JSONDecodeError:
            return False, None

    ##########
    # STDOUT #
    ##########
    def print_response(self, resp):
        """
        Print tabulate response
        :param resp: response from requests
        :return:
        """
        try:
            is_json_serializable, results = self.is_json_serializable(response=resp)
            if self.verbose.print_all_responses and is_json_serializable:
                if isinstance(results, dict):
                    to_print = miscellaneous.List([results])
                elif isinstance(results, list):
                    to_print = miscellaneous.List(results)
                else:
                    logger.debug('Unknown response type: {}. cant print'.format(type(results)))
                    return
                logger.debug('-- Request --')
                logger.debug(self.print_request(req=resp.request, to_return=True))
                logger.debug('-- Response --')
                to_print.print(show_all=False, level='debug')
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

        logger.debug('-- Request --')
        logger.debug(self.print_request(req=resp.request, to_return=True))
        logger.debug('-- Response --')
        if log_error:
            logger.error(msg)
        else:
            logger.debug(msg)

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

        msg = '{}\n{}\n{}\n\n{}'.format(
            '-----------START-----------',
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
                logger.exception(msg)
                raise ConnectionError(msg)
        else:
            matched_env = [env_url for env_url, env_dict in environments.items() if env_dict['alias'] == env]
            if len(matched_env) != 1:
                known_aliases = [env_dict['alias'] for env_url, env_dict in environments.items()]
                raise ConnectionError(
                    'Unknown platform environment: "{}". Known: {}'.format(env, ', '.join(known_aliases)))
            env = matched_env[0]
        self.environment = env
        # reset local token
        self._token = None
        logger.info('Platform environment: %s' % self.environment)
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
        # check if already logged in with SAME email
        if self.token is not None or self.token == '':
            try:
                payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
                if 'email' in payload and \
                        payload['email'] == email and \
                        not self.token_expired() and \
                        not force:
                    logger.warning('Trying to login with same email but token not expired. Not doing anything... '
                                   'Set "force" flag to True to login anyway.')
                    return True
            except jwt.exceptions.DecodeError:
                logger.debug('{}'.format('Cant decode token. Force login is user'))

        logger.info('[Start] Login Secret')
        environment = self.environment
        audience = None
        auth0_url = None
        for env, env_params in self.environments.items():
            if env == environment:
                audience = env_params['audience']
                auth0_url = env_params['auth0_url']
        missing = False
        if audience is None:
            logger.error('audience not found. Please add a new environment to SDK. env: {}'.format(environment))
            missing = True
        if auth0_url is None:
            logger.error('auth0_url not found. Please add a new environment to SDK. env: {}'.format(environment))
            missing = True
        if missing:
            raise ConnectionError('Some values are missing. See above for full error')
        # need to login
        payload = {'username': email,
                   'password': password,
                   'grant_type': 'password',
                   'audience': audience,
                   'scope': 'openid email offline_access',
                   'client_id': client_id,
                   'client_secret': client_secret
                   }
        headers = {'content-type': 'application/json'}
        token_url = auth0_url + '/oauth/token'
        resp = requests.request("POST", token_url, data=json.dumps(payload), headers=headers)
        if not resp.ok:
            self.print_bad_response(resp)
            return False
        else:
            response_dict = resp.json()
            self.token = response_dict['id_token']  # this will also set the refresh_token to None
            if 'refresh_token' in response_dict:
                self.refresh_token = response_dict['refresh_token']
            payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
            if 'email' in payload:
                logger.info('[Done] Login Secret. User: {}'.format(payload['email']))
            else:
                logger.info('[Done] Login Secret. User: {}'.format(email))
                logger.info(payload)
        return True

    ##########
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
        import webbrowser
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from urllib.parse import urlparse, parse_qs

        logger.info('Logging in to Dataloop...')
        login_success = False
        # create a Code Verifier
        n_bytes = 64
        verifier = base64.urlsafe_b64encode(os.urandom(n_bytes)).rstrip(b'=')
        # https://tools.ietf.org/html/rfc7636#section-4.1
        # minimum length of 43 characters and a maximum length of 128 characters.
        if len(verifier) < 43:
            raise ValueError("Verifier too short. n_bytes must be > 30.")
        elif len(verifier) > 128:
            raise ValueError("Verifier too long. n_bytes must be < 97.")
        # Create a code challenge
        digest = hashlib.sha256(verifier).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b'=')

        ################################
        # auth0 parameters for request #
        ################################
        # get env from url
        if self.environment in self.environments.keys():
            env_params = self.environments[self.environment]
            audience = env_params['audience']
            client_id = env_params['client_id']
            auth0_url = env_params['auth0_url']
        else:
            missing = False
            if audience is None:
                logger.error('Missing parameter for environment missing. Need to input "audience"')
                missing = True
            if client_id is None:
                logger.error('Missing parameter for environment missing. Need to input "client_id"')
                missing = True
            if auth0_url is None:
                logger.error('Missing parameter for environment missing. Need to input "auth0_url"')
                missing = True
            if missing:
                raise ConnectionError('Missing parameter for environment. see above')
            # add to login parameters
            self.add_environment(environment=self.environment,
                                 audience=audience,
                                 client_id=client_id,
                                 auth0_url=auth0_url)

        redirect_url = 'http://localhost:3001/token'

        # set url request for auth0
        payload = {'code_challenge_method': 'S256',
                   'code_challenge': challenge,
                   'response_type': 'code',
                   'audience': audience,
                   'scope': 'openid email offline_access',
                   'client_id': client_id,
                   'redirect_uri': redirect_url}

        query_string = urlencode(payload, doseq=True)

        # set up local server to get response from auth0
        global query_dict
        query_dict = None

        class RequestHandler(BaseHTTPRequestHandler):

            def log_message(self, format, *args):
                return

            def do_GET(self):
                global query_dict
                parsed_path = urlparse(self.path)
                query_dict = parse_qs(parsed_path.query)
                try:
                    # working directory when running from command line
                    location = os.path.dirname(os.path.realpath(__file__))
                except NameError:
                    # working directory when running from console
                    location = './dtlpy/services'
                filename = os.path.join(location, '..', 'assets', 'lock_open.png')
                if query_dict and 'code' in query_dict:
                    if os.path.isfile(filename):
                        with open(filename, 'rb') as f:
                            # Open the static file requested and send it
                            self.send_response(200)
                            self.send_header('Content-type', 'image/jpg')
                            self.end_headers()
                            self.wfile.write(f.read())
                return

        port = 3001
        # print('Listening on localhost:%s' % port)
        server = HTTPServer(('', port), RequestHandler)
        # set timeout to 1min (waiting for user to login)
        server.timeout = 60  # timeout 1 min
        try:
            # open browser to Auth0 login page
            webbrowser.open(url=auth0_url + '/authorize' + '?%s' % query_string, new=2, autoraise=True)
            # wait for request
            server.handle_request()
            # check the global list for the token
            if query_dict and 'code' in query_dict:
                # authentication code received from auth0 - can continue login
                # payload for auth0 token request
                payload = {'grant_type': 'authorization_code',
                           'client_id': client_id,
                           'code_verifier': verifier.decode(),
                           'code': query_dict['code'][0],
                           'redirect_uri': redirect_url}
                resp = requests.request("POST",
                                        auth0_url + '/oauth/token',
                                        json=payload,
                                        headers={'content-type': 'application/json'})
                if not resp.ok:
                    self.print_bad_response(resp)
                    login_success = False
                else:
                    response_dict = resp.json()
                    final_token = response_dict['id_token']
                    self.token = final_token  # this will also set the refresh_token to None
                    if 'refresh_token' in response_dict:
                        self.refresh_token = response_dict['refresh_token']

                    payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
                    if 'email' in payload:
                        logger.info('Logged in: %s' % payload['email'])
                    else:
                        logger.info('Logged in: unknown user')
                    login_success = True
            else:
                # if time out passed (in seconds) break
                logger.exception('Timeout reached: getting token from server')
                raise ConnectionError('Timeout reached: getting token from server')
        except Exception as err:
            logger.exception('Error in http server for getting token')
        finally:
            # shutdown local server
            server.server_close()
        return login_success

    def set_api_counter(self, filepath):
        self.calls_counter = CallsCounter(filepath=filepath)


class RefreshTimer(threading.Thread):
    class Status(enum.Enum):
        FAILED = 0
        PENDING = 1
        MISSING = 2
        INPROGRESS = 3

    def __init__(self, client_api):
        super(RefreshTimer, self).__init__()
        self.client_api = client_api
        self.kill = False
        self.renew_status = self.Status.PENDING
        self.times = {
            'before_expired': 60 * 60,  # 60 min
            'on_fail': 10 * 60,  # 10 min
            'wake_margin': 30 * 60,  # 30 min
            'on_missing': 10 * 60 * 60,  # 10 hours
            'default': 10 * 60 * 60  # 10 hours
        }

    def renew_token(self):
        env_params = self.client_api.environments[self.client_api.environment]
        client_id = env_params['client_id']
        auth0_url = env_params['auth0_url']
        payload = {'grant_type': 'refresh_token',
                   'client_id': client_id,
                   'refresh_token': self.client_api.refresh_token}
        resp = requests.request("POST",
                                auth0_url + '/oauth/token',
                                json=payload,
                                headers={'content-type': 'application/json'})
        if not resp.ok:
            self.client_api.print_bad_response(resp)
            self.renew_status = self.Status.FAILED
        else:
            response_dict = resp.json()
            # get new token
            final_token = response_dict['id_token']
            self.client_api.token = final_token
            # set status back to pending
            self.renew_status = self.Status.PENDING

    def run(self):
        while True:
            try:
                logger.debug('RefreshToken: Started')
                next_wake = self.times['default']
                if self.kill:
                    logger.debug('RefreshToken: Killed. Breaking..')
                    break
                if self.client_api.token is None or self.client_api.token == '':
                    # token is missing
                    logger.debug('RefreshToken: Missing token.')
                    self.renew_status = self.Status.MISSING
                if self.client_api.refresh_token is None or self.client_api.refresh_token == '':
                    # missing refresh token
                    logger.debug('RefreshToken: Missing "refresh_token"')
                    self.renew_status = self.Status.MISSING
                if self.client_api.environment not in self.client_api.environments.keys():
                    # env params missing
                    logger.error('RefreshToken: Missing environments params for refreshing token')
                    self.renew_status = self.Status.MISSING
                if self.renew_status == self.Status.PENDING:
                    # check expiration time
                    payload = jwt.decode(self.client_api.token, algorithms=['HS256'], verify=False)
                    now = datetime.datetime.now().timestamp()
                    exp = payload['exp']
                    # check if need to renew
                    if now > (exp - self.times['before_expired']):
                        # 1 hour till expiration and not already in renew process
                        logger.debug('RefreshToken: Refreshing...')
                        self.renew_status = self.Status.INPROGRESS
                        self.renew_token()
                        if self.renew_status == self.Status.PENDING:
                            # calculate next wake time
                            logger.debug('RefreshToken: Success')
                            payload = jwt.decode(self.client_api.token, algorithms=['HS256'], verify=False)
                            now = datetime.datetime.now().timestamp()
                            exp = payload['exp']
                            next_wake = int(exp - now - self.times['wake_margin'])
                        else:
                            logger.debug('RefreshToken: Failed')
                            next_wake = self.times['on_fail']
                    else:
                        next_wake = int(exp - now - self.times['wake_margin'])

                if self.renew_status == self.Status.FAILED:
                    next_wake = self.times['on_fail']
                if self.renew_status == self.Status.MISSING:
                    next_wake = self.times['on_missing']

                logger.debug('RefreshToken: Sleeping for: {}[s]'.format(next_wake))
                time.sleep(next_wake)
            except:
                logger.debug(traceback.format_exc())
                logger.debug('RefreshToken: Non Fatal Error: refresh token failed. Sleeping for: {}'.format(
                    self.times['on_fail']))
                time.sleep(self.times['on_fail'])
