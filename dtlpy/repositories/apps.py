import logging

from .. import entities, exceptions, miscellaneous
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Apps:

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.apps repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def get(self,
            app_name: str = None,
            app_id: str = None,
            fetch: bool = None) -> entities.App:
        """
        Get an app object.

        note: It's required to pass either app_id of app_name

        :param str app_id: optional - search by id.
        :param str app_name: optional - search by name.
        :param bool fetch: optional - fetch entity from platform, default taken from cookie

        **Example**:

        .. code-block:: python
            app = self.apps.get(app_id='app_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if app_id is None and app_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='You must provide an identifier in inputs')
        if fetch:
            if app_name is not None:
                app = self.__get_by_name(name=app_name)
            else:
                success, response = self._client_api.gen_request(req_type='get', path="/apps/{}".format(app_id))
                if not success:
                    raise exceptions.PlatformException(response)
                app = entities.App.from_json(client_api=self._client_api,
                                             _json=response.json(),
                                             project=self._project)
        else:
            app = entities.App.from_json(
                _json={
                    'id': app_id,
                    'name': app_name
                },
                client_api=self._client_api,
                project=self._project,
                is_fetched=False
            )
        assert isinstance(app, entities.App)
        return app

    def __get_by_name(self, name) -> entities.App:
        filters = entities.Filters(field='name',
                                   values=name,
                                   resource=entities.FiltersResource.APP,
                                   use_defaults=False)
        if self._project is not None:
            filters.add(field='projectId', values=self.project.id)
        apps = self.list(filters=filters)
        if apps.items_count == 0:
            raise exceptions.PlatformException(
                error='404',
                message='app not found. Name: {}'.format(name))
        elif apps.items_count > 1:
            raise exceptions.PlatformException(
                error='400',
                message='More than one app found by the name of: {} '.format(apps))
        return apps.items[0]

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.App]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.App._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item,
                                          'project': self._project})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items

    def _list(self, filters: entities.Filters):
        url = '/apps/query'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None, project_id: str = None) -> entities.PagedEntities:
        """
        List the available apps in the specified project.

        :param entities.Filters filters: the filters to apply to the list
        :param str project_id: the project id to apply thew filters on.
        :return a paged entity representing the list of apps.

        ** Example **
        .. code-block:: python
            apps = dl.apps.list(project_id='id')
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.APP)
            # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.APP:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.APP. Got: {!r}'.format(filters.resource))

        # noinspection DuplicatedCode
        if project_id is None and self._project is not None:
            project_id = self._project.id

        if project_id is not None:
            filters.add(field='projectId', values=project_id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       project_id=project_id,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def update(self, app: entities.App = None, app_id: str = None) -> bool:
        """
        Update the current app to the new configuration

        :param entities.App app: The app to update.
        :param str app_id: The app id to update.
        :return bool whether the operation ran successfully or not

        **Example**
        .. code-block:: python
            succeed = dl.apps.update(app)
        """
        if app_id is not None and app is None:
            app = self.get(app_id=app_id)
        if app is None:
            raise exceptions.PlatformException(error='400', message='You must provide app or app_id')
        success, response = self._client_api.gen_request(req_type='put',
                                                         path=f"/apps/{app.id}",
                                                         json_req=app.to_json())
        if success:
            return success
        raise exceptions.PlatformException(response)

    def install(self,
                dpk: entities.Dpk,
                app_name: str = None,
                organization_id: str = None,
                custom_installation: dict = None,
                scope: entities.AppScope = None
                ) -> entities.App:
        """
        Install the specified app in the project.

        Note: You must pass either the app_id or app_name
        :param entities.App dpk: the app entity
        :param str app_name: installed app name. default is the dpk name
        :param str organization_id: the organization which you want to apply on the filter.
        :param dict custom_installation: partial installation.
        :param str scope: the scope of the app. default is project.

        :return the installed app.
        :rtype entities.App

        **Example**
        .. code-block:: python
            app = dl.apps.install(dpk=dpk)
        """
        if dpk is None:
            raise exceptions.PlatformException(error='400', message='You must provide an app')

        if app_name is None:
            app_name = dpk.display_name
        if isinstance(scope, entities.AppScope):
            scope = scope.value
        app = entities.App.from_json(_json={'name': app_name,
                                            'projectId': self.project.id,
                                            'orgId': organization_id,
                                            'dpkName': dpk.name,
                                            "customInstallation": custom_installation,
                                            'dpkVersion': dpk.version,
                                            'scope': scope
                                            },
                                     client_api=self._client_api,
                                     project=self.project)
        success, response = self._client_api.gen_request(req_type='post',
                                                         path="/apps",
                                                         json_req=app.to_json())
        if not success:
            raise exceptions.PlatformException(response)
        return entities.App.from_json(_json=response.json(),
                                      client_api=self._client_api,
                                      project=self.project)

    def uninstall(self, app_id: str = None, app_name: str = None) -> bool:
        """
        Delete an app entity.

        Note: You are required to add either app_id or app_name.

        :param str app_id: optional - the id of the app.
        :param str app_name: optional - the name of the app.
        :return whether we succeed uninstalling the specified app.
        :rtype bool

        **Example**
        .. code-block:: python
            # succeed = dl.apps.delete(app_id='app_id')
        """
        if app_id is None and app_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='You must provide an identifier in inputs')
        if app_name is not None:
            app = self.__get_by_name(app_name)
            app_id = app.id

        success, response = self._client_api.gen_request(req_type='delete', path='/apps/{}'.format(app_id))
        if not success:
            raise exceptions.PlatformException(response)

        logger.debug(f"App deleted successfully (id: {app_id}, name: {app_name}")
        return success

    def resume(self, app: entities.App = None, app_id: str = None) -> bool:
        """
        Activate an app entity.

        Note: You are required to add either app or app_id.

        :param entities.App app: the app entity
        :param str app_id: optional - the id of the app.
        :return whether we succeed activating the specified app.
        :rtype bool

        **Example**
        .. code-block:: python
            # succeed = dl.apps.resume(app)
        """
        if app_id is not None and app is None:
            app = self.get(app_id=app_id)
        if app is None:
            raise exceptions.PlatformException(error='400', message='You must provide app or app_id')

        if app and app.status == entities.CompositionStatus.INSTALLED:
            raise exceptions.PlatformException(
                error='400',
                message='Application is already active'
            )

        success, response = self._client_api.gen_request(req_type='post', path='/apps/{}/activate'.format(app.id))
        if not success:
            raise exceptions.PlatformException(response)

        logger.debug(f"App resumed successfully (id: {app.id}, name: {app.name}")
        return success

    def pause(self, app: entities.App = None, app_id: str = None) -> bool:
        """
        Pausing an app entity.

        Note: You are required to add either app or app_id.

        :param entities.App app: the app entity
        :param str app_id: optional - the id of the app.
        :return whether we succeed pausing the specified app.
        :rtype bool

        **Example**
        .. code-block:: python
            # succeed = dl.apps.pause(app)
        """
        if app_id is not None and app is None:
            app = self.get(app_id=app_id)
        if app is None:
            raise exceptions.PlatformException(error='400', message='You must provide app or app_id')

        if app and app.status == entities.CompositionStatus.UNINSTALLED:
            raise exceptions.PlatformException(
                error='400',
                message='Application is already inactive'
            )

        success, response = self._client_api.gen_request(req_type='post', path='/apps/{}/deactivate'.format(app.id))
        if not success:
            raise exceptions.PlatformException(response)

        logger.debug(f"App paused successfully (id: {app.id}, name: {app.name}")
        return success
