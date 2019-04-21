"""
Dataloop platform calls
"""
import requests_toolbelt
import mimetypes
import datetime
import requests
import logging
import hashlib
import base64
import fleep
import json
import jwt
import os

import pandas as pd
import numpy as np

from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from urllib.parse import urlencode
from tabulate import tabulate
from functools import wraps

logger = logging.getLogger('dataloop.api_client')


class PlatformError(Exception):
    """
    Error handling for api calls
    """

    def __init__(self, resp):
        msg = ''
        if hasattr(resp, 'status_code'):
            msg += '\nstatus_code:%s' % resp.status_code
        if hasattr(resp, 'reason'):
            msg += '\nreason:%s' % resp.reason
        if hasattr(resp, 'text'):
            msg += '\ntext:%s' % resp.text
        super().__init__(msg)


class CookieIO:
    """
    Cookie interface for Dataloop parameters
    """

    def __init__(self):
        self.COOKIE = os.path.join(os.path.expanduser('~'), '.dataloop', 'cookie')
        # create directory '.dataloop' if not exists
        if not os.path.exists(os.path.dirname(self.COOKIE)):
            os.makedirs(os.path.dirname(self.COOKIE))

        if not os.path.exists(self.COOKIE) or os.path.getsize(self.COOKIE) == 0:
            self.reset()
        try:
            with open(self.COOKIE, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            print('{} is corrupted'.format(self.COOKIE))
            raise SystemExit

    def get(self, key):
        with open(self.COOKIE, 'r') as fp:
            cfg = json.load(fp)
        if key in cfg.keys():
            return cfg[key]
        else:
            logger.warning(msg='key not in platform cookie file: %s. default is None' % key)
            return None

    def put(self, key, value):
        with open(self.COOKIE, 'r') as fp:
            cfg = json.load(fp)
        cfg[key] = value
        with open(self.COOKIE, 'w') as fp:
            json.dump(cfg, fp, indent=4)

    def reset(self):
        with open(self.COOKIE, 'w') as fp:
            json.dump({}, fp)


class Decorators:
    @staticmethod
    def token_expired_decorator(method):
        @wraps(method)
        def decorated_method(inst, *args, **kwargs):
            # before the method call
            if inst.token_expired():
                raise ConnectionRefusedError('Token expired, Please login.')
            # the actual method call
            result = method(inst, *args, **kwargs)
            # after the method call
            return result

        return decorated_method


class ApiClient:
    """
    API calls to Dataloop gate
    """

    def __init__(self, token=None):
        ############
        # Initiate #
        ############
        self.last_response = None
        self.last_request = None
        self.platform_exception = None
        self.last_curl = None
        self.io = CookieIO()

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
        return self.io.get('url')

    @environment.setter
    def environment(self, env):
        self.io.put('url', env)

    @property
    def environments(self):
        """
        List of known environments
        :return:
        """
        # get environment login parameters
        env_dict = self.io.get('login_parameters')
        if env_dict is None:
            # default
            env_dict = {
                'https://dev-gate.dataloop.ai/api/v1':
                    {'alias': 'dev',
                     'audience': 'https://dataloop-development.auth0.com/api/v2/',
                     'client_id': 'I4Arr9ixs5RT4qIjOGtIZ30MVXzEM4w8',
                     'auth0_url': 'https://dataloop-development.auth0.com',
                     'token': '',
                     'verify_ssl': True},
                'https://gate.dataloop.ai/api/v1': {'alias': 'prod',
                                                    'audience': 'https://dataloop-production.auth0.com/userinfo',
                                                    'client_id': 'FrG0HZga1CK5UVUSJJuDkSDqItPieWGW',
                                                    'auth0_url': 'https://dataloop-production.auth0.com',
                                                    'token': '',
                                                    'verify_ssl': True},
                'https://localhost:8443/api/v1': {'alias': 'local',
                                                  'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                  'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                  'auth0_url': 'https://dataloop-local.auth0.com',
                                                  'token': '',
                                                  'verify_ssl': False},
                'https://172.17.0.1:8443/api/v1': {'alias': 'docker_linux',
                                                   'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                   'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                   'auth0_url': 'https://dataloop-local.auth0.com',
                                                   'token': '',
                                                   'verify_ssl': False},
                'https://host.docker.internal:8443/api/v1': {'alias': 'docker_windows',
                                                             'audience': 'https://dataloop-local.auth0.com/userinfo',
                                                             'client_id': 'ewGhbg5brMHOoL2XZLHBzhEanapBIiVO',
                                                             'auth0_url': 'https://dataloop-local.auth0.com',
                                                             'token': '',
                                                             'verify_ssl': False}
            }
            # write default to file
            self.io.put('login_parameters', env_dict)
        return env_dict

    @environments.setter
    def environments(self, env_dict):
        self.io.put('login_parameters', env_dict)

    @property
    def verbose(self):
        verbose = self.io.get('verbose')
        if verbose is None:
            verbose = False
            self.verbose = verbose
        return verbose

    @verbose.setter
    def verbose(self, verbose):
        self.io.put(key='verbose', value=verbose)

    @property
    def token(self):
        environments = self.environments
        token = None
        if self.environment in environments:
            if 'token' in environments[self.environment]:
                token = environments[self.environment]['token']
        return token

    @token.setter
    def token(self, token):
        environments = self.environments
        if self.environment in environments:
            environments[self.environment]['token'] = token
        else:
            environments[self.environment] = {'token': token}
        self.environments = environments

    def add_environment(self, environment, audience, client_id, auth0_url, verify_ssl=True, token=None, alias=None):
        environments = self.environments
        if environment in environments:
            logger.warning('Environment exists. Overwriting. env: %s' % environment)
        if token is None:
            token = ''
        if alias is None:
            alias = ''
        environments[environment] = {'audience': audience,
                                     'client_id': client_id,
                                     'auth0_url': auth0_url,
                                     'alias': alias,
                                     'token': token,
                                     'verify_ssl': verify_ssl}
        self.environments = environments

    @Decorators.token_expired_decorator
    def gen_request(self, req_type, path, data=None, json_req=None, files=None, stream=False, headers=None):
        """
        Generic request from platform
        :param req_type:
        :param path:
        :param data:
        :param json_req:
        :param files:
        :param stream:
        :param headers:
        :return:
        """
        req_type = req_type.upper()
        valid_request_type = ['GET', 'DELETE', 'POST', 'PUT', 'PATCH']
        assert req_type in valid_request_type, '[ERROR] type: %s NOT in valid requests' % req_type

        # prepare request
        headers_req = self.auth
        if headers is not None:
            # combine input headers with auth
            headers_req = {**self.auth, **headers}
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
        with requests.Session() as s:
            retry = Retry(
                total=3,
                read=3,
                connect=3,
                backoff_factor=0.3,
            )
            adapter = HTTPAdapter(max_retries=retry)
            s.mount('http://', adapter)
            s.mount('https://', adapter)
            resp = s.send(request=prepared, stream=stream, verify=self.verify)
        self.last_response = resp
        # handle output
        if not resp.ok:
            self.print_bad_response(resp)
            return_type = False
        else:
            try:
                # print only what is printable (dont print get steam etc..)
                if not stream:
                    self.print_json(resp.json())
            except ValueError:
                # no JSON returned
                pass
            return_type = True
        return return_type, resp

    def upload_local_file(self, filepath, remote_url, uploaded_filename=None, remote_path=None, callback=None):
        """
        Upload a file (Streaming..)
        :param filepath:
        :param remote_url:
        :param uploaded_filename:
        :param remote_path:
        :param callback:
        :return:
        """
        if uploaded_filename is None:
            uploaded_filename = os.path.basename(filepath)
        if remote_path is None:
            remote_path = '/'
        if os.path.isfile(filepath):
            item_type = 'file'
        else:
            item_type = 'dir'
        statinfo = os.stat(filepath)
        try:
            # read beginning for mime type
            try:
                _, ext = os.path.splitext(filepath)
                if ext in mimetypes.types_map:
                    mime = mimetypes.types_map[ext.lower()]
                else:
                    import magic
                    mime = magic.Magic(mime=True)
                    mime = mime.from_file(filepath)
            except:
                mime = 'unknown'

            with open(filepath, 'rb') as file:
                info = fleep.get(file.read(128))
            # multipart uploading of the file
            with open(filepath, 'rb') as f:
                file = requests_toolbelt.MultipartEncoder(fields={
                    'file': (uploaded_filename, f, mime),
                    'type': item_type,
                    'path': os.path.join(remote_path, uploaded_filename).replace('\\', '/'),
                })
                # move file to last part
                lens = [part.len for part in file.parts]
                temp = file.parts[2]
                file.parts[2] = file.parts[np.argmax(lens)]
                file.parts[np.argmax(lens)] = temp
                # create callback
                if callback is None:
                    if statinfo.st_size > 10e6:
                        pbar = ProgressBar(
                            widgets=[' [', Timer(), '] ', Bar(), ' (', FileTransferSpeed(), ' | ', DataSize(),
                                     ' | ', ETA(), ')'])
                        pbar.max_value = file.len

                        def callback(monitor):
                            pbar.update(monitor.bytes_read)
                    else:
                        def callback(monitor):
                            pass
                monitor = requests_toolbelt.MultipartEncoderMonitor(file, callback)
                headers = {'Content-Type': monitor.content_type}
                req = requests.Request('POST', self.environment + remote_url,
                                       headers={**self.auth, **headers},
                                       data=monitor)
                # prepare to send
                prepared = req.prepare()
                with requests.Session() as s:
                    retry = Retry(
                        total=3,
                        read=3,
                        connect=3,
                        backoff_factor=0.3,
                    )
                    adapter = HTTPAdapter(max_retries=retry)
                    s.mount('http://', adapter)
                    s.mount('https://', adapter)
                    resp = s.send(prepared, verify=self.verify)
            self.last_response = resp
            self.last_request = prepared
            # handle output
            if not resp.ok:
                self.print_bad_response(resp)
                success = False
            else:
                try:
                    # print only what is printable (dont print get steam etc..)
                    self.print_json(resp.json())
                except ValueError:
                    # no JSON returned
                    pass
                success = True
        except Exception as e:
            logger.exception(e)

            success = False
            resp = None
        return success, resp

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
            logger.exception(err)
            return True
        except Exception as err:
            logger.exception(err)
            return True

    ##########
    # STDOUT #
    ##########
    def print_json(self, to_print):
        """
        Print tabulate response
        :param to_print:
        :return:
        """
        try:
            if self.verbose is False:
                return
            import collections
            if isinstance(to_print, dict):
                keys_list = list(to_print.keys())
                to_print = [to_print]
            elif isinstance(to_print, list):
                if len(to_print) == 0:
                    keys_list = ['']
                else:
                    keys_list = list()
                    for item in to_print:
                        [keys_list.append(key) for key in list(item.keys()) if key not in keys_list]
            else:
                msg = 'Unknown printing input type: %s' % type(to_print)
                logger.exception(msg)
                raise ValueError(msg)

            try:
                # try sorting bt creation date
                to_print = sorted(to_print, key=lambda k: k['createdAt'])
            except KeyError:
                pass
            except Exception as err:
                logger.exception(err)

            if self.minimal_print:
                for key in self.remove_keys_list:
                    if key in keys_list:
                        keys_list.remove(key)

            # keys_list = ['name']#, 'id']

            df = pd.DataFrame(to_print, columns=keys_list)
            logger.debug('\n%s' % tabulate(df, headers='keys', tablefmt='psql'))

        except Exception as err:
            logger.exception('Printing response from gate:')
            logger.exception(err)

    def print_bad_response(self, resp=None):
        """
        Print error from platform
        :param resp:
        :return:
        """
        if resp is None:
            resp = self.last_response
        if hasattr(resp, 'status_code'):
            logger.exception('status_code:%s' % resp.status_code)
        if hasattr(resp, 'reason'):
            logger.exception('reason:%s' % resp.reason)
        if hasattr(resp, 'text'):
            logger.exception('text:%s' % resp.text)
        logger.exception(resp)
        self.platform_exception = PlatformError(resp)

    def print_request(self, req=None, to_return=False):
        """
        Print a request to the platform
        :param req:
        :param to_return:
        :return:
        """
        if not req:
            req = self.last_request
        msg = '{}\n{}\n{}\n\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
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
                logger.exception('Unknown environment. Please add environment to SDK ("add_environment" method)')
                raise ConnectionError('Unknown environment. Please add environment to SDK ("add_environment" method)')
        else:
            env = [env_url for env_url, env_dict in environments.items() if env_dict['alias'] == env]
            if len(env) != 1:
                known_aliases = [env_dict['alias'] for env_url, env_dict in environments.items()]
                logger.exception('Unknown environment alias: \'%s\'. known: %s' % (env, ', '.join(known_aliases)))
                raise ConnectionError(
                    'Unknown platform environment: \'%s\'. . known: %s' % (env, ', '.join(known_aliases)))
            env = env[0]
        self.environment = env
        logger.info('Platform environment: %s' % self.environment)
        if self.token_expired():
            logger.info('Token expired, Please login.')

    ##########
    # Log in #
    ##########
    def login_secret(self, email, password, client_id, client_secret):
        """
        Login with email and password from environment variables
        :param email:
        :param password:
        :param client_id:
        :param client_secret:
        :return:
        """
        environment = self.environment
        audience = None
        auth0_url = None
        for env, env_params in self.environments.items():
            if env == environment:
                audience = env_params['audience']
                auth0_url = env_params['auth0_url']
        missing = False
        if audience is None:
            logger.exception('audience not found. Please add a new environment to SDK. env: %s' % environment)
            missing = True
        if auth0_url is None:
            logger.exception('auth0_url not found. Please add a new environment to SDK. env: %s' % environment)
            missing = True
        if missing:
            raise ConnectionError('Some values are missing. See above for full error')
        # need to login
        payload = {'username': email,
                   'password': password,
                   'grant_type': 'password',
                   'audience': audience,
                   'scope': 'openid email',
                   'client_id': client_id,
                   'client_secret': client_secret
                   }
        headers = {
            'content-type': 'application/json',
            'Cache-Control': 'no-cache',
            'Postman-Token': 'c9e3e17b-00a6-4329-93c3-a9cea74f3f6b'
        }
        token_url = auth0_url + '/oauth/token'
        resp = requests.request("POST", token_url, data=json.dumps(payload), headers=headers)
        if not resp.ok:
            self.print_bad_response(resp)
            return False
        else:
            token = resp.json()['id_token']
            self.token = token
            payload = jwt.decode(self.token, algorithms=['HS256'], verify=False)
            if 'email' in payload:
                logger.info('Logged in: %s' % payload['email'])
            else:
                logger.info('Logged in: %s' % email)
                logger.info(payload)
        return True

    ##########
    def login_token(self, token):
        """
        Login using existing token
        :param token: a valid token
        :return:
        """
        self.token = token

    def login(self, audience=None, auth0_url=None, client_id=None):
        """
        Login using Auth0.
        :return:
        """
        import webbrowser
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from urllib.parse import urlparse, parse_qs

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
                logger.exception('Missing parameter for environment missing. Need to input "audience"')
                missing = True
            if client_id is None:
                logger.exception('Missing parameter for environment missing. Need to input "client_id"')
                missing = True
            if auth0_url is None:
                logger.exception('Missing parameter for environment missing. Need to input "auth0_url"')
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
                   'scope': 'openid email',
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
                    final_token = resp.json()['id_token']
                    self.token = final_token
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
            logger.exception(err)
        finally:
            # shutdown local server
            server.server_close()
        return login_success
