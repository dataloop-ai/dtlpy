from ..services.api_client import ApiClient
from .. import exceptions, entities, repositories
from typing import List, Optional, Dict


class Computes:

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api
        self._base_url = '/compute'
        self._commands = None

    @property
    def commands(self) -> repositories.Commands:
        if self._commands is None:
            self._commands = repositories.Commands(client_api=self._client_api)
        return self._commands

    def create(
            self,
            name: str,
            context: entities.ComputeContext,
            shared_contexts: Optional[List[entities.ComputeContext]],
            cluster: entities.ComputeCluster,
            type: entities.ComputeType = entities.ComputeType.KUBERNETES,
            is_global: Optional[bool] = False,
            features: Optional[Dict] = None,
            wait=True
    ):
        """
        Create a new compute

        :param name: Compute name
        :param context: Compute context
        :param shared_contexts: Shared contexts
        :param cluster: Compute cluster
        :param type: Compute type
        :param is_global: Is global
        :param features: Features
        :param wait: Wait for compute creation
        :return: Compute
        """

        payload = {
            'name': name,
            'context': context.to_json(),
            'type': type.value,
            'global': is_global,
            'features': features,
            'shared_contexts': [sc.to_json() for sc in shared_contexts],
            'cluster': cluster.to_json()
        }

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=self._base_url,
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = entities.Compute.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        if wait:
            command_id = compute.metadata.get('system', {}).get('commands', {}).get('create', {})
            if command_id is not None:
                command = self.commands.get(command_id=command_id, url='api/v1/commands/faas/{}'.format(command_id))
                command.wait()
                compute = self.get(compute_id=compute.id)

        return compute

    def get(self, compute_id: str):
        """
        Get a compute

        :param compute_id: Compute ID
        :return: Compute
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='get',
            path=self._base_url + '/{}'.format(compute_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = entities.Compute.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return compute

    def update(self, compute: entities.Compute):
        """
        Update a compute

        :param compute: Compute
        :return: Compute
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path=self._base_url + '/{}'.format(compute.id),
            json_req=compute.to_json()
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = entities.Compute.from_json(
            _json=response.json(),
            client_api=self._client_api
        )

        return compute

    def delete(self, compute_id: str):
        """
        Delete a compute

        :param compute_id: compute ID
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='delete',
            path=self._base_url + '/{}'.format(compute_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        return True


class ServiceDrivers:

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api
        self._base_url = '/serviceDrivers'

    def create(
            self,
            name: str,
            compute_id: str,
            context: entities.ComputeContext
    ):
        """
        Create a new service driver

        :param name: Service driver name
        :param compute_id: Compute ID
        :param context: Compute context
        :return: Service driver

        """

        payload = {
            'name': name,
            'computeId': compute_id,
            'context': context.to_json()
        }

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

        :param service_driver_id: Service driver ID
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
