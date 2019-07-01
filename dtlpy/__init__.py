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
import json
import jwt

from .exceptions import PlatformException
from . import services, repositories
from .__version__ import version as __version__
from .entities import Box, Point, Segmentation, Polygon, Ellipse, Classification, Polyline
from .entities import AnnotationCollection, Annotation, Item, Package, Filters, Task, Session, Recipe, Ontology, Label

"""
Main Platform Interface module for Dataloop
"""

client_api = services.ApiClient()
projects = repositories.Projects(client_api=client_api)
datasets = repositories.Datasets(client_api=client_api, project=None)
tasks = repositories.Tasks(client_api=client_api)
plugins = repositories.Plugins(client_api=client_api)
sessions = repositories.Sessions(client_api=client_api, task=None)

logger = logging.getLogger(name='dataloop.platform_interface')

if client_api.token_expired():
    logger.error('Token expired. Please login')


def login(audience=None, auth0_url=None, client_id=None):
    """
    Login to Dataloop platform
    :param audience: optional -
    :param auth0_url: optional -
    :param client_id: optional -
    :return:
    """
    client_api.login(audience=audience, auth0_url=auth0_url, client_id=client_id)


def login_token(token):
    """
    Login with a token string
    :param token: valid token-id
    :return:
    """
    client_api.login_token(token=token)


def login_secret(email, password, client_id, client_secret):
    """
    Login with Auth0 clientID and secret
    :param email: user email
    :param password: user password
    :param client_id: auth0 client-id
    :param client_secret: auth0 secret
    :return:
    """

    client_api.login_secret(email=email,
                            password=password,
                            client_id=client_id,
                            client_secret=client_secret)


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


def info():
    payload = jwt.decode(token(), algorithms=['HS256'], verify=False)
    print('{}'.format(json.dumps(payload, indent=4)))
