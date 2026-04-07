import logging
from .. import entities, repositories, exceptions, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Compositions:
    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        if project is None:
            project = entities.Project(_dict={}, _client_api=client_api)
        self.project = project

    def get(self,
            composition_id=None,
            fetch=None
            ) -> entities.Pipeline:

        if fetch is None:
            fetch = self._client_api.fetch_entities

        if composition_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        elif fetch:
            if composition_id is not None:
                success, response = self._client_api.gen_request(
                    req_type="get",
                    path="/compositions/{}".format(composition_id))
                if self._client_api.check_response(success, response, path="/compositions") is False:
                    return None
                composition = response.json()
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out pipeline was found, must checkout or provide an identifier in inputs')
        else:
            composition = {'id': composition_id}

        return composition
