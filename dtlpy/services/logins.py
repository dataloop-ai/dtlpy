import threading
import requests
import logging
import hashlib
import base64
import json
import jwt
import os
from urllib.parse import urlencode

logger = logging.getLogger(name=__name__)
threadLock = threading.Lock()


def login_secret(api_client, email, password, client_id, client_secret, force=False):
    """
    Login with email and password from environment variables
    :param api_client: ApiClient instance
    :param email: user email. if already logged in with same user - login will NOT happen. see "force"
    :param password: user password
    :param client_id:
    :param client_secret:
    :param force: force login. in case login with same user but want to get a new JWT
    :return:
    """
    # check if already logged in with SAME email
    if api_client.token is not None or api_client.token == '':
        try:
            payload = jwt.decode(api_client.token, algorithms=['HS256'], verify=False)
            if 'email' in payload and \
                    payload['email'] == email and \
                    not api_client.token_expired() and \
                    not force:
                logger.warning('Trying to login with same email but token not expired. Not doing anything... '
                               'Set "force" flag to True to login anyway.')
                return True
        except jwt.exceptions.DecodeError:
            logger.debug('{}'.format('Cant decode token. Force login is user'))

    logger.info('[Start] Login Secret')
    environment = api_client.environment
    audience = None
    auth0_url = None
    for env, env_params in api_client.environments.items():
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
        api_client.print_bad_response(resp)
        return False
    else:
        response_dict = resp.json()
        api_client.token = response_dict['id_token']  # this will also set the refresh_token to None
        if 'refresh_token' in response_dict:
            api_client.refresh_token = response_dict['refresh_token']
        payload = jwt.decode(api_client.token, algorithms=['HS256'], verify=False)
        if 'email' in payload:
            logger.info('[Done] Login Secret. User: {}'.format(payload['email']))
        else:
            logger.info('[Done] Login Secret. User: {}'.format(email))
            logger.info(payload)
    return True


def login(api_client, audience=None, auth0_url=None, client_id=None):
    """
    Login using Auth0.
    :param api_client: ApiClient instance
    :param audience:
    :param auth0_url:
    :param client_id:
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
    if api_client.environment in api_client.environments.keys():
        env_params = api_client.environments[api_client.environment]
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
        api_client.add_environment(environment=api_client.environment,
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

        def log_message(api_client, format, *args):
            return

        def do_GET(api_client):
            global query_dict
            parsed_path = urlparse(api_client.path)
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
                        api_client.send_response(200)
                        api_client.send_header('Content-type', 'image/jpg')
                        api_client.end_headers()
                        api_client.wfile.write(f.read())
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
                api_client.print_bad_response(resp)
                login_success = False
            else:
                response_dict = resp.json()
                final_token = response_dict['id_token']
                api_client.token = final_token  # this will also set the refresh_token to None
                if 'refresh_token' in response_dict:
                    api_client.refresh_token = response_dict['refresh_token']

                payload = jwt.decode(api_client.token, algorithms=['HS256'], verify=False)
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
