import logging
from typing import Union

from .. import exceptions, entities, ApiClient

logger = logging.getLogger(name='dtlpy')
BASE_URL = '/settings'


class Settings:
    def __init__(
            self,
            client_api: ApiClient,
            project: entities.Project = None,
            dataset: entities.Dataset = None,
            org: entities.Organization = None,
            task: entities.Task = None,
            resource=None,
            resource_type=None
    ):
        self._client_api = client_api
        self._org = org
        self._project = project
        self._dataset = dataset
        self._task = task
        self._resource = resource
        self._resource_type = resource_type

    ###########
    # methods #
    ###########

    @staticmethod
    def get_constructor(res: dict):
        constructor = entities.Setting.from_json
        return constructor

    def _build_entities_from_response(self, response_items):
        settings = list()
        for _, setting in enumerate(response_items):
            settings.append(
                self.get_constructor(setting)(
                    client_api=self._client_api,
                    _json=setting,
                    project=self._project
                )
            )

        return settings

    def _build_settings(self,
                        setting_name: str = None,
                        setting_value: entities.SettingsTypes = None,
                        setting_value_type: entities.SettingsValueTypes = None,
                        setting_default_value=None
                        ):
        if self._resource is None:
            raise exceptions.PlatformException('400', 'Must have resource')
        setting = entities.Setting(
            name=setting_name,
            value=setting_value,
            value_type=setting_value_type,
            section_name=entities.SettingsSectionNames.SDK,
            default_value=setting_default_value,
            scope=entities.SettingScope(type=self._resource_type,
                                        id=self._resource.id,
                                        role=entities.Role.ALL,
                                        prevent_override=False,
                                        visible=True),
        )
        return setting

    def create(self,
               setting: entities.Setting = None,
               setting_name: str = None,
               setting_value=None,
               setting_value_type: entities.SettingsValueTypes = None,
               setting_default_value=None,
               ) -> entities.Setting:
        """
        Create a new setting

        :param Setting setting: setting entity
        :param str setting_name: the setting name
        :param setting_value: the setting value
        :param SettingsValueTypes setting_value_type: the setting type dl.SettingsValueTypes
        :param setting_default_value: the setting default value
        :return: setting entity
        """
        if sum([1 for param in [setting_name, setting_value, setting_value_type] if param is None]) > 0 \
                and setting is None:
            raise exceptions.PlatformException('400', 'Must provide setting object or'
                                                      'setting_name, setting_value and setting_value_type')

        if setting is None:
            setting = self._build_settings(setting_name=setting_name,
                                           setting_value=setting_value,
                                           setting_value_type=setting_value_type,
                                           setting_default_value=setting_default_value)

        success, response = self._client_api.gen_request(
            req_type='post',
            path='{}'.format(
                BASE_URL
            ),
            json_req=setting.to_json()
        )

        if success:
            _json = response.json()
            constructor = self.get_constructor(_json)
        else:
            raise exceptions.PlatformException(response)

        # add settings to cookies
        self._client_api.platform_settings.add(setting.name,
                                               {
                                                   setting.scope.id: setting.value
                                               }
                                               )
        return constructor(
            _json=_json,
            client_api=self._client_api,
            project=self._project,
            org=self._org
        )

    def update(self,
               setting: entities.BaseSetting = None,
               setting_id: str = None,
               setting_name: str = None,
               setting_value=None,
               setting_default_value=None,
               ) -> entities.Setting:
        """
        Update a setting

        :param Setting setting: setting entity
        :param str setting_id: the setting id
        :param str setting_name: the setting name
        :param setting_value: the setting value
        :param setting_default_value: the setting default value
        :return: setting entity
        """
        if sum([1 for param in [setting_name, setting_value] if param is None]) > 0 \
                and setting is None:
            raise exceptions.PlatformException('400', 'Must provide setting object or'
                                                      'setting_name, setting_value and setting_value_type')

        if setting is None:
            setting = self.get(setting_id=setting_id)
            setting.name = setting_name
            setting.value = setting_value
            if setting_default_value is not None:
                setting.default_value = setting_default_value

        patch = setting.to_json()
        patch.pop('id')
        patch.pop('name')
        success, response = self._client_api.gen_request(
            req_type='patch',
            path='{}/{}'.format(
                BASE_URL,
                setting.id
            ),
            json_req=patch
        )

        if success:
            _json = response.json()
            constructor = self.get_constructor(_json)
        else:
            raise exceptions.PlatformException(response)

        # add settings to cookies
        self._client_api.platform_settings.add(setting.name,
                                               {
                                                   setting.scope.id: setting.value
                                               }
                                               )

        return constructor(
            _json=_json,
            client_api=self._client_api,
            project=self._project,
            org=self._org
        )

    def delete(self, setting_id: str) -> bool:
        """
        Delete a setting

        :param str setting_id: the setting id
        :return: True if success exceptions if not
        """
        success, response = self._client_api.gen_request(
            req_type='delete',
            path='{}/{}'.format(
                BASE_URL,
                setting_id
            )
        )

        if success:
            return True
        else:
            raise exceptions.PlatformException(response)

    def get(self, setting_name: str = None, setting_id: str = None) -> entities.Setting:
        """
        Get a setting by id

        :param str setting_name: the setting name
        :param str setting_id: the setting id
        :return: setting entity
        """
        success, response = self._client_api.gen_request(
            req_type='get',
            path='{}/{}'.format(
                BASE_URL,
                setting_id
            )
        )

        if success:
            _json = response.json()
            constructor = self.get_constructor(_json)
        else:
            raise exceptions.PlatformException(response)

        return constructor(
            _json=_json,
            client_api=self._client_api,
            project=self._project,
            org=self._org
        )

    def _list(self, filters: entities.Filters):
        success, response = self._client_api.gen_request(
            req_type='post',
            path='{}/query'.format(BASE_URL),
            json_req=filters.prepare()
        )
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List settings

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.SETTINGS)
            filters.sort_by(entities.FiltersOrderByDirection.ASCENDING)

        if filters.resource != entities.FiltersResource.SETTINGS:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.SETTINGS . Got: {!r}'.format(filters.resource))

        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)

        paged = entities.PagedEntities(
            items_repository=self,
            filters=filters,
            page_offset=filters.page,
            page_size=filters.page_size,
            project_id=self._project.id if self._project is not None else None,
            client_api=self._client_api
        )

        paged.get_page()

        return paged

    def resolve(
            self,
            user_email: str,
            org_id: str = None,
            project_id: str = None,
            dataset_id: str = None,
            task_id: str = None,
    ):
        """
        return all the settings that relevant to the provider params

        :param str user_email: user email
        :param str org_id: org id
        :param str project_id: project id
        :param str dataset_id: dataset id
        :param str task_id: task id
        """
        payload = {
            'userId': user_email
        }

        if self._project:
            payload['projectId'] = self._project.id
        elif project_id:
            payload['projectId'] = project_id

        if self._org:
            payload['orgId'] = self._org.id
        elif org_id:
            payload['orgId'] = org_id

        if self._dataset:
            payload['datasetId'] = self._dataset.id
        elif dataset_id:
            payload['datasetId'] = dataset_id

        if self._task:
            payload['taskId'] = self._task.id
        elif task_id:
            payload['taskId'] = task_id

        success, response = self._client_api.gen_request(
            req_type='post',
            path='{}/resolve'.format(BASE_URL),
            json_req=payload
        )

        if success:
            _json = response.json()
            return self._build_entities_from_response(response_items=_json)
        else:
            raise exceptions.PlatformException(response)
