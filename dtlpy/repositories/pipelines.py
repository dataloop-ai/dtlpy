import logging
from .. import entities, repositories, exceptions, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')

BASIC_PIPELINE = {
    "name": "",
    "projectId": "",
    "nodes": [],
    "connections": []
}


class Pipelines:
    """
    Pipelines Repository

    The Pipelines class allows users to manage pipelines and their properties. See our documentation for more information on `pipelines <https://dataloop.ai/docs/pipelines-overview>`_.
    """

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

    ###########
    # methods #
    ###########
    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/pipelines".format(self.project.id))

    def open_in_web(self,
                    pipeline: entities.Pipeline = None,
                    pipeline_id: str = None,
                    pipeline_name: str = None):
        """
        Open the pipeline in web platform.

        **prerequisites**: Must be *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :param str pipeline_id: pipeline id
        :param str pipeline_name: pipeline name

        **Example**:

        .. code-block:: python

            project.pipelines.open_in_web(pipeline_id='pipeline_id')
        """
        if pipeline_name is not None:
            pipeline = self.get(pipeline_name=pipeline_name)
        if pipeline is not None:
            pipeline.open_in_web()
        elif pipeline_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(pipeline_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    @_api_reference.add(path='/pipelines/{pipelineId}', method='get')
    def get(self,
            pipeline_name=None,
            pipeline_id=None,
            fetch=None
            ) -> entities.Pipeline:
        """
        Get Pipeline object to use in your code.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: pipeline_name, pipeline_id.

        :param str pipeline_id: pipeline id
        :param str pipeline_name: pipeline name
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Pipeline object
        :rtype: dtlpy.entities.pipeline.Pipeline

        **Example**:

        .. code-block:: python

            pipeline = project.pipelines.get(pipeline_id='pipeline_id')
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

    @_api_reference.add(path='/pipelines/query', method='post')
    def list(self,
             filters: entities.Filters = None,
             project_id: str = None
             ) -> entities.PagedEntities:
        """
        List project pipelines.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param str project_id: project id
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            pipelines = project.pipelines.list()
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.PIPELINE)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.PIPELINE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.PIPELINE. Got: {!r}'.format(filters.resource))

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

    @_api_reference.add(path='/pipelines/{pipelineId}', method='delete')
    def delete(self,
               pipeline: entities.Pipeline = None,
               pipeline_name: str = None,
               pipeline_id: str = None):
        """
        Delete Pipeline object.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

       :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
       :param str pipeline_id: pipeline id
       :param str pipeline_name: pipeline name
       :return: True if success
       :rtype: bool

       **Example**:

        .. code-block:: python

            is_deleted = project.pipelines.delete(pipeline_id='pipeline_id')
       """
        # get id and name
        if pipeline_id is None:
            if pipeline is None:
                pipeline = self.get(pipeline_name=pipeline_name)
            pipeline_id = pipeline.id

        # request
        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="/pipelines/{}".format(pipeline_id))

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    @_api_reference.add(path='/pipelines/{pipelineId}/settings', method='patch')
    def update_settings(self, pipeline: entities.Pipeline, settings: entities.PipelineSettings):
        """
        Update pipeline settings.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :param dtlpy.entities.pipeline.PipelineSettings settings: settings entity
        :return: Pipeline object
        :rtype: dtlpy.entities.pipeline.Pipeline

        **Example**:

        .. code-block:: python

            pipeline = project.pipelines.update_settings(pipeline='pipeline_entity', settings=dl.PipelineSettings(keep_triggers_active=True))
        """
        # payload
        payload = {'settings': settings.to_json()}

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path='/pipelines/{}'.format(pipeline.id),
            json_req=payload
        )
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Pipeline.from_json(
            _json=response.json(),
            client_api=self._client_api,
            project=self._project
        )

    def __update_variables(self, pipeline: entities.Pipeline):
        pipeline_json = pipeline.to_json()
        variables = pipeline_json['variables']

        for var in variables:
            if var.get('reference', None) is None:
                var['reference'] = pipeline.id

        # payload
        payload = {'variables': variables}

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path='/pipelines/{}/variables'.format(pipeline.id),
            json_req=payload
        )
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Pipeline.from_json(
            _json=response.json(),
            client_api=self._client_api,
            project=self._project
        )

    @_api_reference.add(path='/pipelines/{pipelineId}', method='patch')
    def update(self,
               pipeline: entities.Pipeline = None
               ) -> entities.Pipeline:
        """
        Update pipeline changes to platform.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :return: Pipeline object
        :rtype: dtlpy.entities.pipeline.Pipeline

        **Example**:

        .. code-block:: python

            pipeline = project.pipelines.update(pipeline='pipeline_entity')
        """

        # payload
        payload = pipeline.to_json()

        # update settings
        if pipeline.settings_changed():
            self.update_settings(pipeline=pipeline, settings=pipeline.settings)

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

    @_api_reference.add(path='/pipelines', method='post')
    def create(self,
               name: str = None,
               project_id: str = None,
               pipeline_json: dict = None
               ) -> entities.Pipeline:
        """
        Create a new pipeline.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str name: pipeline name
        :param str project_id: project id
        :param dict pipeline_json: json containing the pipeline fields
        :return: Pipeline object
        :rtype: dtlpy.entities.pipeline.Pipeline

        **Example**:

        .. code-block:: python

            pipeline = project.pipelines.create(name='pipeline_name')
        """
        if pipeline_json is None:
            pipeline_json = BASIC_PIPELINE

        if name is not None:
            pipeline_json['name'] = name

        if project_id is not None:
            pipeline_json['projectId'] = project_id
        else:
            if not pipeline_json.get('projectId', None):
                pipeline_json['projectId'] = self.project.id

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/pipelines',
                                                         json_req=pipeline_json)
        if success:
            pipeline = entities.Pipeline.from_json(client_api=self._client_api,
                                                   _json=response.json(),
                                                   project=self.project)
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(pipeline, entities.Pipeline)
        return pipeline

    @_api_reference.add(path='/pipelines/{pipelineId}/install', method='post')
    def install(self, pipeline: entities.Pipeline = None, resume_option: entities.PipelineResumeOption = None):
        """
        Install (start) a pipeline.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :param dtlpy.entities.pipeline.PipelineResumeOption resume_option: optional - resume pipeline method (what to do with existing cycles)
        :return: Composition object

        **Example**:

        .. code-block:: python

            project.pipelines.install(pipeline='pipeline_entity')
        """

        payload = {}
        if resume_option:
            payload['resumeOption'] = resume_option

        success, response = self._client_api.gen_request(
            req_type='post',
            path='/pipelines/{}/install'.format(pipeline.id),
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        return entities.Pipeline.from_json(client_api=self._client_api,
                                           _json=response.json(),
                                           project=self.project)

    @_api_reference.add(path='/pipelines/{pipelineId}/uninstall', method='post')
    def pause(self, pipeline: entities.Pipeline = None, keep_triggers_active: bool = None):
        """
        Pause a pipeline.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :param bool keep_triggers_active: Do we want the triggers to stay active and collect events
        :return: Composition object

        **Example**:

        .. code-block:: python

            project.pipelines.pause(pipeline='pipeline_entity')
        """

        payload = {}
        if keep_triggers_active is not None:
            payload['keepTriggersActive'] = keep_triggers_active

        success, response = self._client_api.gen_request(
            req_type='post',
            path='/pipelines/{}/uninstall'.format(pipeline.id),
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/pipelines/{pipelineId}/reset', method='post')
    def reset(self,
              pipeline: entities.Pipeline = None,
              pipeline_id: str = None,
              pipeline_name: str = None,
              stop_if_running: bool = False):
        """
        Reset pipeline counters.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity - optional
        :param str pipeline_id: pipeline_id -  optional
        :param str pipeline_name: pipeline_name -  optional
        :param bool stop_if_running: If the pipeline is installed it will stop the pipeline and reset the counters.
        :return: bool

        **Example**:

        .. code-block:: python

            success = project.pipelines.reset(pipeline='pipeline_entity')
        """

        if pipeline_id is None:
            if pipeline is None:
                if pipeline_name is not None:
                    pipeline = self.get(pipeline_name=pipeline_name)
                else:
                    raise exceptions.PlatformException(
                        '400',
                        'Must provide one of pipeline, pipeline_id or pipeline_name'
                    )
            pipeline_id = pipeline.id

        if stop_if_running is True:
            if pipeline is None:
                pipeline = self.get(pipeline_id=pipeline_id)
            pipeline.pause()

        success, response = self._client_api.gen_request(
            req_type='post',
            path='/pipelines/{}/reset'.format(pipeline_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        return True

    @_api_reference.add(path='/pipelines/{id}/statistics', method='get')
    def stats(self, pipeline: entities.Pipeline = None, pipeline_id: str = None, pipeline_name: str = None):
        """
        Get pipeline counters.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity - optional
        :param str pipeline_id: pipeline_id -  optional
        :param str pipeline_name: pipeline_name -  optional
        :return: PipelineStats
        :rtype: dtlpy.entities.pipeline.PipelineStats

        **Example**:

        .. code-block:: python

            pipeline_stats = project.pipelines.stats(pipeline='pipeline_entity')
        """

        if pipeline_id is None:
            if pipeline is None:
                if pipeline_name is not None:
                    pipeline = self.get(pipeline_name=pipeline_name)
                else:
                    raise exceptions.PlatformException(
                        '400',
                        'Must provide one of pipeline, pipeline_id or pipeline_name'
                    )
            pipeline_id = pipeline.id

        success, response = self._client_api.gen_request(
            req_type='get',
            path='/pipelines/{}/statistics'.format(pipeline_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        return entities.PipelineStats.from_json(_json=response.json())

    def execute(self,
                pipeline: entities.Pipeline = None,
                pipeline_id: str = None,
                pipeline_name: str = None,
                execution_input=None):
        """
        Execute a pipeline and return the pipeline execution as an object.

        **prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.pipeline.Pipeline pipeline: pipeline entity
        :param str pipeline_id: pipeline id
        :param str pipeline_name: pipeline name
        :param execution_input: list of the dl.FunctionIO or dict of pipeline input - example {'item': 'item_id'}
        :return: entities.PipelineExecution object
        :rtype: dtlpy.entities.pipeline_execution.PipelineExecution

        **Example**:

        .. code-block:: python

            pipeline_execution= project.pipelines.execute(pipeline='pipeline_entity', execution_input= {'item': 'item_id'} )
        """
        if pipeline is None:
            pipeline = self.get(pipeline_id=pipeline_id, pipeline_name=pipeline_name)
        execution = repositories.PipelineExecutions(pipeline=pipeline,
                                                    client_api=self._client_api,
                                                    project=self._project).create(pipeline_id=pipeline.id,
                                                                                  execution_input=execution_input)
        return execution
