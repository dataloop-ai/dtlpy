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
            task: entities.Task = None
    ):
        self._client_api = client_api
        self._org = org
        self._project = project
        self._dataset = dataset
        self._task = task

    ###########
    # methods #
    ###########

    @staticmethod
    def get_constructor(res: dict):
        if res['settingType'] == entities.SettingsTypes.USER_SETTINGS:
            constructor = entities.UserSetting.from_json
        else:
            constructor = entities.FeatureFlag.from_json

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

    def create(self, setting: Union[entities.FeatureFlag, entities.UserSetting]) -> Union[
        entities.FeatureFlag, entities.UserSetting
    ]:
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

        return constructor(
            _json=_json,
            client_api=self._client_api,
            project=self._project,
            org=self._org
        )

    def update(self, setting: entities.BaseSetting) -> Union[
        entities.FeatureFlag, entities.UserSetting
    ]:
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

        return constructor(
            _json=_json,
            client_api=self._client_api,
            project=self._project,
            org=self._org
        )

    def delete(self, setting_id: str) -> bool:
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

    def get(self, setting_id: str) -> Union[entities.FeatureFlag, entities.UserSetting]:
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
            req_type='get',
            path='{}/query'.format(BASE_URL),
            json_req=filters.prepare()
        )
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters) -> entities.PagedEntities:
        if filters.resource != entities.FiltersResource.SETTINGS:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.PACKAGE. Got: {!r}'.format(filters.resource))

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
