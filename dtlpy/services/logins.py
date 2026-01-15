from urllib.parse import urlsplit, urlunsplit
import base64
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
        logged_email = api_client.info()['user_email']
        if logged_email == email and \
            not api_client.token_expired() and \
            not force:
            return True
        else:
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
        logout(api_client=api_client)
        api_client.print_bad_response(resp)
        return False
    else:
        response_dict = resp.json()
        api_client.token = response_dict['id_token']  # this will also set the refresh_token to None
        if 'refresh_token' in response_dict:
            api_client.refresh_token = response_dict['refresh_token']

        # set new client id for refresh
        logged_email = api_client.info()['user_email']

        if not logged_email == 'null':
            logger.info(f'[Done] Login Secret. User: {logged_email}')
        else:
            logger.info(f'[Done] Login Secret. User: {email}')
    return True


def logout(api_client):
    """
    remove JWT from cookie
    """
    api_client.token = None
    api_client.refresh_token = None
    return True


def login_html():
    try:
        location = os.path.dirname(os.path.realpath(__file__))
    except NameError:
        location = './dtlpy/services'
    filename = os.path.join(location, '..', 'assets', 'lock_open.png')

    if os.path.isfile(filename):

        with open(filename, 'rb') as f:
            image = f.read()

        html = (
            "        <!doctype html>\n"
            "        <html>\n"
            "        <head>\n"
            "            <style>\n"
            "                body {{\n"
            "                    background-color: #F7F7F9 !important;\n"
            "                    display: flex;\n"
            "                    justify-content: center;\n"
            "                    align-items: center;\n"
            "                    height: 100vh;\n"
            "                    width: 100vw;\n"
            "                    margin: 0;\n"
            "                }}\n"
            "                img {{\n"
            "                    display: block;\n"
            "                    max-width: 100%;\n"
            "                    max-height: 100%;\n"
            "                    margin: auto;\n"
            "                }}\n"
            "            </style>\n"
            "        </head>\n"
            "        <body>\n"
            "            <img src='data:image/png;base64,{image}'>\n"
            "        </body>\n"
            "        </html>\n"
        ).format(image=base64.b64encode(image).decode())
    else:
        html = "<!doctype html><html><body>Logged in successfully</body></html>"

    return html.encode('utf-8')


def login(api_client, auth0_url=None, audience=None, client_id=None, login_domain=None, callback_port=None):
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
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(login_html())
                self.__class__.id_token = query['id_token'][0]
                self.__class__.access_token = query['access_token'][0]
                self.__class__.refresh_token = query['refresh_token'][0]
                self.__class__.tokens_obtained = True

        def __init__(self):
            self.port = callback_port if callback_port is not None else 3001
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
        if login_domain is not None:
            login_page_url = "{}&domain={}".format(login_page_url, login_domain)
        logger.info("Launching interactive login via {}".format(remote_ep))
        webbrowser.open(url=login_page_url, new=2, autoraise=True)

        success, tokens = server.process_request()

        if success:
            # oxsec-disable jwt-signature-disabled - Client-side SDK: signature verification disabled intentionally to extract claims for display; server validates on API calls
            decoded_jwt = jwt.decode(
                tokens['id'],
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                }
            )

            if 'email' in decoded_jwt:
                logger.info('Logged in: {}'.format(decoded_jwt['email']))
            else:
                logger.info('Logged in: unknown user')

            api_client.token = tokens['id']
            api_client.refresh_token = tokens['refresh']

            return True
        else:
            logout(api_client=api_client)
            logger.error('Login failed: no tokens obtained')
            return False
    except Exception as err:
        logout(api_client=api_client)
        logger.exception('Login failed: error while getting token', err)
        return False
    finally:
        server.close()


def gate_url_from_host(environment):
    parsed = urlsplit(environment)
    return urlunsplit((parsed.scheme, parsed.netloc, '', '', ''))
