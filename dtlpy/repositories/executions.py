import threading
import logging
import time
from copy import deepcopy

import numpy as np

from .. import exceptions, entities, repositories, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')
MAX_SLEEP_TIME = 30


class Executions:
    """
    Service Executions Repository

    The Executions class allows the users to manage executions (executions of services) and their properties.
    See our documentation for more information about `executions <https://developers.dataloop.ai/tutorials/faas/execution_control/chapter/>`_.
    """

    def __init__(self,
                 client_api: ApiClient,
                 service: entities.Service = None,
                 project: entities.Project = None):
        self._client_api = client_api
        self._service = service
        self._project = project

    ############
    # entities #
    ############
    @property
    def service(self) -> entities.Service:
        if self._service is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "service". need to set a Service entity or use service.executions repository')
        assert isinstance(self._service, entities.Service)
        return self._service

    @service.setter
    def service(self, service: entities.Service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid Service entity')
        self._service = service

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            if self._service is not None:
                self._project = self._service._project
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

    def __get_from_entity(self, name, value):
        project_id = None
        try:
            from_dataset = False
            entity_obj = None
            for input_type in entities.FunctionIO.INPUT_TYPES:
                input_type = input_type.value
                entity = input_type.lower()
                param = '{}_id'.format(entity)
                if isinstance(value, dict):
                    if param in value:
                        repo = getattr(repositories, '{}s'.format(input_type))(client_api=self._client_api)
                        entity_obj = repo.get(**{param: value[param]})
                        if param in ['annotation_id', 'item_id']:
                            from_dataset = True
                            if param == 'item_id':
                                entity_obj = entity_obj.dataset
                            else:
                                entity_obj = repositories.Datasets(client_api=self._client_api).get(
                                    dataset_id=entity_obj.dataset_id)
                        elif param in ['dataset_id']:
                            from_dataset = True
                        break
                elif isinstance(value, str):
                    if entity == name:
                        repo = getattr(repositories, '{}s'.format(input_type))(client_api=self._client_api)
                        entity_obj = repo.get(**{param: value})
                        if name in ['annotation', 'item']:
                            from_dataset = True
                            if param == 'item_id':
                                entity_obj = entity_obj.dataset
                            else:
                                entity_obj = repositories.Datasets(client_api=self._client_api).get(
                                    dataset_id=entity_obj.dataset_id)
                        elif name in ['dataset']:
                            from_dataset = True
                        break

            if entity_obj is not None:
                if isinstance(entity_obj, entities.Project):
                    project_id = entity_obj.id
                elif from_dataset:
                    project_id = entity_obj.projects[0]
                else:
                    project_id = entity_obj.project_id
        except Exception:
            project_id = None

        return project_id

    def __get_project_id(self, project_id=None, payload=None):
        if project_id is None:
            inputs = payload.get('input', dict())
            try:
                for key, val in inputs.items():
                    project_id = self.__get_from_entity(name=key, value=val)
                    if project_id is not None:
                        break
            except Exception:
                project_id = None

            if project_id is None:
                # if still None - get from current repository
                if self._project is not None:
                    project_id = self._project.id
                else:
                    raise exceptions.PlatformException('400', 'Please provide project_id')

        return project_id

    ###########
    # methods #
    ###########
    @_api_reference.add(path='/executions/{serviceId}', method='post')
    def create(self,
               # executions info
               service_id: str = None,
               execution_input: list = None,
               function_name: str = None,
               # inputs info
               resource: entities.PackageInputType = None,
               item_id: str = None,
               dataset_id: str = None,
               annotation_id: str = None,
               project_id: str = None,
               # execution config
               sync: bool = False,
               stream_logs: bool = False,
               return_output: bool = False,
               # misc
               return_curl_only: bool = False,
               timeout: int = None) -> entities.Execution:
        """
        Execute a function on an existing service

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str service_id: service id to execute on
        :param List[FunctionIO] or dict execution_input: input dictionary or list of FunctionIO entities
        :param str function_name: function name to run
        :param str resource: input type.
        :param str item_id: optional - item id as input to function
        :param str dataset_id: optional - dataset id as input to function
        :param str annotation_id: optional - annotation id as input to function
        :param str project_id: resource's project
        :param bool sync: if true, wait for function to end
        :param bool stream_logs: prints logs of the new execution. only works with sync=True
        :param bool return_output: if True and sync is True - will return the output directly
        :param bool return_curl_only: return the cURL of the creation WITHOUT actually do it
        :param int timeout: int, seconds to wait until TimeoutError is raised. if <=0 - wait until done -
         by default wait take the service timeout
        :return: execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.create(function_name='function_name', item_id='item_id', project_id='project_id')
        """
        if service_id is None:
            if self._service is None:
                raise exceptions.PlatformException('400', 'Please provide service id')
            service_id = self._service.id

        if resource is None:
            if annotation_id is not None:
                resource = entities.PackageInputType.ANNOTATION
            elif item_id is not None:
                resource = entities.PackageInputType.ITEM
            elif dataset_id is not None:
                resource = entities.PackageInputType.DATASET

        # payload
        payload = dict()
        if execution_input is None:
            if resource is not None:
                inputs = {resource.lower(): {
                    'dataset_id': dataset_id}
                }
                if item_id is not None:
                    inputs[resource.lower()]['item_id'] = item_id
                if annotation_id is not None:
                    inputs[resource.lower()]['annotation_id'] = annotation_id
                payload['input'] = inputs
        else:
            if isinstance(execution_input, dict):
                payload['input'] = execution_input
            else:
                if not isinstance(execution_input, list):
                    execution_input = [execution_input]
                if len(execution_input) > 0 and isinstance(execution_input[0], entities.FunctionIO):
                    payload['input'] = dict()
                    for single_input in execution_input:
                        payload['input'].update(single_input.to_json(resource='execution'))
                else:
                    raise exceptions.PlatformException('400', 'Unknown input type')

        payload['projectId'] = self.__get_project_id(project_id=project_id, payload=payload)

        if function_name is not None:
            payload['functionName'] = function_name
        else:
            payload['functionName'] = entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME

        # request url
        url_path = '/executions/{service_id}'.format(service_id=service_id)

        if return_curl_only:
            curl = self._client_api.export_curl_request(req_type='post',
                                                        path=url_path,
                                                        json_req=payload)
            logger.warning(msg='Execution was NOT created. Exporting cURL only.')
            return curl
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        execution = entities.Execution.from_json(_json=response.json(),
                                                 client_api=self._client_api,
                                                 project=self._project,
                                                 service=self._service)

        if sync and not return_output and not stream_logs:
            execution = self.wait(execution_id=execution.id, timeout=timeout)

        if sync and (stream_logs or return_output):
            thread = None
            if stream_logs:
                thread = threading.Thread(target=self.logs,
                                          kwargs={'execution_id': execution.id,
                                                  'follow': True,
                                                  'until_completed': True})
                thread.setDaemon(True)
                thread.start()
            execution = self.get(execution_id=execution.id,
                                 sync=True)
            # stream logs
            if stream_logs and thread is not None:
                thread.join()
        if sync and return_output:
            return execution.output
        return execution

    @_api_reference.add(path='/executions/{serviceId}', method='post')
    def create_batch(self,
                     service_id: str,
                     filters,
                     function_name: str = None,
                     execution_inputs: list = None,
                     wait=True
                     ):
        """
        Execute a function on an existing service

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str service_id: service id to execute on
        :param filters: Filters entity for a filtering before execute
        :param str function_name: function name to run
        :param List[FunctionIO] or dict execution_inputs: input dictionary or list of FunctionIO entities, that represent the extra inputs of the function
        :param bool wait: wait until create task finish
        :return: execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            command = service.executions.create_batch(
                        execution_inputs=dl.FunctionIO(type=dl.PackageInputType.STRING, value='test', name='string'),
                        filters=dl.Filters(field='dir', values='/test'),
                        function_name='run')
        """
        if service_id is None:
            if self._service is None:
                raise exceptions.PlatformException('400', 'Please provide service id')
            service_id = self._service.id

        if filters is None:
            raise exceptions.PlatformException('400', 'Please provide filter')

        if execution_inputs is None:
            execution_inputs = dict()

        if isinstance(execution_inputs, dict):
            extra_inputs = execution_inputs
        else:
            if not isinstance(execution_inputs, list):
                execution_inputs = [execution_inputs]
            if len(execution_inputs) > 0 and isinstance(execution_inputs[0], entities.FunctionIO):
                extra_inputs = dict()
                for single_input in execution_inputs:
                    extra_inputs.update(single_input.to_json(resource='execution'))
            else:
                raise exceptions.PlatformException('400', 'Unknown input type')

        # payload
        payload = dict()
        payload['batch'] = dict()
        payload['batch']['query'] = filters.prepare()
        payload['batch']['args'] = extra_inputs

        if function_name is not None:
            payload['functionName'] = function_name
        else:
            payload['functionName'] = entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME

        # request url
        url_path = '/executions/{service_id}'.format(service_id=service_id)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        response_json = response.json()
        command = entities.Command.from_json(_json=response_json,
                                             client_api=self._client_api)
        if wait:
            command = command.wait(timeout=0)
        return command

    @_api_reference.add(path='/executions/rerun', method='post')
    def rerun_batch(self,
                    filters,
                    service_id: str = None,
                    wait=True
                    ):
        """
        rerun a executions on an existing service

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a Filter.

        :param filters: Filters entity for a filtering before rerun
        :param str service_id: service id to rerun on
        :param bool wait: wait until create task finish
        :return: rerun command
        :rtype: dtlpy.entities.command.Command

        **Example**:

        .. code-block:: python

            command = service.executions.rerun_batch(
                        filters=dl.Filters(field='id', values=['executionId'], operator=dl.FiltersOperations.IN, resource=dl.FiltersResource.EXECUTION))
        """
        url_path = '/executions/rerun'

        if filters is None:
            raise exceptions.PlatformException('400', 'Please provide filter')

        if filters.resource != entities.FiltersResource.EXECUTION:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.EXECUTION. Got: {!r}'.format(filters.resource))

        if service_id is not None and not filters.has_field('serviceId'):
            filters = deepcopy(filters)
            filters.add(field='serviceId', values=service_id, method=entities.FiltersMethod.AND)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req={'query': filters.prepare()['filter']})
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        response_json = response.json()
        command = entities.Command.from_json(_json=response_json,
                                             client_api=self._client_api)
        if wait:
            command = command.wait(timeout=0)
        return command

    def _list(self, filters: entities.Filters):
        """
        List service executions

        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return:
        """
        url = '/query/faas'

        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    @_api_reference.add(path='/query/faas', method='post')
    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List service executions

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            service.executions.list()
        """
        # default filtersf
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.EXECUTION)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(
                error='400',
                message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.EXECUTION:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.EXECUTION. Got: {!r}'.format(filters.resource))
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)
        if self._service is not None:
            filters.add(field='serviceId', values=self._service.id)

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
            jobs[i_item] = pool.submit(entities.Execution._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item,
                                          'project': self._project,
                                          'service': self._service})

        # get results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    @_api_reference.add(path='/executions/{id}', method='get')
    def get(self,
            execution_id: str = None,
            sync: bool = False
            ) -> entities.Execution:
        """
        Get Service execution object

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str execution_id: execution id
        :param bool sync: if true, wait for the execution to finish
        :return: Service execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.get(execution_id='execution_id')
        """
        url_path = "/executions/{}".format(execution_id)
        if sync:
            return self.wait(execution_id=execution_id)

        success, response = self._client_api.gen_request(req_type="get",
                                                         path=url_path)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Execution.from_json(client_api=self._client_api,
                                            _json=response.json(),
                                            project=self._project,
                                            service=self._service)

    def logs(self,
             execution_id: str,
             follow: bool = True,
             until_completed: bool = True):
        """
        executions logs

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str execution_id: execution id
        :param bool follow: if true, keep stream future logs
        :param bool until_completed: if true, wait until completed
        :return: executions logs

        **Example**:

        .. code-block:: python

            service.executions.logs(execution_id='execution_id')
        """
        return self.service.log(execution_id=execution_id,
                                follow=follow,
                                until_completed=until_completed,
                                view=True)

    def increment(self, execution: entities.Execution):
        """
        Increment the number of attempts that an execution is allowed to attempt to run a service that is not responding.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param dtlpy.entities.execution.Execution execution:
        :return: int
        :rtype: int

        **Example**:

        .. code-block:: python

            service.executions.increment(execution='execution_entity')
        """
        # request
        success, response = self._client_api.gen_request(
            req_type='post',
            path='/executions/{}/attempts'.format(execution.id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return response.json()

    @_api_reference.add(path='/executions/{executionId}/rerun', method='post')
    def rerun(self, execution: entities.Execution, sync: bool = False):
        """
        Rerun execution

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param dtlpy.entities.execution.Execution execution:
        :param bool sync: wait for the execution to finish
        :return: Execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.rerun(execution='execution_entity')
        """

        url_path = "/executions/{}/rerun".format(execution.id)
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        else:
            execution = entities.Execution.from_json(
                client_api=self._client_api,
                _json=response.json(),
                project=self._project,
                service=self._service
            )
            if sync:
                execution = self.wait(execution_id=execution.id)
        return execution

    def wait(self,
             execution_id: str = None,
             execution: entities.Execution = None,
             timeout: int = None,
             backoff_factor=1):
        """
        Get Service execution object.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str execution_id: execution id
        :param str execution: dl.Execution, optional. must input one of execution or execution_id
        :param int timeout: seconds to wait until TimeoutError is raised. if <=0 - wait until done - by default wait take the service timeout
        :param float backoff_factor: A backoff factor to apply between attempts after the second try
        :return: Service execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.wait(execution_id='execution_id')
        """
        if execution is None:
            if execution_id is None:
                raise ValueError('Must input at least one: [execution, execution_id]')
            else:
                execution = self.get(execution_id=execution_id)
        elapsed = 0
        start = int(time.time())
        if timeout is None or timeout <= 0:
            timeout = np.inf

        num_tries = 1
        while elapsed < timeout:
            execution = self.get(execution_id=execution.id)
            if not execution.in_progress():
                break
            elapsed = time.time() - start
            if elapsed >= timeout:
                raise TimeoutError(
                    f"execution wait() got timeout. id: {execution.id!r}, status: {execution.latest_status}")
            sleep_time = np.min([timeout - elapsed, backoff_factor * (2 ** num_tries), MAX_SLEEP_TIME])
            num_tries += 1
            logger.debug("Execution {!r} is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format(execution.id,
                                                                                                           elapsed,
                                                                                                           sleep_time))
            time.sleep(sleep_time)

        return execution

    @_api_reference.add(path='/executions/{id}/terminate', method='post')
    def terminate(self, execution: entities.Execution):
        """
        Terminate Execution

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param dtlpy.entities.execution.Execution execution:
        :return: execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.terminate(execution='execution_entity')
        """
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/executions/{}/terminate'.format(execution.id))

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return entities.Execution.from_json(_json=response.json(),
                                                service=self._service,
                                                project=self._project,
                                                client_api=self._client_api)

    @_api_reference.add(path='/executions/{id}', method='patch')
    def update(self, execution: entities.Execution) -> entities.Execution:
        """
        Update execution changes to platform

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param dtlpy.entities.execution.Execution execution: execution entity
        :return: Service execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.update(execution='execution_entity')
        """
        # payload
        payload = execution.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/executions/{}'.format(execution.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        if self._project is not None:
            project = self._project
        else:
            project = execution._project

        # return
        if self._service is not None:
            service = self._service
        else:
            service = execution._service

        return entities.Execution.from_json(_json=response.json(),
                                            service=service,
                                            project=self._project,
                                            client_api=self._client_api)

    def progress_update(
            self,
            execution_id: str,
            status: entities.ExecutionStatus = None,
            percent_complete: int = None,
            message: str = None,
            output: str = None,
            service_version: str = None
    ):
        """
        Update Execution Progress.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a service.

        :param str execution_id: execution id
        :param str status: ExecutionStatus
        :param int percent_complete: percent work done
        :param str message: message
        :param str output: the output of the execution
        :param str service_version: service version
        :return: Service execution object
        :rtype: dtlpy.entities.execution.Execution

        **Example**:

        .. code-block:: python

            service.executions.progress_update(execution_id='execution_id', status='complete', percent_complete=100)
        """
        # create payload
        payload = dict()

        if status is not None:
            payload['status'] = status
        else:
            if percent_complete is not None and isinstance(percent_complete, int):
                if percent_complete < 100:
                    payload['status'] = 'inProgress'
                else:
                    payload['status'] = 'completed'
            elif output is not None:
                payload['status'] = 'completed'
            else:
                payload['status'] = 'inProgress'

        if percent_complete is not None:
            payload['percentComplete'] = percent_complete

        if message is not None:
            payload['message'] = message

        if output is not None:
            payload['output'] = output

        if service_version is not None:
            payload['serviceVersion'] = service_version

        # request
        success, response = self._client_api.gen_request(
            req_type="post",
            path="/executions/{}/progress".format(execution_id),
            json_req=payload
        )

        # exception handling
        if success:
            return entities.Execution.from_json(_json=response.json(),
                                                client_api=self._client_api,
                                                project=self._project,
                                                service=self._service)
        else:
            raise exceptions.PlatformException(response)
