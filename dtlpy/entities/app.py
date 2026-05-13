from collections import namedtuple
import traceback
import datetime
import logging
import requests
from enum import Enum

import attr
import jwt

from .. import entities, repositories, exceptions
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class AppScope(str, Enum):
    """ The scope of the app.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - SYSTEM
         - Dataloop internal app
       * - PROJECT
         - Project app
    """
    SYSTEM = 'system'
    PROJECT = 'project'


@attr.s
class App(entities.BaseEntity):
    id = attr.ib(type=str)
    name = attr.ib(type=str)
    url = attr.ib(type=str)
    created_at = attr.ib(type=str)
    updated_at = attr.ib(type=str)
    creator = attr.ib(type=str)
    project_id = attr.ib(type=str)
    org_id = attr.ib(type=str)
    dpk_name = attr.ib(type=str)
    dpk_version = attr.ib(type=str)
    composition_id = attr.ib(type=str)
    scope = attr.ib(type=str)
    routes = attr.ib(type=dict)
    custom_installation = attr.ib(type=dict)
    metadata = attr.ib(type=dict)
    status = attr.ib(type=entities.CompositionStatus)
    settings = attr.ib(type=dict)
    dpk = attr.ib(type=entities.Dpk)

    # sdk
    project = attr.ib(type=entities.Project, repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)
    integrations = attr.ib(type=list, default=None)

    # endpoint state (runtime-only, not serialized)
    _endpoint_url = attr.ib(default=None, repr=False)
    _endpoint_session = attr.ib(default=None, repr=False)
    _cached_route_key = attr.ib(default=None, repr=False)

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories', field_names=['projects', 'apps', 'compositions', 'models'])
        return reps(
            projects=repositories.Projects(client_api=self._client_api),
            apps=repositories.Apps(client_api=self._client_api, project=self.project, project_id=self.project_id),
            compositions=repositories.Compositions(client_api=self._client_api, project=self.project),
            models=repositories.Models(client_api=self._client_api, app=self)
        )


    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def apps(self):
        assert isinstance(self._repositories.apps, repositories.Apps)
        return self._repositories.apps

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    @property
    def compositions(self):
        assert isinstance(self._repositories.compositions, repositories.Compositions)
        return self._repositories.compositions

    def uninstall(self):
        """
        Uninstall an app installed app from the project.

        **Example**
        .. code-block:: python
            succeed = app.uninstall()
        """
        return self.apps.uninstall(app=self)

    def update(self):
        """
        Update the current app to the new configuration

        :return bool whether the operation ran successfully or not

        **Example**
        .. code-block:: python
            succeed = app.update()
        """
        return self.apps.update(self)

    def resume(self):
        """
        Resume the current app

        :return bool whether the operation ran successfully or not

        **Example**
        .. code-block:: python
            succeed = app.resume()
        """
        return self.apps.resume(self)

    def pause(self):
        """
        Pause the current app

        :return bool whether the operation ran successfully or not

        **Example**
        .. code-block:: python
            succeed = app.pause()
        """
        return self.apps.pause(self)

    def _is_app_jwt_expired(self, margin_seconds: int = 60) -> bool:
        """
        Check whether the **JWT-APP** (app-route) token is expired or about to expire.

        This is **not** the same as :meth:`~dtlpy.services.api_client.ApiClient.token_expired`:
        ``ApiClient.token_expired`` inspects ``client_api.token`` (the gate Bearer JWT) and may
        trigger refresh-token renewal. Here we only inspect the **JWT-APP** cookie set on the
        redirect to the app service host. Reusing ``token_expired()`` would check the wrong
        credential. The expiry math matches the gate token logic (same margin idea as
        ``token_expired(t=60)``: treat as expired when ``now >= exp - margin_seconds``).

        Decode uses ``verify_exp=False`` on purpose (same as ``ApiClient``): client-side
        scheduling only; the app service still enforces auth on each request.

        :param int margin_seconds: refresh when fewer than this many seconds remain
        :return: True if expired, missing, or no session exists
        :rtype: bool
        """
        if self._endpoint_session is None:
            return True
        token = self._endpoint_session.cookies.get("JWT-APP")
        if not token:
            return True
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                })
            exp = payload.get("exp")
            if exp is None:
                return True
            now = datetime.datetime.now(datetime.timezone.utc).timestamp()
            return now >= (exp - margin_seconds)
        except jwt.exceptions.DecodeError:
            logger.warning("Failed to decode JWT-APP cookie")
            return True

    def _get_route(self, route_name: str = None):
        """
        Return (route_key, route_url) for the given route_name.
        Raises if multiple routes exist and route_name is not specified.
        """
        if not self.routes:
            raise exceptions.PlatformException(
                error='400',
                message='App has no routes. Cannot resolve endpoint.')

        key = None
        route = None
        if route_name is not None:
            if route_name not in self.routes:
                raise exceptions.PlatformException(
                    error='404',
                    message='Route {!r} not found. Available routes: {}'.format(
                        route_name, list(self.routes.keys())))
            key = route_name
            route = self.routes[key]
        elif len(self.routes) > 1:
            raise exceptions.PlatformException(
                error='400',
                message='App has multiple routes ({}). '
                        'Specify route_name explicitly.'.format(
                            list(self.routes.keys())))
        else:
            key = next(iter(self.routes))
            route = self.routes[key]
        return key, route

    def _resolve_endpoint(self, path: str, route_key: str, route: str):
        """
        Follow the gateway redirect to discover the real service URL and capture
        the JWT-APP cookie.

        Failures from the backend use ``PlatformException(resp)`` so the status
        and message match the backend response (same pattern as
        :meth:`ApiClient.check_response`). If the response is ok but ``JWT-APP``
        is not set, we raise ``401`` -- the auth handshake silently failed on the
        SDK side.
        """
        route_base = route.rstrip("/")

        if self._endpoint_session is not None:
            self._endpoint_session.close()

        session = requests.Session()
        resolve_url = route_base + path
        try:
            resp = session.get(resolve_url,
                               headers=self._client_api.auth,
                               verify=self._client_api.verify,
                               timeout=30)
        except Exception:
            logger.error('Failed to resolve app endpoint: %s', resolve_url)
            raise

        if not resp.history:
            session.close()
            raise exceptions.PlatformException(
                error=str(resp.status_code),
                message='Gateway did not redirect for endpoint resolution (HTTP {}).'.format(
                    resp.status_code))

        jwt_token = session.cookies.get("JWT-APP")
        if not jwt_token:
            session.close()
            raise exceptions.PlatformException(
                error='401',
                message='JWT-APP cookie was not set after gateway redirect (HTTP {}).'.format(
                    resp.status_code))

        session.headers["Cookie"] = "JWT-APP={}".format(jwt_token)

        # The gateway redirects to <service_domain>/<panel_name><path>.
        # Strip /<panel_name><path> from the final URL to recover the service base URL.
        panel_path = "/" + route_key + path
        idx = resp.url.rfind(panel_path)
        if idx == -1:
            session.close()
            raise exceptions.PlatformException(resp)


        base_url = resp.url[:idx]

        self._endpoint_url = base_url
        self._endpoint_session = session
        self._cached_route_key = route_key
        logger.debug("App endpoint resolved: %s", base_url)

    def get_endpoint(self, path: str, route_name: str = None) -> str:
        """
        Resolve the app's service endpoint by following the gateway redirect.

        ``path`` is any valid path on the service (e.g. ``'/v1/models'``).
        It is appended to the route base to trigger the gateway redirect, then
        stripped from the final URL to recover the real service base URL.
        The result is cached and reused until the JWT-APP cookie expires or the
        requested route changes.

        :param str path: a path on the service used to trigger the redirect
        :param str route_name: route key in ``self.routes``. Required when the
            app has multiple routes; uses the only route when there is one.
        :return: the resolved base URL of the app service
        :rtype: str

        **Example**

        .. code-block:: python

            app = dl.apps.get(app_id='app_id')
            base_url = app.get_endpoint(path='/v1/models')
        """
        route_key, route = self._get_route(route_name)
        needs_resolve = (self._is_app_jwt_expired()
                         or self._cached_route_key != route_key)
        if needs_resolve:
            self._resolve_endpoint(path=path, route_key=route_key, route=route)
        return self._endpoint_url

    def reset_endpoint(self):
        """
        Clear the cached endpoint URL and close the session.

        Use after service redeployments, ``app.pause()`` / ``app.resume()`` cycles,
        or connection errors to force a fresh resolve on the next call.

        **Example**

        .. code-block:: python

            app.reset_endpoint()
            response = app.request(method='GET', path='/v1/models')
        """
        if self._endpoint_session is not None:
            self._endpoint_session.close()
        self._endpoint_url = None
        self._endpoint_session = None
        self._cached_route_key = None

    @property
    def endpoint_cookie_header(self) -> str:
        """
        The ``JWT-APP`` cookie as a header string for use with external HTTP clients.

        Call :meth:`get_endpoint` or :meth:`request` first to establish the session.

        :return: cookie header value, e.g. ``"JWT-APP=eyJ..."``
        :rtype: str

        **Example**

        .. code-block:: python

            app = dl.apps.get(app_id='app_id')
            base_url = app.get_endpoint(path='/v1/models')
            cookie = app.endpoint_cookie_header
        """
        if self._endpoint_session is None:
            raise exceptions.PlatformException(
                error='400',
                message='No endpoint session. Call get_endpoint() or request() first.')
        cookie_header = self._endpoint_session.headers.get("Cookie")
        if not cookie_header:
            raise exceptions.PlatformException(
                error='401',
                message='JWT-APP cookie not found in session.')
        return cookie_header

    def request(self, method: str, path: str, json: dict = None,
                data=None, headers: dict = None, stream: bool = False,
                route_name: str = None,
                raise_for_status: bool = True) -> requests.Response:
        """
        Send an HTTP request to the app's service endpoint.

        Resolves the endpoint automatically on first call using ``path`` to
        trigger the gateway redirect. Refreshes the JWT-APP cookie transparently
        when it expires.

        :param str method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        :param str path: path appended to the base URL (e.g. ``'/v1/chat/completions'``)
        :param dict json: JSON body
        :param data: raw body data
        :param dict headers: extra headers
        :param bool stream: if True, the response body is streamed
        :param str route_name: route key in ``self.routes``. Required when the
            app has multiple routes.
        :param bool raise_for_status: if True (default), raise
            :class:`~dtlpy.exceptions.PlatformException` on non-2xx responses
        :return: the HTTP response
        :rtype: requests.Response

        **Example**

        .. code-block:: python

            app = dl.apps.get(app_id='app_id')
            response = app.request(
                method='POST',
                path='/v1/chat/completions',
                json={'model': 'my-model', 'messages': [{'role': 'user', 'content': 'Hello'}]}
            )
        """
        self.get_endpoint(path=path, route_name=route_name)
        resp = self._endpoint_session.request(
            method=method,
            url=self._endpoint_url + path,
            json=json,
            data=data,
            headers=headers,
            verify=self._client_api.verify,
            stream=stream
        )
        if raise_for_status and not resp.ok:
            raise exceptions.PlatformException(resp)
        return resp

    @staticmethod
    def _protected_from_json(_json, client_api, project=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json:  platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            app = App.from_json(_json=_json,
                                client_api=client_api,
                                project=project,
                                is_fetched=is_fetched)
            status = True
        except Exception:
            app = traceback.format_exc()
            status = False
        return status, app

    def to_json(self):
        _json = {}
        if self.id is not None:
            _json['id'] = self.id
        if self.name is not None:
            _json['name'] = self.name
        if self.url is not None:
            _json['url'] = self.url
        if self.created_at is not None:
            _json['createdAt'] = self.created_at
        if self.updated_at is not None:
            _json['updatedAt'] = self.updated_at
        if self.creator is not None:
            _json['creator'] = self.creator
        if self.project_id is not None:
            _json['projectId'] = self.project_id
        if self.org_id is not None:
            _json['orgId'] = self.org_id
        if self.dpk_name is not None:
            _json['dpkName'] = self.dpk_name
        if self.dpk_version is not None:
            _json['dpkVersion'] = self.dpk_version
        if self.composition_id is not None:
            _json['compositionId'] = self.composition_id
        if self.scope is not None:
            _json['scope'] = self.scope
        if self.routes != {}:
            _json['routes'] = self.routes
        if self.custom_installation != {}:
            _json['customInstallation'] = self.custom_installation
        if self.metadata is not None:
            _json['metadata'] = self.metadata
        if self.status is not None:
            _json['status'] = self.status
        if self.settings != {}:
            _json['settings'] = self.settings
        if self.integrations is not None:
            _json['integrations'] = self.integrations
        if self.dpk is not None:
            _json['dpk'] = self.dpk.to_json()

        return _json

    @classmethod
    def from_json(cls, _json, client_api: ApiClient, project: entities.Project=None, is_fetched=True):
        # Initialize project with minimal JSON if not provided but projectId exists
        if project is None:
            project_id = _json.get('projectId', None)
            if project_id:
                project = entities.Project.from_json(
                    _json={'id': project_id},
                    client_api=client_api,
                    is_fetched=False  # Not fully fetched yet, will lazy fetch when needed
                )

        app = cls(
            id=_json.get('id', None),
            name=_json.get('name', None),
            url=_json.get('url', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            creator=_json.get('creator', None),
            project_id=_json.get('projectId', None),
            org_id=_json.get('orgId', None),
            dpk_name=_json.get('dpkName', None),
            dpk_version=_json.get('dpkVersion', None),
            composition_id=_json.get('compositionId', None),
            scope=_json.get('scope', None),
            routes=_json.get('routes', {}),
            custom_installation=_json.get('customInstallation', {}),
            client_api=client_api,
            project=project,
            metadata=_json.get('metadata', None),
            status=_json.get('status', None),
            settings=_json.get('settings', {}),
            integrations=_json.get('integrations', None),
            dpk=entities.Dpk.from_json(_json=_json.get('dpk', {}), client_api=client_api, project=project, is_fetched=is_fetched)
        )
        app.is_fetched = is_fetched
        return app
