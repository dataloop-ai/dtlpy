"""
Main Platform Interface module for Dataloop
"""
import logging

from . import services, repositories
from .__version__ import version


class PlatformInterface:
    """
    Platform Interface repository
    """
    __version__ = version

    def __init__(self):
        super().__init__()
        self._client_api = services.ApiClient()
        self._projects = repositories.Projects()
        self._datasets = repositories.Datasets(project=None)
        self._tasks = repositories.Tasks()
        self._sessions = repositories.Sessions(task=None)

        self.logger = logging.getLogger(name='dataloop.platform_interface')

        if self._client_api.token_expired():
            self.logger.exception('Token expired. Please login')


    def login(self, audience=None, auth0_url=None, client_id=None):
        """
        Login to Dataloop platform
        :param audience: optional -
        :param auth0_url: optional -
        :param client_id: optional -
        :return:
        """
        self._client_api.login(audience=audience, auth0_url=auth0_url, client_id=client_id)

    def login_token(self, token):
        """
        Login with a token string
        :param token: valid token-id
        :return:
        """
        self._client_api.login_token(token=token)

    def login_secret(self, email, password, client_id, client_secret):
        """
        Login with Auth0 clientID and secret
        :param email: user email
        :param password: user password
        :param client_id: auth0 client-id
        :param client_secret: auth0 secret
        :return:
        """

        self._client_api.login_secret(email=email,
                                      password=password,
                                      client_id=client_id,
                                      client_secret=client_secret)

    def add_environment(self, environment, audience, client_id, auth0_url, verify_ssl=True, token=None, alias=None):
        self._client_api.add_environment(environment=environment,
                                         audience=audience,
                                         client_id=client_id,
                                         auth0_url=auth0_url,
                                         verify_ssl=verify_ssl,
                                         token=token,
                                         alias=alias)

    def setenv(self, env):
        """
        Set an environment for API
        :param env:
        :return:
        """
        self._client_api.setenv(env=env)

    def token_expired(self):
        """
        Check if token is expired
        :return: bool. True if token expired
        """
        return self._client_api.token_expired()

    @property
    def token(self):
        """
        token
        :return: token in use
        """
        return self._client_api.token

    @property
    def environment(self):
        """
        environment
        :return: current environment
        """
        return self._client_api.environment

    @property
    def projects(self):
        """
        Projects repository
        :return:
        """
        return self._projects

    @property
    def datasets(self):
        """
        Datasets repository
        :return:
        """
        return self._datasets

    @property
    def tasks(self):
        """
        Tasks repository
        :return:
        """
        return self._tasks

    @property
    def packages(self):
        """
        Packages repository
        :return:
        """
        return self._packages

    @property
    def sessions(self):
        """
        Sessions repository
        :return:
        """
        return self._sessions
