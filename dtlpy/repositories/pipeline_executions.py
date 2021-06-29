import logging
from .. import entities, repositories, exceptions, miscellaneous, services

logger = logging.getLogger(name=__name__)


class PipelineExecutions:
    """
    PipelineExecutions Repository
    """

    def __init__(
            self,
            client_api: services.ApiClient,
            project: entities.Project = None,
            pipeline: entities.Pipeline = None
    ):
        self._client_api = client_api
        self._project = project
        self._pipeline = pipeline

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

    @property
    def pipeline(self) -> entities.Pipeline:
        assert isinstance(self._pipeline, entities.Pipeline)
        return self._pipeline

    @pipeline.setter
    def pipeline(self, pipeline: entities.Pipeline):
        if not isinstance(pipeline, entities.Pipeline):
            raise ValueError('Must input a valid pipeline entity')
        self._pipeline = pipeline

    ###########
    # methods #
    ###########
    def get(self, pipeline_execution_id: str, pipeline_id: str = None) -> entities.Pipeline:
        """
        Get Pipeline Execution object

        :param pipeline_execution_id: str
        :param pipeline_id: str
        :return: Pipeline object
        """

        if pipeline_id is None and self._pipeline is None:
            raise exceptions.PlatformException('400', 'Must provide param pipeline_id')
        elif pipeline_id is None:
            pipeline_id = self.pipeline.id

        success, response = self._client_api.gen_request(
            req_type="get",
            path="/pipelines/{pipeline_id}/executions/{pipeline_execution_id}".format(
                pipeline_id=pipeline_id,
                pipeline_execution_id=pipeline_execution_id
            )
        )
        if not success:
            raise exceptions.PlatformException(response)

        pipeline = entities.PipelineExecution.from_json(
            client_api=self._client_api,
            _json=response.json(),
            pipeline=self._pipeline
        )

        return pipeline

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.PipelineExecution]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]

        for i_pipeline_execution, pipeline_execution in enumerate(response_items):
            jobs[i_pipeline_execution] = pool.submit(
                entities.PipelineExecution._protected_from_json,
                **{
                    'client_api': self._client_api,
                    '_json': pipeline_execution,
                    'pipeline': self._pipeline
                }
            )

        # get all results
        # noinspection PyUnresolvedReferences
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        pipeline_executions = miscellaneous.List([r[1] for r in results if r[0] is True])
        return pipeline_executions

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

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project pipeline executions
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.PIPELINE_EXECUTION)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.PIPELINE_EXECUTION:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.PIPELINE_EXECUTION. Got: {!r}'.format(filters.resource))

        project_id = None
        if self._project is not None:
            project_id = self._project.id

        if self._project is not None:
            filters.add(field='projectId', values=self.project.id)

        if self._pipeline is not None:
            filters.add(field='pipelineId', values=self.pipeline.id)

        paged = entities.PagedEntities(
            items_repository=self,
            filters=filters,
            page_offset=filters.page,
            page_size=filters.page_size,
            project_id=project_id,
            client_api=self._client_api
        )

        paged.get_page()
        return paged
