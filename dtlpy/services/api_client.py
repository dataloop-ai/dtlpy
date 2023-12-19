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
import certifi
import base64
import time
import tqdm
import json
import sys
import ssl
import jwt
import os
import io
import concurrent
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from functools import wraps
import numpy as np
import inspect
from requests.models import Response
from dtlpy.caches.cache import CacheManger, CacheConfig
from .calls_counter import CallsCounter
from .cookie import CookieIO
from .logins import login, logout, login_secret, login_m2m, gate_url_from_host
from .async_utils import AsyncResponse, AsyncUploadStream, AsyncResponseError, AsyncThreadEventLoop
from .events import Events
from .service_defaults import DEFAULT_ENVIRONMENTS, DEFAULT_ENVIRONMENT
from .aihttp_retry import RetryClient
from .. import miscellaneous, exceptions, __version__

logger = logging.getLogger(name='dtlpy')
threadLock = threading.Lock()


class VerboseLoggingLevel:
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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
    __PRINT_ERROR_LOGS = False

    def __init__(self, cookie):
        self.cookie = cookie
        dictionary = self.cookie.get('verbose')
        if isinstance(dictionary, dict):
            self.from_cookie(dictionary)
        else:
            self._logging_level = self.__DEFAULT_LOGGING_LEVEL
            self._disable_progress_bar = self.__DEFAULT_DISABLE_PROGRESS_BAR
            self._print_all_responses = self.__DEFAULT_PRINT_ALL_RESPONSES
            self._print_error_logs = self.__PRINT_ERROR_LOGS
            if os.getenv('DTLPY_REFRESH_TOKEN_METHOD', "") == "proxy":
                self._print_error_logs = True
            self.to_cookie()

    def to_cookie(self):
        dictionary = {'logging_level': self._logging_level,
                      'disable_progress_bar': self._disable_progress_bar,
                      'print_all_responses': self._print_all_responses,
                      'print_error_logs': self._print_error_logs}
        self.cookie.put(key='verbose', value=dictionary)

    def from_cookie(self, dictionary):
        self._logging_level = dictionary.get('logging_level', self.__DEFAULT_LOGGING_LEVEL)
        self._disable_progress_bar = dictionary.get('disable_progress_bar', self.__DEFAULT_DISABLE_PROGRESS_BAR)
        self._print_all_responses = dictionary.get('print_all_responses', self.__DEFAULT_PRINT_ALL_RESPONSES)
        self._print_error_logs = dictionary.get('print_error_logs', self.__PRINT_ERROR_LOGS)

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
        logging.getLogger(name='dtlpy').handlers[0].setLevel(logging._nameToLevel[self._logging_level.upper()])
        # write to cookie
        self.to_cookie()

    @property
    def print_all_responses(self):
        return self._print_all_responses

    @print_all_responses.setter
    def print_all_responses(self, val):
        self._print_all_responses = val
        self.to_cookie()

    @property
    def print_error_logs(self):
        return self._print_error_logs

    @print_error_logs.setter
    def print_error_logs(self, val):
        self._print_error_logs = val
        self.to_cookie()


class CacheMode:
    __DEFAULT_ENABLE_CACHE = True
    __DEFAULT_CHUNK_CACHE = 200000

    def __init__(self, cookie):
        self.cookie = cookie
        dictionary = self.cookie.get('cache_mode')
        if isinstance(dictionary, dict):
            self.from_cookie(dictionary)
        else:
            self._enable_cache = self.__DEFAULT_ENABLE_CACHE
            self._chunk_cache = self.__DEFAULT_CHUNK_CACHE
            self.to_cookie()

    def to_cookie(self):
        dictionary = {'enable_cache': self._enable_cache,
                      'chunk_cache': self._chunk_cache}
        self.cookie.put(key='cache_mode', value=dictionary)

    def from_cookie(self, dictionary):
        self._enable_cache = dictionary.get('enable_cache', self.__DEFAULT_ENABLE_CACHE)
        self._chunk_cache = dictionary.get('chunk_cache', self.__DEFAULT_CHUNK_CACHE)

    @property
    def enable_cache(self):
        return self._enable_cache

    @enable_cache.setter
    def enable_cache(self, val: bool):
        if not isinstance(val, bool):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type bool")
        self._enable_cache = val
        self.to_cookie()

    @property
    def chunk_cache(self):
        return self._chunk_cache

    @chunk_cache.setter
    def chunk_cache(self, val):
        self._chunk_cache = val
        self.to_cookie()


class SDKCache:
    __DEFAULT_USE_CACHE = False
    __DEFAULT_CACHE_PATH = os.path.join(os.path.expanduser('~'), '.dataloop', 'obj_cache')
    __DEFAULT_CACHE_PATH_BIN = os.path.join(os.path.expanduser('~'), '.dataloop')
    __DEFAULT_CONFIGS_CACHE = CacheConfig().to_string()
    __DEFAULT_BINARY_CACHE_SIZE = 1000

    def __init__(self, cookie):
        self.cookie = cookie
        dictionary = self.cookie.get('cache_configs')
        if isinstance(dictionary, dict):
            self.from_cookie(dictionary)
        else:
            self._cache_path = self.__DEFAULT_CACHE_PATH
            self._cache_path_bin = self.__DEFAULT_CACHE_PATH_BIN
            self._configs = self.__DEFAULT_CONFIGS_CACHE
            self._bin_size = self.__DEFAULT_BINARY_CACHE_SIZE
            self._use_cache = self.__DEFAULT_USE_CACHE
            self.to_cookie()

    def to_cookie(self):
        dictionary = {'cache_path': self._cache_path,
                      'cache_path_bin': self._cache_path_bin,
                      'configs': self._configs,
                      'bin_size': self._bin_size,
                      'use_cache': self._use_cache}
        self.cookie.put(key='cache_configs', value=dictionary)

    def from_cookie(self, dictionary):
        self._cache_path = dictionary.get('cache_path', self.__DEFAULT_CACHE_PATH)
        self._cache_path_bin = dictionary.get('cache_path_bin', self.__DEFAULT_CACHE_PATH_BIN)
        self._configs = dictionary.get('configs', self.__DEFAULT_CONFIGS_CACHE)
        self._bin_size = dictionary.get('bin_size', self.__DEFAULT_BINARY_CACHE_SIZE)
        self._use_cache = dictionary.get('use_cache', self.__DEFAULT_USE_CACHE)

    @property
    def cache_path(self):
        return self._cache_path

    @property
    def cache_path_bin(self):
        return self._cache_path_bin

    @cache_path_bin.setter
    def cache_path_bin(self, val: str):
        if not isinstance(val, str):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type str")
        self._cache_path_bin = val
        os.environ['DEFAULT_CACHE_PATH'] = val
        self.to_cookie()

    @property
    def use_cache(self):
        return self._use_cache

    @use_cache.setter
    def use_cache(self, val: bool):
        if not isinstance(val, bool):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type bool")
        self._use_cache = val
        self.to_cookie()

    @property
    def configs(self):
        return self._configs

    @configs.setter
    def configs(self, val):
        if isinstance(val, CacheConfig):
            val = val.to_string()
        if not isinstance(val, str):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type str or CacheConfig")
        self._configs = val
        self.to_cookie()

    @property
    def bin_size(self):
        return self._bin_size

    @bin_size.setter
    def bin_size(self, val: int):
        if not isinstance(val, int):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type int")
        self._bin_size = val
        self.to_cookie()


class Attributes2:
    __DEFAULT_USE_ATTRIBUTE = False

    def __init__(self, cookie):
        self.cookie = cookie
        dictionary = self.cookie.get('use_attributes_2')
        if isinstance(dictionary, dict):
            self.from_cookie(dictionary)
        else:
            self._use_attributes_2 = self.__DEFAULT_USE_ATTRIBUTE
            self.to_cookie()

    def to_cookie(self):
        dictionary = {'use_attributes_2': self._use_attributes_2}
        self.cookie.put(key='use_attributes_2', value=dictionary)

    def from_cookie(self, dictionary):
        self._use_attributes_2 = dictionary.get('use_attributes_2', self.__DEFAULT_USE_ATTRIBUTE)

    @property
    def use_attributes_2(self):
        return self._use_attributes_2

    @use_attributes_2.setter
    def use_attributes_2(self, val: bool):
        if not isinstance(val, bool):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type bool")
        self._use_attributes_2 = val
        os.environ["USE_ATTRIBUTE_2"] = json.dumps(val)
        self.to_cookie()


class PlatformSettings:

    def __init__(self):
        self._working_projects = list()
        self._settings = dict()

    @property
    def settings(self) -> dict:
        return self._settings

    @property
    def working_projects(self) -> list:
        return self._working_projects

    @settings.setter
    def settings(self, val: dict):
        if not isinstance(val, dict):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type dict")

        self._settings = val

    def add(self, setting_name: str, setting: dict):
        if setting_name in self.settings:
            self._settings[setting_name].update(setting)
        else:
            self._settings[setting_name] = setting

    def add_project(self, project_id: str):
        if not isinstance(project_id, str):
            raise exceptions.PlatformException(error=400,
                                               message="input must be of type str")
        self._working_projects.append(project_id)

    def add_bulk(self, settings_list):
        settings_dict = {s.name: {s.scope.id: s.value}
                         for s in settings_list}
        for setting_name, settings_val in settings_dict.items():
            if setting_name in self._settings:
                self._settings[setting_name].update(settings_val)
            else:
                self._settings[setting_name] = settings_val


class Decorators:
    @staticmethod
    def token_expired_decorator(method):
        @wraps(method)
        def decorated_method(inst, *args, **kwargs):
            # save event
            frm = inspect.stack()[1]

            # before the method call
            kwargs.update({'stack': frm})
            if inst.token_expired():
                if inst.renew_token_method() is False:
                    raise exceptions.PlatformException('600', 'Token expired, Please login.'
                                                              '\nSDK login options: dl.login(), dl.login_token(), '
                                                              'dl.login_m2m()'
                                                              '\nCLI login options: dlp login, dlp login-token, '
                                                              'dlp login-m2m')
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
        self.lock = threading.Lock()
        self.renew_token_method = self.renew_token
        self.is_cli = False
        self.session = None
        self.default_headers = dict()
        self._token = None
        self._environments = None
        self._environment = None
        self._verbose = None
        self._cache_state = None
        self._attributes_mode = None
        self._platform_settings = None
        self._cache_configs = None
        self._sdk_cache = None
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
        self._event_loop = None
        self._login_domain = None
        self.__gate_url_for_requests = None

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
        # check for proxies in connection
        self.check_proxy()

        # set token if input
        if token is not None:
            self.token = token

        # STDOUT
        self.remove_keys_list = ['contributors', 'url', 'annotations', 'items', 'export', 'directoryTree',
                                 'attributes', 'partitions', 'metadata', 'stream', 'createdAt', 'updatedAt', 'arch']

        # API calls counter
        counter_filepath = os.path.join(os.path.dirname(self.cookie_io.COOKIE), 'calls_counter.json')
        self.calls_counter = CallsCounter(filepath=counter_filepath)

        # create a global thread pool to run multi threading
        if num_processes is None:
            num_processes = 3 * multiprocessing.cpu_count()
        self._num_processes = num_processes
        self._thread_pools_names = {'item.download': num_processes,
                                    'item.status_update': num_processes,
                                    'item.page': num_processes,
                                    'annotation.upload': num_processes,
                                    'annotation.download': num_processes,
                                    'annotation.update': num_processes,
                                    'entity.create': num_processes,
                                    'dataset.download': num_processes}
        # set logging level
        logging.getLogger(name='dtlpy').handlers[0].setLevel(logging._nameToLevel[self.verbose.logging_level.upper()])
        os.environ["USE_ATTRIBUTE_2"] = json.dumps(self.attributes_mode.use_attributes_2)

        self.cache = None
        #######################
        # start event tracker #
        self.event_tracker = Events(client_api=self)
        self.event_tracker.daemon = True
        self.event_tracker.start()

    @property
    def event_loop(self):
        self.lock.acquire()
        if self._event_loop is None:
            self._event_loop = self.create_event_loop_thread()
        elif not self._event_loop.loop.is_running():
            if self._event_loop.is_alive():
                self._event_loop.stop()
            self._event_loop = self.create_event_loop_thread()
        self.lock.release()
        return self._event_loop

    def build_cache(self, cache_config=None):
        if cache_config is None:
            cache_config_json = os.environ.get('CACHE_CONFIG', None)
            if cache_config_json is None:
                if self.sdk_cache.use_cache:
                    cache_config = CacheConfig.from_string(cls=CacheConfig, base64_string=self.sdk_cache.configs)
            else:
                cache_config = CacheConfig.from_string(cls=CacheConfig, base64_string=cache_config_json)
        if cache_config:
            # cache paths
            if os.environ.get('DEFAULT_CACHE_PATH', None) is None:
                os.environ['DEFAULT_CACHE_PATH'] = self.sdk_cache.cache_path_bin
            else:
                self.sdk_cache.cache_path_bin = os.environ['DEFAULT_CACHE_PATH']

            if not os.path.isdir(self.sdk_cache.cache_path_bin):
                os.makedirs(self.sdk_cache.cache_path_bin, exist_ok=True)

            if not os.path.isfile(os.path.join(self.sdk_cache.cache_path_bin, 'cacheConfig.json')):
                os.makedirs(self.sdk_cache.cache_path_bin, exist_ok=True)

            if isinstance(cache_config, str):
                self.sdk_cache.configs = cache_config
                cache_config = CacheConfig.from_string(cls=CacheConfig, base64_string=cache_config)
            elif isinstance(cache_config, CacheConfig):
                self.sdk_cache.configs = cache_config.to_string()
            else:
                raise Exception("config should be of type str or CacheConfig")
            try:
                self.cache = CacheManger(cache_configs=[cache_config], bin_cache_size=self.sdk_cache.bin_size)
                self.cache.ping()
                self.sdk_cache.use_cache = True
            except Exception as e:
                logger.warning("Cache build error {}".format(e))
                self.cache = None

    def __del__(self):
        for name, pool in self._thread_pools.items():
            pool.shutdown()
        self.event_loop.stop()

    def _build_request_headers(self, headers=None):
        if headers is None:
            headers = dict()
        if not isinstance(headers, dict):
            raise exceptions.PlatformException(
                error='400',
                message="Input 'headers' must be a dictionary, got: {}".format(type(headers)))
        headers.update(self.default_headers)
        headers.update(self.auth)
        headers.update({'User-Agent': requests_toolbelt.user_agent('dtlpy', __version__)})
        return headers

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
            self._thread_pools[pool].shutdown()
        self._thread_pools = dict()

    def create_event_loop_thread(self):
        loop = asyncio.new_event_loop()
        event_loop = AsyncThreadEventLoop(loop=loop,
                                          n=self._num_processes)
        event_loop.daemon = True
        event_loop.start()
        time.sleep(1)
        return event_loop

    def thread_pools(self, pool_name):
        if pool_name not in self._thread_pools_names:
            raise ValueError('unknown thread pool name: {}. known name: {}'.format(
                pool_name,
                list(self._thread_pools_names.keys())))
        num_processes = self._thread_pools_names[pool_name]
        if pool_name not in self._thread_pools or self._thread_pools[pool_name]._shutdown:
            self._thread_pools[pool_name] = ThreadPoolExecutor(max_workers=num_processes)
        pool = self._thread_pools[pool_name]
        assert isinstance(pool, concurrent.futures.ThreadPoolExecutor)
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
    def use_ssl_context(self):
        environments = self.environments
        use_ssl_context = False
        if self.environment in environments:
            if 'use_ssl_context' in environments[self.environment]:
                use_ssl_context = environments[self.environment]['use_ssl_context']
        return use_ssl_context

    @property
    def auth(self):
        return {'authorization': 'Bearer ' + self.token}

    @property
    def environment(self):
        _environment = self._environment
        if _environment is None:
            _environment = self.cookie_io.get('url')
            if _environment is None:
                _environment = DEFAULT_ENVIRONMENT
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
                _environments = DEFAULT_ENVIRONMENTS
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
    def cache_state(self):
        if self._cache_state is None:
            self._cache_state = CacheMode(cookie=self.cookie_io)
        assert isinstance(self._cache_state, CacheMode)
        return self._cache_state

    @property
    def attributes_mode(self):
        if self._attributes_mode is None:
            self._attributes_mode = Attributes2(cookie=self.cookie_io)
        assert isinstance(self._attributes_mode, Attributes2)
        return self._attributes_mode

    @property
    def platform_settings(self):
        if self._platform_settings is None:
            self._platform_settings = PlatformSettings()
        assert isinstance(self._platform_settings, PlatformSettings)
        return self._platform_settings

    @property
    def sdk_cache(self):
        if self._sdk_cache is None:
            self._sdk_cache = SDKCache(cookie=self.cookie_io)
        assert isinstance(self._sdk_cache, SDKCache)
        return self._sdk_cache

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

    def add_environment(self, environment,
                        audience=None,
                        client_id=None,
                        auth0_url=None,
                        verify_ssl=True,
                        token=None,
                        refresh_token=None,
                        alias=None,
                        use_ssl_context=False,
                        gate_url=None,
                        url=None,
                        login_domain=None
                        ):
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
                                     'gate_url': gate_url,
                                     'refresh_token': refresh_token,
                                     'verify_ssl': verify_ssl,
                                     'use_ssl_context': use_ssl_context,
                                     'url': url,
                                     'login_domain': login_domain}
        self.environments = environments

    def info(self, with_token=True):
        """
        Return a dictionary with current information: env, user, token
        :param with_token:
        :return:
        """
        user_email = 'null'
        if self.token is not None:
            payload = jwt.decode(self.token, algorithms=['HS256'],
                                 verify=False, options={'verify_signature': False})
            user_email = payload['email']
        information = {'environment': self.environment,
                       'user_email': user_email}
        if with_token:
            information['token'] = self.token
        return information

    @property
    def __base_gate_url(self):
        if self.__gate_url_for_requests is None:
            self.__gate_url_for_requests = self.environment
            internal_requests_url = os.environ.get('INTERNAL_REQUESTS_URL', None)
            if internal_requests_url is not None:
                self.__gate_url_for_requests = internal_requests_url
        return self.__gate_url_for_requests
        
    def export_curl_request(self, req_type, path, headers=None, json_req=None, files=None, data=None):
        curl, prepared = self._build_gen_request(req_type=req_type,
                                                 path=path,
                                                 headers=headers,
                                                 json_req=json_req,
                                                 files=files,
                                                 data=data)
        return curl

    def _build_gen_request(self, req_type, path, headers, json_req, files, data):
        req_type = req_type.upper()
        valid_request_type = ['GET', 'DELETE', 'POST', 'PUT', 'PATCH']
        assert req_type in valid_request_type, '[ERROR] type: %s NOT in valid requests' % req_type

        # prepare request
        req = requests.Request(method=req_type,
                               url=self.__base_gate_url + path,
                               json=json_req,
                               files=files,
                               data=data,
                               headers=self._build_request_headers(headers=headers))
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
        return curl, prepared

    def _convert_json_to_response(self, response_json):
        the_response = Response()
        the_response._content = json.dumps(response_json).encode('utf-8')
        return the_response

    def _cache_on(self, request):
        if self.cache is not None and self.sdk_cache.use_cache:
            pure_request = request.split('?')[0]
            valid_req = ['annotation', 'item', 'dataset', 'project', 'task', 'assignment']
            for req_type in valid_req:
                if req_type in pure_request:
                    return True
        return False

    @Decorators.token_expired_decorator
    def gen_request(self, req_type, path, data=None, json_req=None, files=None, stream=False, headers=None,
                    log_error=True, dataset_id=None, **kwargs):
        """
        Generic request from platform
        :param req_type: type of the request: GET, POST etc
        :param path: url (without host header - take from environment)
        :param data: data to pass to request
        :param json_req: json to pass to request
        :param files: files to pass to request
        :param stream: stream to pass the request
        :param headers: headers to pass to request. auth will be added to it
        :param log_error: if true - print the error log of the request
        :param dataset_id: dataset id needed in stream True
        :param kwargs: kwargs
        :return:
        """
        success, resp, cache_values = False, None, []
        if self.cache is None and 'sdk' not in path:
            self.build_cache()
        if req_type.lower() not in ['patch', 'put', 'post', 'delete'] and self._cache_on(request=path):
            try:
                if stream:
                    if dataset_id is None:
                        raise ValueError("must provide a dataset id")
                    success, cache_values = self.cache.read_stream(request_path=path, dataset_id=dataset_id)

                else:
                    success, cache_values = self.cache.read(request_path=path)
                if success:
                    resp = self._convert_json_to_response(cache_values)
            except Exception as e:
                logger.warning("Cache error {}".format(e))
                success, resp = False, None

        if not success and not resp:
            success, resp = self._gen_request(req_type=req_type,
                                              path=path,
                                              data=data,
                                              json_req=json_req,
                                              files=files,
                                              stream=stream,
                                              headers=headers,
                                              log_error=log_error)

            if success and self._cache_on(request=path):
                try:
                    if stream:
                        res = self.cache.write_stream(request_path=path,
                                                      response=resp,
                                                      dataset_id=dataset_id)
                        if res != '':
                            resp = self._convert_json_to_response(res)
                    else:
                        if req_type == 'delete':
                            self.cache.invalidate(path=path)
                        else:
                            try:
                                resp_list = resp.json()
                                write = True
                                if isinstance(resp_list, list):
                                    pass
                                elif isinstance(resp_list, dict):
                                    if 'hasNextPage' in resp_list:
                                        resp_list = resp_list['items']
                                    elif 'id' in resp_list:
                                        resp_list = [resp_list]
                                    else:
                                        write = False
                                else:
                                    raise exceptions.PlatformException(error='400', message="unsupported return type")
                                if write:
                                    self.cache.write(list_entities_json=resp_list)
                            except:
                                raise exceptions.PlatformException(error='400', message="failed to set cache")
                except Exception as e:
                    logger.warning("Cache error {}".format(e))
                    self.cache = None
        # only for projects events
        if success:
            if 'stack' in kwargs:
                self.event_tracker.put(event=kwargs.get('stack'), resp=resp, path=path)
        return success, resp

    def _gen_request(self, req_type, path, data=None, json_req=None, files=None, stream=False, headers=None,
                     log_error=True):
        """
        Generic request from platform
        :param req_type: type of the request: GET, POST etc
        :param path: url (without host header - take from environment)
        :param data: data to pass to request
        :param json_req: json to pass to request
        :param files: files to pass to request
        :param stream: stream to pass the request
        :param headers: headers to pass to request. auth will be added to it
        :param log_error: if true - print the error log of the request
        :return:
        """
        curl, prepared = self._build_gen_request(req_type=req_type,
                                                 path=path,
                                                 headers=headers,
                                                 json_req=json_req,
                                                 files=files,
                                                 data=data)
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
                                is_dataloop=True,
                                **kwargs):
        req_type = req_type.upper()
        valid_request_type = ['GET', 'DELETE', 'POST', 'PUT', 'PATCH']
        assert req_type in valid_request_type, '[ERROR] type: %s NOT in valid requests' % req_type

        # prepare request
        if is_dataloop:
            full_url = self.environment + path
            headers_req = self._build_request_headers(headers=headers)
        else:
            full_url = path
            headers = dict()
            headers_req = headers

        if headers is not None:
            if not isinstance(headers, dict):
                raise exceptions.PlatformException(error='400', message="Input 'headers' must be a dictionary")
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
                                        await asyncio.sleep(0)
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
                        except Exception:
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

    @Decorators.token_expired_decorator
    async def upload_file_async(self,
                                to_upload,
                                item_type,
                                item_size,
                                remote_url,
                                uploaded_filename,
                                remote_path=None,
                                callback=None,
                                mode='skip',
                                item_metadata=None,
                                headers=None,
                                item_description=None,
                                **kwargs):
        headers = self._build_request_headers(headers=headers)
        pbar = None
        if callback is None:
            if item_size > 10e6:
                # size larger than 10MB
                pbar = tqdm.tqdm(total=item_size,
                                 unit="B",
                                 unit_scale=True,
                                 unit_divisor=1024,
                                 position=1,
                                 file=sys.stdout,
                                 disable=self.verbose.disable_progress_bar,
                                 desc='Upload Items')

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
                if item_description is not None:
                    form.add_field('description', item_description)
                form.add_field('file', AsyncUploadStream(buffer=to_upload,
                                                         callback=callback,
                                                         name=uploaded_filename))
                url = '{}?mode={}'.format(self.environment + remote_url, mode)

                # use SSL context
                ssl_context = None
                if self.use_ssl_context:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                async with session.post(url,
                                        data=form,
                                        verify_ssl=self.verify,
                                        ssl=ssl_context) as resp:
                    self.last_request = resp.request_info
                    command = "curl -X {method} -H {headers} -d '{uri}'"
                    headers = ['"{0}: {1}"'.format(k, v) for k, v in resp.request_info.headers.items()]
                    headers = " -H ".join(headers)
                    self.last_curl = command.format(method=resp.request_info.method,
                                                    headers=headers,
                                                    uri=resp.request_info.url)
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
        if response.ok and self.cache is not None:
            try:
                self.cache.write(list_entities_json=[response.json()])
                dataset_id = url.split('/')[-2]
                self.cache.write_stream(request_path=url,
                                        buffer=to_upload,
                                        file_name=uploaded_filename,
                                        entity_id=response.json()['id'],
                                        dataset_id=dataset_id)
            except:
                logger.warning("Failed to add the file to the cache")
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
                                     file=sys.stdout,
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
                backoff_factor=1,
                # use on any request type
                allowed_methods=False,
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
                payload = jwt.decode(self.token, algorithms=['HS256'],
                                     options={'verify_signature': False}, verify=False)
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
                request_id = resp.headers.get('x-request-id', 'na')
                logger.debug('--- [Request] Start ---')
                logger.debug(self.print_request(req=resp.request, to_return=True))
                logger.debug('--- [Request] End ---')
                logger.debug('--- [Response][x-request-id:{}] Start ---'.format(request_id))
                to_print.print(show_all=False, level='debug')
                logger.debug('--- [Response][x-request-id:{}] End ---'.format(request_id))
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

        request_id = resp.headers.get('x-request-id', 'na')
        logger.debug('--- [Request] Start ---')
        logger.debug(self.print_request(req=resp.request, to_return=True))
        logger.debug('--- [Request] End ---')
        logger.debug('--- [Response][x-request-id:{}] Start ---'.format(request_id))
        if log_error:
            logger.error(msg)
        else:
            logger.debug(msg)
        logger.debug('--- [Response][x-request-id:{}] End ---'.format(request_id))
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
        elif env == 'custom':
            custom_env = os.environ.get('DTLPY_CUSTOM_ENV', None)
            environment = json.loads(base64.b64decode(custom_env.encode()).decode())
            env = environment.pop('url')
            self.environments[env] = environment.get(env, environment)
            verify_ssl = self.environments[env].get('verify_ssl', None)
            if verify_ssl is not None and isinstance(verify_ssl, str):
                self.environments[env]['verify_ssl'] = True if verify_ssl.lower() == 'true' else False
        else:
            matched_env = [env_url for env_url, env_dict in environments.items() if env_dict['alias'] == env]
            if len(matched_env) != 1:
                known_aliases = [env_dict['alias'] for env_url, env_dict in environments.items()]
                raise ConnectionError(
                    'Unknown platform environment: "{}". Known: {}'.format(env, ', '.join(known_aliases)))
            env = matched_env[0]
        if self.environment != env:
            self.environment = env
            self.__gate_url_for_requests = None
            # reset local token
            self._token = None
            self.refresh_token_active = True
        logger.info('Platform environment: {}'.format(self.environment))
        if self.token_expired():
            logger.info('Token expired, Please login.')

    ##########
    # Log in #
    ##########
    def login_secret(self, email, password, client_id, client_secret=None, force=False):
        """
        Login with email and password from environment variables.
        If already logged in with same user - login will NOT happen. see "force"

        :param email: user email.
        :param password: user password
        :param client_id: auth0 client id
        :param client_secret: secret that match the client id
        :param force: force login. in case login with same user but want to get a new JWT
        :return:
        """
        return login_secret(api_client=self,
                            email=email,
                            password=password,
                            client_id=client_id,
                            client_secret=client_secret,
                            force=force)

    def login_m2m(self, email, password, client_id=None, client_secret=None, force=False):
        """
        Login with email and password from environment variables
        :param email: user email. if already logged in with same user - login will NOT happen. see "force"
        :param password: user password
        :param client_id:
        :param client_secret:
        :param force: force login. in case login with same user but want to get a new JWT
        :return:
        """
        res = login_m2m(api_client=self,
                        email=email,
                        password=password,
                        client_id=client_id,
                        client_secret=client_secret,
                        force=force)
        if res:
            self._send_login_event(user_type='human', login_type='m2m')
        return res

    def login_token(self, token):
        """
        Login using existing token
        :param token: a valid token
        :return:
        """
        self.token = token  # this will also set the refresh_token to None

    @property
    def login_domain(self):
        if self._login_domain is None:
            self._login_domain = self.environments[self.environment].get('login_domain', None)
        return self._login_domain

    @login_domain.setter
    def login_domain(self, domain: str):
        if domain is not None and not isinstance(domain, str):
            raise exceptions.PlatformException('400', 'domain should be a string value')
        self._login_domain = domain
        self.environments[self.environment]['login_domain'] = domain
        self.cookie_io.put('login_parameters', self.environments)

    def login(self, audience=None, auth0_url=None, client_id=None, callback_port=None):
        """
        Login using Auth0.
        :return:
        """
        res = login(
            api_client=self,
            audience=audience,
            auth0_url=auth0_url,
            client_id=client_id,
            login_domain=self.login_domain,
            callback_port=callback_port
        )
        if res:
            self._send_login_event(user_type='human', login_type='interactive')
        return res

    def _send_login_event(self, user_type, login_type):
        event_payload = {
            'event': 'dtlpy:login',
            'properties': {
                'login_type': login_type,
                'user_type': user_type
            }
        }
        self.event_tracker.put(event=event_payload)

    def logout(self):
        """
        Logout.
        :return:
        """
        return logout(api_client=self)

    def _renew_token_in_dual_agent(self):
        renewed = False
        try:
            proxy_port = os.environ.get('AGENT_PROXY_MAIN_PORT') or "1001"
            resp = requests.get('http://localhost:{port}/get_jwt'.format(port=proxy_port))
            if resp.ok:
                self.token = resp.json()['jwt']
                renewed = True
            else:
                self.print_bad_response(resp)
        except Exception:
            logger.exception('Failed to get token from proxy')

        return renewed

    def renew_token(self):
        refresh_method = os.environ.get('DTLPY_REFRESH_TOKEN_METHOD', None)
        if refresh_method is not None and refresh_method == 'proxy':
            res = self._renew_token_in_dual_agent()
        else:
            res = self._renew_token_with_refresh_token()
        if res:
            self._send_login_event(user_type='human', login_type='refresh')
        return res

    def _renew_token_with_refresh_token(self):
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
            logger.debug('RefreshToken: Missing environments params for refreshing token')
            self.refresh_token_active = False

        if self.refresh_token_active is False:
            return renewed

        refresh_token = self.refresh_token

        env_params = self.environments[self.environment]
        if 'gate_url' not in env_params:
            env_params['gate_url'] = gate_url_from_host(environment=self.environment)
            self.environments[self.environment] = env_params
        token_endpoint = "{}/token?default".format(env_params['gate_url'])

        payload = {
            'type': 'refresh_token',
            'refresh_token': refresh_token
        }
        logger.debug("RefreshToken: Refreshing token via {}".format(token_endpoint))
        resp = requests.request("POST",
                                token_endpoint,
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

    def _get_resource_url(self, url):

        env = self._environments[self._environment]['alias']
        head = self._environments[self._environment].get('url', None)
        # TODO need to deprecate somehow (the following)
        if head is None:
            if env == 'prod':
                head = 'https://console.dataloop.ai/'
            elif env == 'dev':
                head = 'https://dev-con.dataloop.ai/'
            elif env == 'rc':
                head = 'https://rc-con.dataloop.ai/'
            elif env in ['local', 'minikube_local_mac']:
                head = 'https://localhost:8443/'
            elif env == 'new-dev':
                head = 'https://custom1-gate.dataloop.ai/'
            else:
                raise exceptions.PlatformException(error='400', message='Unknown environment: {}'.format(env))

        return head + url

    def _open_in_web(self, url):
        import webbrowser
        webbrowser.open(url=url, new=2, autoraise=True)


client = ApiClient()
