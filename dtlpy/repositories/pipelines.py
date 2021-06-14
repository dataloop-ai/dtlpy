import logging
from .. import entities, repositories, exceptions, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Pipelines:
    """
    Pipelines Repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
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

    ###########
    # methods #
    ###########
    def open_in_web(self, pipeline=None, pipeline_id=None, pipeline_name=None):
        if pipeline is None:
            pipeline = self.get(pipeline_name=pipeline_name, pipeline_id=pipeline_id)
        self._client_api._open_in_web(resource_type='pipeline', project_id=pipeline.project_id, pipeline_id=pipeline.id)

    def get(self, pipeline_name=None, pipeline_id=None, fetch=None) -> entities.Pipeline:
        """
        Get Pipeline object

        :param pipeline_name: str
        :param pipeline_id: str
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Pipeline object
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if pipeline_name is None and pipeline_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')
        elif fetch:
            if pipeline_id is not None:
                success, response = self._client_api.gen_request(
                    req_type="get",
                    path="/pipelines/{}".format(pipeline_id))
                if not success:
                    raise exceptions.PlatformException(response)
                pipeline = entities.Pipeline.from_json(
                    client_api=self._client_api,
                    _json=response.json(),
                    project=self._project
                )
                if pipeline_name is not None and pipeline.name != pipeline_name:
                    logger.warning(
                        "Mismatch found in pipeline.get: pipeline_name is different then pipeline.name:"
                        " {!r} != {!r}".format(
                            pipeline_name,
                            pipeline.name
                        )
                    )
            elif pipeline_name is not None:
                filters = entities.Filters(
                    field='name',
                    values=pipeline_name,
                    resource=entities.FiltersResource.PIPELINE,
                    use_defaults=False
                )
                if self._project is not None:
                    filters.add(field='projectId', values=self._project.id)
                pipelines = self.list(filters=filters)
                if pipelines.items_count == 0:
                    raise exceptions.PlatformException(
                        error='404',
                        message='Pipeline not found. Name: {}'.format(pipeline_name))
                elif pipelines.items_count > 1:
                    raise exceptions.PlatformException(
                        error='400',
                        message='More than one pipelines found by the name of: {} '
                                'Please get pipeline from a project entity'.format(pipeline_name))
                pipeline = pipelines.items[0]
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out pipeline was found, must checkout or provide an identifier in inputs')
        else:
            pipeline = entities.Pipeline.from_json(
                _json={'id': pipeline_id,
                       'name': pipeline_name},
                client_api=self._client_api,
                project=self._project,
                is_fetched=False
            )

        return pipeline

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Pipeline]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]

        for i_pipeline, pipeline in enumerate(response_items):
            jobs[i_pipeline] = pool.submit(
                entities.Pipeline._protected_from_json,
                **{
                    'client_api': self._client_api,
                    '_json': pipeline,
                    'project': self._project
                }
            )

        # get all results
        # noinspection PyUnresolvedReferences
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        pipelines = miscellaneous.List([r[1] for r in results if r[0] is True])
        return pipelines

    def _list(self, filters: entities.Filters):
        url = '/pipelines/query'

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=url,
            json_req=filters.prepare()
        )
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None, project_id=None) -> entities.PagedEntities:
        """
        List project pipelines
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.PIPELINE)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

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

    def _name_validation(self, name: str):
        url = '/piper-misc/naming/packages/{}'.format(name)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

    def delete(self, pipeline: entities.Pipeline = None, pipeline_name=None, pipeline_id=None):
        """
        Delete Pipeline object

        :param pipeline:
        :param pipeline_name:
        :param pipeline_id:
        :return: True
        """
        # get id and name
        if pipeline_id is None:
            if pipeline is None:
                pipeline = self.get(pipeline_id=pipeline_id, pipeline_name=pipeline_name)
            pipeline_id = pipeline.id

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/pipelines/{}".format(pipeline_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, pipeline: entities.Pipeline = None) -> entities.Pipeline:
        """
        Update pipeline changes to platform

        :param pipeline:
        :return: pipeline entity
        """

        # payload
        payload = pipeline.to_json()

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path='/pipelines/{}'.format(pipeline.id),
            json_req=payload
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Pipeline.from_json(
            _json=response.json(),
            client_api=self._client_api,
            project=self._project
        )
