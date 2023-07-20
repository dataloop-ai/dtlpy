import logging
from .. import entities, repositories, exceptions, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Compositions:
    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self._client_api).get()
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "project". need to set a Project entity or use project.pipelines repository')
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

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
                if not success:
                    raise exceptions.PlatformException(response)
                composition = response.json()
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out pipeline was found, must checkout or provide an identifier in inputs')
        else:
            composition = {'id': composition_id}

        return composition
