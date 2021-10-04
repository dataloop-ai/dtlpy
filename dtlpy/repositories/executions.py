import threading
import logging
import time
import numpy as np

from .. import exceptions, entities, repositories, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Executions:
    """
    Service Executions repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
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
    def create(self,
               # executions info
               service_id=None,
               execution_input=None,
               function_name=None,
               # inputs info
               resource: entities.PackageInputType = None,
               item_id=None,
               dataset_id=None,
               annotation_id=None,
               project_id=None,
               # execution config
               sync=False,
               stream_logs=False,
               return_output=False,
               # misc
               return_curl_only=False,
               timeout=None) -> entities.Execution:
        """
        Execute a function on an existing service

        :param service_id: service id to execute on
        :param execution_input: input dictionary or list of FunctionIO entities
        :param function_name: function name to run
        :param resource: input type.
        :param item_id: optional - input to function
        :param dataset_id: optional - input to function
        :param annotation_id: optional - input to function
        :param project_id: resource's project
        :param sync: wait for function to end
        :param stream_logs: prints logs of the new execution. only works with sync=True
        :param return_output: if True and sync is True - will return the output directly
        :param return_curl_only: return the cURL of the creation WITHOUT actually do it
        :param timeout: int, seconds to wait until TimeoutError is raised. if <=0 - wait until done -
         by default wait take the service timeout
        :return:
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

    def _list(self, filters: entities.Filters):
        """
        List service executions
        :param filters: dl.Filters entity to filters items
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

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List service executions
        :param filters: dl.Filters entity to filters items
        :return:
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

    def get(self, execution_id=None, sync=False) -> entities.Execution:
        """
        Get Service execution object

        :param execution_id:
        :param sync: wait for the execution to finish
        :return: Service execution object
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

    def logs(self, execution_id, follow=True, until_completed=True):
        """
        executions logs
        :param execution_id:
        :param follow:
        :param until_completed:
        :return: executions logs
        """
        return self.service.log(execution_id=execution_id,
                                follow=follow,
                                until_completed=until_completed,
                                view=True)

    def increment(self, execution: entities.Execution):
        """
        Increment attempts
        :param execution:
        :return: int
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

    def rerun(self, execution: entities.Execution, sync: bool = False):
        """
        Increment attempts
        :param execution:
        :param sync:
        :return: int
        """

        url_path = "/executions/{}/rerun".format(execution.id)
        if sync:
            url_path += '?sync=true'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return entities.Execution.from_json(
                client_api=self._client_api,
                _json=response.json(),
                project=self._project,
                service=self._service
            )

    def wait(self, execution_id, timeout=None):
        """
        Get Service execution object

        :param execution_id:
        :param timeout: int, seconds to wait until TimeoutError is raised. if <=0 - wait until done -
         by default wait take the service timeout
        :return: Service execution object
        """
        url_path = "/executions/{}".format(execution_id)
        elapsed = 0
        start = int(time.time())
        if timeout is not None and timeout <= 0:
            timeout = np.inf

        i = 1
        while True:
            success, response = self._client_api.gen_request(req_type="get",
                                                             path=url_path,
                                                             log_error=False)
            if not success:
                raise exceptions.PlatformException(response)
            # return entity
            execution = entities.Execution.from_json(client_api=self._client_api,
                                                     _json=response.json(),
                                                     project=self._project,
                                                     service=self._service)
            if timeout is None:
                timeout = execution.service.execution_timeout + 60
            if execution.latest_status['status'] not in ['inProgress', 'created']:
                break
            elapsed = int(time.time()) - start
            sleep_time = np.minimum(timeout - elapsed, 2 ** i)
            time.sleep(sleep_time)
            i += 1
            if i > 18 or elapsed > timeout:
                break
        if execution is None:
            raise ValueError('Nothing to wait for')
        if elapsed >= timeout:
            raise TimeoutError("execution wait() got timeout. id: {!r}, status: {}".format(
                execution.id, execution.latest_status))
        return execution

    def terminate(self, execution: entities.Execution):
        """
        Terminate Execution
        :param execution:
        :return:
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

    def update(self, execution: entities.Execution) -> entities.Execution:
        """
        Update execution changes to platform
        :param execution: execution entity
        :return: execution entity
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
        Update Execution Progress

        :param execution_id:
        :param status: ExecutionStatus
        :param percent_complete:
        :param message:
        :param output:
        :param service_version:
        :return:
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
