import base64
import datetime
import json

from ..services.api_client import ApiClient
from .. import exceptions, entities, repositories
from typing import List, Optional, Dict
from ..entities import ComputeCluster, ComputeContext, ComputeType, Project
from ..entities.integration import IntegrationType


class Computes:

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api
        self._base_url = '/compute'
        self._commands = None
        self._projects = None
        self._organizations = None

    @property
    def commands(self) -> repositories.Commands:
        if self._commands is None:
            self._commands = repositories.Commands(client_api=self._client_api)
        return self._commands

    @property
    def projects(self):
        if self._projects is None:
            self._projects = repositories.Projects(client_api=self._client_api)
        return self._projects

    @property
    def organizations(self):
        if self._organizations is None:
            self._organizations = repositories.Organizations(client_api=self._client_api)
        return self._organizations

    def create(
            self,
            name: str,
            context: entities.ComputeContext,
            shared_contexts: Optional[List[entities.ComputeContext]],
            cluster: entities.ComputeCluster,
            type: entities.ComputeType = entities.ComputeType.KUBERNETES,
            is_global: Optional[bool] = False,
            features: Optional[Dict] = None,
            wait=True,
            status: entities.ComputeStatus = None
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
        :param status: Compute status
        :return: Compute
        """

        payload = {
            'name': name,
            'context': context.to_json(),
            'type': type.value,
            'global': is_global,
            'features': features,
            'shared_contexts': [sc.to_json() for sc in shared_contexts],
            'cluster': cluster.to_json(),
            'status': status
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
            command_id = compute.metadata.get('system', {}).get('commands', {}).get('create', None)
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

    @staticmethod
    def read_file(file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            print(f"The file at {file_path} was not found.")
        except IOError:
            print(f"An error occurred while reading the file at {file_path}.")

    def decode_and_parse_input(self, file_path):
        """Decode a base64 encoded string from file a and parse it as JSON."""
        decoded_bytes = base64.b64decode(self.read_file(file_path))
        return json.loads(decoded_bytes)

    @staticmethod
    def create_integration(org, name, auth_data):
        """Create a new key-value integration within the specified project."""
        return org.integrations.create(
            integrations_type=IntegrationType.KEY_VALUE,
            name=name,
            options={
                'key': name,
                'value': json.dumps(auth_data)
            }
        )

    def setup_compute_cluster(self, config, integration, org_id, project=None):
        """Set up a compute cluster using the provided configuration and integration."""
        cluster = ComputeCluster.from_setup_json(config, integration)
        project_id = None
        if project is not None:
            project_id = project.id
        compute = self.create(
            config['config']['name'],
            ComputeContext([], org_id, project_id),
            [],
            cluster,
            ComputeType.KUBERNETES,
            status=config['config'].get('status', None))
        return compute

    def create_from_config_file(self, config_file_path, org_id, project_name: Optional[str] = None):
        config = self.decode_and_parse_input(config_file_path)
        project = None
        if project_name is not None:
            project = self.projects.get(project_name=project_name)
        org = self.organizations.get(organization_id=org_id)
        integration_name = ('cluster_integration_test_' + datetime.datetime.now().isoformat().split('.')[0]
                            .replace(':', '_'))
        integration = self.create_integration(org, integration_name, config['authentication'])
        compute = self.setup_compute_cluster(config, integration, org_id, project)
        return compute


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
