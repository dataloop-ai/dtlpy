import logging
from urllib.parse import urlencode

from .. import exceptions, entities

logger = logging.getLogger(name=__name__)


class Executions:
    """
    Service Executions repository
    """

    def __init__(self, client_api, service=None, project=None):
        self._client_api = client_api
        self._service = service
        self._project = project

    ############
    # entities #
    ############
    @property
    def service(self):
        if self._service is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "service". need to set a Service entity or use service.executions repository')
        assert isinstance(self._service, entities.Service)
        return self._service

    @service.setter
    def service(self, service):
        if not isinstance(service, entities.Service):
            raise ValueError('Must input a valid Service entity')
        self._service = service

    @property
    def project(self):
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
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def create(self, service_id=None, sync=False, execution_input=None, function_name=None,
               resource=None, item_id=None, dataset_id=None, annotation_id=None):
        """
        Create service entity
        :param function_name:
        :param annotation_id:
        :param item_id:
        :param resource:
        :param sync:
        :param service_id:
        :param execution_input:
        :param dataset_id:
        :return:
        """
        if service_id is None:
            if self._service is None:
                raise exceptions.PlatformException('400', 'Please provide service id')
            service_id = self._service.id

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

        # request url
        url_path = '/executions/{service_id}'.format(service_id=service_id)
        if sync:
            url_path += '?sync=true'

        if function_name is not None:
            payload['functionName'] = function_name
        else:
            payload['functionName'] = 'run'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Execution.from_json(_json=response.json(),
                                            client_api=self._client_api,
                                            service=self._service)

    def list(self, service_id=None, page_offset=0, page_size=1000, order_by_type=None,
             order_by_direction=None, project_id=None, status=None):
        """
        List service executions
        :return:
        """

        # either project or service
        if project_id is None and self._project is not None:
            project_id = self._project.id
        if service_id is None and self._service is not None:
            service_id = self._service.id

        paged = entities.PagedEntities(items_repository=self,
                                       filters=None,
                                       page_offset=page_offset,
                                       page_size=page_size,
                                       client_api=self._client_api,
                                       item_entity=self,
                                       service_id=service_id,
                                       project_id=project_id,
                                       order_by_direction=order_by_direction,
                                       order_by_type=order_by_type,
                                       execution_status=status)
        paged.get_page()
        return paged

    def get_list(self, service_id=None, project_id=None, page_offset=None, page_size=None, order_by_type=None,
                 order_by_direction=None, status=None):
        """
        List service executions
        :return:
        """
        url = '/executions'
        query_params = {
            'orderByType': order_by_type,
            'orderByDirection': order_by_direction,
            'pageOffset': page_offset,
            'pageSize': page_size,
            'status': status
        }

        if service_id is not None:
            query_params['service'] = service_id
        else:
            query_params['projects'] = project_id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def get(self, execution_id=None):
        """
        Get Service execution object

        :param execution_id:
        :return: Service execution object
        """
        # get by id
        # request
        success, response = self._client_api.gen_request(
            req_type="get",
            path="/executions/{}".format(execution_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Execution.from_json(client_api=self._client_api,
                                            _json=response.json(),
                                            service=self._service)

    def progress_update(self, execution_id, status=None, percent_complete=None, message=None, output=None):
        """
        Update Execution Progress

        :param execution_id:
        :param status:
        :param percent_complete:
        :param message:
        :param output:
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
                                                service=self._service)
        else:
            raise exceptions.PlatformException(response)
