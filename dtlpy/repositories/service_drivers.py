from dtlpy import miscellaneous

from ..services.api_client import ApiClient
from .. import exceptions, entities
import logging

logger = logging.getLogger(name='dtlpy')

class ServiceDrivers:

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api
        self._base_url = '/serviceDrivers'

    def create(
            self,
            name: str,
            compute_id: str,
            context: entities.ComputeContext,
            namespace: str = None
    ):
        """
        Create a new service driver

        :param name: Service driver name
        :param compute_id: Compute ID
        :param context: Compute context
        :param namespace: Namespace
        :return: Service driver

        """

        payload = {
            'name': name,
            'computeId': compute_id,
            'context': context.to_json()
        }
        if namespace is not None:
            payload['namespace'] = namespace

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=self._base_url,
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        service_driver = entities.ServiceDriver.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return service_driver

    def get(self, service_driver_id: str):
        """
        Get a service driver

        :param service_driver_id: Service driver ID
        :return: Service driver
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='get',
            path=self._base_url + '/{}'.format(service_driver_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        service_driver = entities.ServiceDriver.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return service_driver

    def delete(self, service_driver_id: str):
        """
        Delete a service driver

        :param service_driver_id: Service driver ID
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='delete',
            path=self._base_url + '/{}'.format(service_driver_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        return True

    def set_default(self, service_driver_id: str, org_id: str, update_existing_services=False):
        """
        Set a service driver as default

        :param service_driver_id: Compute name
        :param org_id: Organization ID
        :param update_existing_services: Update existing services

        :return: Service driver
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=self._base_url + '/default',
            json_req={
                'organizationId': org_id,
                'updateExistingServices': update_existing_services,
                'driverName': service_driver_id
            }
        )

        if not success:
            raise exceptions.PlatformException(response)

        service_driver = entities.ServiceDriver.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return service_driver

    def update(self, service_driver: entities.ServiceDriver):
        """
        Update a service driver

        :param dtlpy.entities.service_driver.ServiceDriver service_driver: updated service driver object
        :return: Service driver entity
        :rtype: dtlpy.entities.service_driver.ServiceDriver
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path=self._base_url + '/{}'.format(service_driver.id),
            json_req=service_driver.to_json()
        )

        if not success:
            raise exceptions.PlatformException(response)

        service_driver = entities.ServiceDriver.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return service_driver

    def _list(self, filters: entities.Filters):
        url = self._base_url + '/query'
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.ServiceDriver]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.ServiceDriver._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item})
        results = [j.result() for j in jobs]
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List all services drivers

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            services = dl.service_drivers.list()
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.SERVICE_DRIVER)

        if filters.resource != entities.FiltersResource.SERVICE_DRIVER:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.SERVICE_DRIVER. Got: {!r}'.format(
                    filters.resource))

        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged
