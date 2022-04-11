from urllib.parse import urlsplit, urlunsplit
import requests
import logging
import json
import jwt
import os

logger = logging.getLogger(name='dtlpy')


def login_m2m(api_client, email, password, client_id=None, client_secret=None, force=False):
    return login_secret(api_client=api_client,
                        email=email,
                        password=password,
                        client_id=client_id,
                        client_secret=client_secret,
                        force=force)


def login_secret(api_client, email, password, client_id, client_secret=None, force=False):
    """
    Login with email and password from environment variables
    :param api_client: ApiClient instance
    :param email: user email. if already logged in with same user - login will NOT happen. see "force"
    :param password: user password
    :param client_id: DEPRECATED
    :param client_secret: DEPRECATED
    :param force: force login. in case login with same user but want to get a new JWT
    :return:
    """
    # TODO add deprecation warning to client_id
    # check if already logged in with SAME email
    if api_client.token is not None or api_client.token == '':
        try:
            payload = jwt.decode(api_client.token, algorithms=['HS256'],
                                 options={'verify_signature': False}, verify=False)
            if 'email' in payload and \
                    payload['email'] == email and \
                    not api_client.token_expired() and \
                    not force:
                logger.warning('Trying to login with same email but token not expired. Not doing anything... '
                               'Set "force" flag to True to login anyway.')
                return True
        except jwt.exceptions.DecodeError:
            logger.debug('{}'.format('Cant decode token. Force login is used'))

    logger.info('[Start] Login Secret')
    env_params = api_client.environments[api_client.environment]
    # need to login
    payload = {'username': email,
               'password': password,
               'type': 'user_credentials'
               }
    headers = {'content-type': 'application/json'}
    if 'gate_url' not in env_params:
        env_params['gate_url'] = gate_url_from_host(environment=api_client.environment)
        api_client.environments[api_client.environment] = env_params
    token_url = env_params['gate_url'] + "/token?default"
    resp = requests.request("POST",
                            token_url,
                            data=json.dumps(payload),
                            headers=headers,
                            verify=env_params.get('verify_ssl', True))
    if not resp.ok:
        api_client.print_bad_response(resp)
        return False
    else:
        response_dict = resp.json()
        api_client.token = response_dict['id_token']  # this will also set the refresh_token to None
        if 'refresh_token' in response_dict:
            api_client.refresh_token = response_dict['refresh_token']

        # set new client id for refresh
        payload = jwt.decode(api_client.token, algorithms=['HS256'],
                             options={'verify_signature': False}, verify=False)
        if 'email' in payload:
            logger.info('[Done] Login Secret. User: {}'.format(payload['email']))
        else:
            logger.info('[Done] Login Secret. User: {}'.format(email))
            logger.info(payload)
    return True


def logout(api_client):
    """
    remove JWT from cookie
    """
    api_client.token = None
    api_client.refresh_token = None
    return True


def login(api_client, auth0_url=None, audience=None, client_id=None):
    import webbrowser
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs
    logger.info('Logging in to Dataloop...')

    class LocalServer:

        class Handler(BaseHTTPRequestHandler):

            tokens_obtained = False
            id_token = None
            access_token = None
            refresh_token = None

            def log_message(self, format, *args):
                return

            def do_GET(self):
                parsed_path = urlparse(self.path)
                query = parse_qs(parsed_path.query)
                self.send_response(200)

                # get display image
                try:
                    # working directory when running from command line
                    location = os.path.dirname(os.path.realpath(__file__))
                except NameError:
                    # working directory when running from console
                    location = './dtlpy/services'
                filename = os.path.join(location, '..', 'assets', 'lock_open.png')
                if os.path.isfile(filename):
                    with open(filename, 'rb') as f:
                        self.send_header('Content-type', 'image/jpg')
                        self.end_headers()
                        self.wfile.write(f.read())
                else:
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(bytes("<!doctype html><html><body>Logged in successfully</body></html>", 'utf-8'))
                self.__class__.id_token = query['id_token'][0]
                self.__class__.access_token = query['access_token'][0]
                self.__class__.refresh_token = query['refresh_token'][0]
                self.__class__.tokens_obtained = True

        def __init__(self):
            self.port = 3001
            self.server = HTTPServer(('', self.port), self.Handler)
            self.server.timeout = 60

        def process_request(self):
            self.server.handle_request()

            if self.Handler.tokens_obtained:
                return True, {
                    "id": self.Handler.id_token,
                    "access": self.Handler.access_token,
                    "refresh": self.Handler.refresh_token
                }
            else:
                return False, {}

        def local_endpoint(self):
            return "http://localhost:{}".format(self.port)

        def close(self):
            self.server.server_close()

    server = LocalServer()

    try:
        local_ep = server.local_endpoint()
        env_params = api_client.environments[api_client.environment]
        if 'gate_url' not in env_params:
            env_params['gate_url'] = gate_url_from_host(environment=api_client.environment)
            api_client.environments[api_client.environment] = env_params
        remote_ep = env_params['gate_url']
        login_page_url = "{}/login?callback={}".format(remote_ep, local_ep)
        logger.info("Launching interactive login via {}".format(remote_ep))
        webbrowser.open(url=login_page_url, new=2, autoraise=True)

        success, tokens = server.process_request()

        if success:
            decoded_jwt = jwt.decode(tokens['id'], verify=False,
                                     options={'verify_signature': False})

            if 'email' in decoded_jwt:
                logger.info('Logged in: {}'.format(decoded_jwt['email']))
            else:
                logger.info('Logged in: unknown user')

            api_client.token = tokens['id']
            api_client.refresh_token = tokens['refresh']

            return True
        else:
            logger.error('Login failed: no tokens obtained')
            return False
    except Exception as err:
        logger.exception('Login failed: error while getting token', err)
        return False
    finally:
        server.close()


def gate_url_from_host(environment):
    parsed = urlsplit(environment)
    return urlunsplit((parsed.scheme, parsed.netloc, '', '', ''))
