import base64
import datetime
import json

from dtlpy import miscellaneous

from ..services.api_client import ApiClient
from .. import exceptions, entities, repositories
from typing import List, Optional, Dict
from ..entities import ComputeCluster, ComputeContext, ComputeType
from ..entities.integration import IntegrationType
import logging
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

logger = logging.getLogger(name='dtlpy')


class Computes:

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api
        self._base_url = '/compute'
        self._commands = None
        self._projects = None
        self._organizations = None
        self.log_cache = dict()

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
            status: entities.ComputeStatus = None,
            settings: entities.ComputeSettings = None,
            metadata: dict = None,
            deployment_configuration: dict = None
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
        :param settings: Compute settings
        :param metadata: Compute metadata
        :param deployment_configuration: Compute deployment Configuration
        :return: Compute
        :rtype: dl.entities.compute.Compute
        """
        if metadata is None:
            metadata = {}
        shared_contexts_json = []
        for shared_context in shared_contexts:
            src_json = shared_context.to_json() if isinstance(shared_context,
                                                              entities.ComputeContext) else shared_context
            shared_contexts_json.append(src_json)
        payload = {
            'name': name,
            'context': context.to_json(),
            'type': type.value,
            'global': is_global,
            'features': features,
            'sharedContexts': shared_contexts_json,
            'cluster': cluster.to_json(),
            'status': status,
            "settings": settings.to_json() if isinstance(settings, entities.ComputeSettings) else settings,
            "metadata": metadata,
            "deploymentConfiguration": deployment_configuration
        }

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=self._base_url,
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = self._build_compute_by_type(response.json())

        if wait:
            command_id = compute.metadata.get('system', {}).get('commands', {}).get('create', None)
            if command_id is not None:
                command = self.commands.get(command_id=command_id, url='api/v1/commands/faas/{}'.format(command_id))
                try:
                    callback = self.__get_log_compute_progress_callback(compute.id)
                    command.wait(iteration_callback=callback)
                    callback()
                except Exception as e:
                    self.log_cache.pop(compute.id, None)
                    raise e
                compute = self.get(compute_id=compute.id)

        return compute

    def _build_compute_by_type(self, _json):
        if _json.get('type') == 'kubernetes':
            compute = entities.KubernetesCompute.from_json(
                _json=_json,
                client_api=self._client_api
            )
        else:
            compute = entities.Compute.from_json(
                _json=_json,
                client_api=self._client_api
            )
        return compute

    def __get_log_compute_progress_callback(self, compute_id: str, is_destroy=False):
        def func():
            compute = self.get(compute_id=compute_id, archived=True)
            log_type = 'bootstrap'
            validation_progress = None
            validation_logs = None
            if is_destroy is True:
                log_type = 'destroy'
            else:
                validation_progress = compute.metadata.get('system', {}).get('validation', {}).get('progress', None)
                validation_logs = compute.metadata.get('system', {}).get('validation', {}).get('logs', None)
            bootstrap_progress = compute.metadata.get('system', {}).get(log_type, {}).get('progress', None)
            bootstrap_logs = compute.metadata.get('system', {}).get(log_type, {}).get('logs', None)

            if bootstrap_progress is not None:
                if 'bootstrap' not in self.log_cache.get(compute_id, {}):
                    logger.info(f"{log_type} in progress:")
                last_index = len(self.log_cache.get(compute_id, {}).get(log_type, []))
                new_logs = bootstrap_logs[last_index:]
                if new_logs:
                    for log in new_logs:
                        logger.info(log)
                    logger.info(f'{log_type} progress: {int(bootstrap_progress)}%')
                    if compute_id not in self.log_cache:
                        self.log_cache[compute_id] = {}
                    self.log_cache[compute_id][log_type] = bootstrap_logs
            if bootstrap_progress in [100, None] and validation_progress is not None:
                if 'validation' not in self.log_cache.get(compute_id, {}):
                    logger.info(f"Validating created compute:")
                last_index = len(self.log_cache.get(compute_id, {}).get('validation', []))
                new_logs = validation_logs[last_index:]
                if new_logs:
                    for log in new_logs:
                        logger.info(log)
                    logger.info(f'Validation progress: {int(validation_progress)}%')
                    if compute_id not in self.log_cache:
                        self.log_cache[compute_id] = {}
                    self.log_cache[compute_id]['validation'] = validation_logs

        return func

    def get(self, compute_id: str, archived=False):
        """
        Get a compute

        :param compute_id: Compute ID
        :param archived: Archived
        :return: Compute
        :rtype: dl.entities.compute.Compute
        """
        url_path = self._base_url + '/{}'.format(compute_id)
        params_to_add = {"archived": "true" if archived else "false"}
        parsed_url = urlparse(url_path)
        query_dict = parse_qs(parsed_url.query)
        query_dict.update(params_to_add)
        new_query = urlencode(query_dict, doseq=True)
        url_path = urlunparse(parsed_url._replace(query=new_query))
        # request
        success, response = self._client_api.gen_request(
            req_type='get',
            path=url_path
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = self._build_compute_by_type(response.json())

        return compute

    def update(self, compute: entities.Compute):
        """
        Update a compute

        :param compute: Compute
        :return: Compute
        :rtype: dl.entities.compute.Compute
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='patch',
            path=self._base_url + '/{}'.format(compute.id),
            json_req=compute.to_json()
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = self._build_compute_by_type(response.json())

        return compute

    def delete(self, compute_id: str, skip_destroy: bool = False, wait: bool = True):
        """
        Delete a compute

        :param compute_id: compute ID
        :param skip_destroy: bool
        :param bool wait: Wait for deletion
        """
        url_path = self._base_url + '/{}'.format(compute_id)
        params_to_add = {"skipDestroy": "true" if skip_destroy else "false"}
        parsed_url = urlparse(url_path)
        query_dict = parse_qs(parsed_url.query)
        query_dict.update(params_to_add)
        new_query = urlencode(query_dict, doseq=True)
        url_path = urlunparse(parsed_url._replace(query=new_query))
        # request
        success, response = self._client_api.gen_request(
            req_type='delete',
            path=url_path
        )

        if not success:
            raise exceptions.PlatformException(response)
        if skip_destroy is not True and wait is True:
            command_response = response.json()
            command_id = command_response['id']
            command = self.commands.get(command_id, url='api/v1/commands/faas/{}'.format(command_id))
            try:
                callback = self.__get_log_compute_progress_callback(compute_id, is_destroy=True)
                command.wait(iteration_callback=callback)
                callback()
            except Exception as e:
                self.log_cache.pop(command_id, None)
                raise e

        return True

    def validate(self, compute_id: str, wait: bool = True):
        """
        Validate a compute

        :param str compute_id: Compute ID
        :param bool wait: Wait for validation
        :return: Compute
        :rtype: dl.entities.compute.Compute
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path=self._base_url + '/{}/validate'.format(compute_id)
        )

        if not success:
            raise exceptions.PlatformException(response)

        compute = self._build_compute_by_type(response.json())

        if wait:
            command_id = compute.metadata.get('system', {}).get('commands', {}).get('validate', None)
            if command_id is not None:
                command = self.commands.get(command_id=command_id, url='api/v1/commands/faas/{}'.format(command_id))
                try:
                    callback = self.__get_log_compute_progress_callback(compute.id)
                    command.wait(iteration_callback=callback)
                    callback()
                except Exception as e:
                    self.log_cache.pop(compute.id, None)
                    raise e
                compute = self.get(compute_id=compute.id)

        return compute

    def list_global(self):
        """
        List computes

        :return: List of computes
        :rtype: list[str]
        """

        # request
        success, response = self._client_api.gen_request(
            req_type='get',
            path=self._base_url + '/globals',
        )

        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

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

    def setup_compute_cluster(self, config, integration, org_id, project=None, is_global=False):
        """Set up a compute cluster using the provided configuration and integration."""
        cluster = ComputeCluster.from_setup_json(config, integration)
        project_id = None
        if project is not None:
            project_id = project.id
        compute = self.create(
            config['config']['name'],
            ComputeContext(labels=[], org=org_id, project=project_id),
            [],
            cluster,
            ComputeType.KUBERNETES,
            status=config['config'].get('status', None),
            settings=config['config'].get('settings', None),
            deployment_configuration=config['config'].get('deploymentConfiguration', {}),
            metadata=config['config'].get('metadata', None), is_global=is_global)

        return compute

    def create_from_config_file(self, config_file_path, org_id, project_name: Optional[str] = None, is_global=False):
        config = self.decode_and_parse_input(config_file_path)
        project = None
        if project_name is not None:
            project = self.projects.get(project_name=project_name)
        org = self.organizations.get(organization_id=org_id)
        integration_name = ('cluster_integration_test_' + datetime.datetime.now().isoformat().split('.')[0]
                            .replace(':', '_'))
        integration = self.create_integration(org, integration_name, config['authentication'])
        compute = self.setup_compute_cluster(config, integration, org_id, project, is_global=is_global)
        return compute

    def _list(self, filters: entities.Filters):
        url = self._base_url + '/query'
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Compute]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.Compute._protected_from_json,
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
            filters = entities.Filters(resource=entities.FiltersResource.COMPUTE)

        if filters.resource != entities.FiltersResource.COMPUTE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.COMPUTE. Got: {!r}'.format(
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
