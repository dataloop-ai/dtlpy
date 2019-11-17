#! /usr/bin/env python3
# This file is part of DTLPY.
#
# DTLPY is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DTLPY is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DTLPY.  If not, see <http://www.gnu.org/licenses/>.
import logging
import jwt
import sys
import os

from .exceptions import PlatformException
from . import services, repositories, exceptions, entities
from .__version__ import version as __version__
from .entities import Box, Point, Segmentation, Polygon, Ellipse, Classification, Polyline, Filters, Trigger, \
    AnnotationCollection, Annotation, Item, Package, Filters, Session, Recipe, Ontology, Label, Similarity, \
    PluginInput, ItemLink, UrlLink
from . import examples
from .services.check_sdk import check
from .utilities import Converter, BasePluginRunner, Progress

if os.name == "nt":
    # set encoding for windows printing
    os.environ["PYTHONIOENCODING"] = ":replace"
"""
Main Platform Interface module for Dataloop
"""
# check python version
if sys.version_info.major != 3:
    if sys.version_info.minor not in [5, 6]:
        sys.stderr.write(
            'Error: Your Python version "{}.{}" is NOT supported by Dataloop SDK dtlpy. '
            'Supported version are 3.5, 3.6)\n'.format(
                sys.version_info.major, sys.version_info.minor))
        sys.exit(-1)

"""
Main Platform Interface module for Dataloop
"""

##########
# Logger #
##########
logger = logging.getLogger(name=__name__)
logger = services.create_logger(logger, level=logging.WARNING)

################
# Repositories #
################
# Create repositories instances
client_api = services.ApiClient()
projects = repositories.Projects(client_api=client_api)
datasets = repositories.Datasets(client_api=client_api, project=None)
items = repositories.Items(client_api=client_api, datasets=datasets)
plugins = repositories.Plugins(client_api=client_api)
sessions = repositories.Sessions(client_api=client_api)
deployments = repositories.Deployments(client_api=client_api)

if client_api.token_expired():
    logger.error('Token expired. Please login')

try:
    check(version=__version__, client_api=client_api)
except Exception:
    logger.debug('Failed to check SDK! Continue without')


def login(audience=None, auth0_url=None, client_id=None):
    """
    Login to Dataloop platform
    :param audience: optional -
    :param auth0_url: optional -
    :param client_id: optional -
    :return:
    """
    client_api.login(audience=audience, auth0_url=auth0_url, client_id=client_id)


# noinspection PyShadowingNames
def login_token(token):
    """
    Login with a token string
    :param token: valid token-id
    :return:
    """
    client_api.login_token(token=token)


def login_secret(email, password, client_id, client_secret, force=False):
    """
    Login with Auth0 clientID and secret
    :param email: user email
    :param password: user password
    :param client_id: auth0 client-id
    :param client_secret: auth0 secret
    :param force: force the login (if user did not change and token still valid)
    :return:
    """

    client_api.login_secret(email=email,
                            password=password,
                            client_id=client_id,
                            client_secret=client_secret,
                            force=force)


# noinspection PyShadowingNames
def add_environment(environment, audience, client_id, auth0_url, verify_ssl=True, token=None, alias=None):
    client_api.add_environment(environment=environment,
                               audience=audience,
                               client_id=client_id,
                               auth0_url=auth0_url,
                               verify_ssl=verify_ssl,
                               token=token,
                               alias=alias)


def setenv(env):
    """
    Set an environment for API
    :param env:
    :return:
    """
    client_api.setenv(env=env)


def token_expired():
    """
    Check if token is expired
    :return: bool. True if token expired
    """
    return client_api.token_expired()


def token():
    """
    token
    :return: token in use
    """
    return client_api.token


def environment():
    """
    environment
    :return: current environment
    """
    return client_api.environment


def info(with_token=True):
    """
    Return a dictionary with current information: env, user, token
    :param with_token:
    :return:
    """
    user_email = 'null'
    if client_api.token is not None:
        payload = jwt.decode(client_api.token, algorithms=['HS256'], verify=False)
        user_email = payload['email']
    information = {'environment': client_api.environment,
                   'user_email': user_email}
    if with_token:
        information['token'] = client_api.token
    return information


def init():
    """
    init current directory as a Dataloop working directory
    :return:
    """
    from .services import CookieIO
    client_api.state_io = CookieIO.init_local_cookie(create=True)
    assert isinstance(client_api.state_io, CookieIO)
    logger.info('.Dataloop directory initiated successfully in {}'.format(os.getcwd()))


def checkout_state():
    """
    Return the current checked out state
    :return:
    """
    state = client_api.state_io.read_json()
    return state


class ModalityTypeEnum:
    """
    State enum
    """
    OVERLAY = 'overlay'


class SimilarityTypeEnum:
    """
    State enum
    """
    ID = 'id'
    URL = 'url'


class LinkTypeEnum:
    """
    State enum
    """
    ID = 'id'
    URL = 'url'

