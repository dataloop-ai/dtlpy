import logging

from .. import exceptions, entities, miscellaneous
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class ResourceExecutions:
    """
    Resource Executions Repository

    The ResourceExecutions class allows the users to manage executions (executions of Resource) and their properties.
    """

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 resource=None):
        self._client_api = client_api
        self._project = project
        self._resource = resource

    ############
    # entities #
    ############
    @property
    def resource(self):
        if self._resource is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "resource". need to set a entity or use resource.executions repository')
        assert hasattr(entities, self._resource.__class__.__name__)
        return self._resource

    @resource.setter
    def resource(self, resource):
        if not hasattr(entities, self._resource.__class__.__name__):
            raise ValueError('Must input a valid entity')
        self._resource = resource

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use Project.executions repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def _list(self, filters: entities.Filters):
        """
        List resource executions

        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return:
        """
        url = "/executions/resource/query"

        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List resource executions

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            item.resource_executions.list()
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.RESOURCE_EXECUTION)
            if self._resource is not None:
                filters.add(field='resourceType', values=self._resource.__class__.__name__)
                filters.add(field='resourceId', values=self._resource.id)
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='Must have resource')
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(
                error='400',
                message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.RESOURCE_EXECUTION:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.RESOURCE_EXECUTION. '
                        'Got: {!r}'.format(filters.resource))
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Execution]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return execution list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.ResourceExecution._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item,
                                          'project': self._project,
                                          'resource': self._resource})

        # get results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])
