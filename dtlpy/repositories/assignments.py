import logging

from .. import exceptions, miscellaneous, entities, repositories, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Assignments:
    """
    Assignments Repository

    The Assignments class allows users to manage assignments and their properties.
    Read more about `Task Assignment <https://developers.dataloop.ai/tutorials/task_workflows/create_a_task/chapter/>`_ in our Developers documentation.
    """

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 task: entities.Task = None,
                 dataset: entities.Dataset = None,
                 project_id=None):
        self._client_api = client_api
        self._project = project
        self._dataset = dataset
        self._task = task

        self._project_id = project_id
        if self._project_id is None and self._project is not None:
            self._project_id = self._project.id

    ############
    # entities #
    ############
    @property
    def task(self) -> entities.Task:
        if self._task is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "task". need to set an Task entity or use task.assignments repository')
        assert isinstance(self._task, entities.Task)
        return self._task

    @task.setter
    def task(self, task: entities.Task):
        if not isinstance(task, entities.Task):
            raise ValueError('Must input a valid Task entity')
        self._task = task

    @property
    def project_id(self):
        if self._project_id is not None:
            return self._project_id
        elif self._project is not None:
            return self._project.id
        else:
            return None

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.assignments repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def list(self,
             project_ids: list = None,
             status: str = None,
             assignment_name: str = None,
             assignee_id: str = None,
             pages_size: int = None,
             page_offset: int = None,
             task_id: int = None
             ) -> miscellaneous.List[entities.Assignment]:
        """
        Get Assignment list to be able to use it in your code.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param list project_ids: search assignment by given list of project ids
        :param str status: search assignment by a given task status
        :param str assignment_name: search assignment by a given assignment name
        :param str assignee_id: the user email that assignee the assignment to it
        :param int pages_size: pages size of the output generator
        :param int page_offset: page offset of the output generator
        :param str task_id: search assignment by given task id
        :return: List of Assignment objects
        :rtype: miscellaneous.List[dtlpy.entities.assignment.Assignment]

        **Example**:

        .. code-block:: python

            assignments = task.assignments.list(status='complete', assignee_id='user@dataloop.ai', pages_size=100, page_offset=0)
        """

        # url
        url = '/assignments'

        query = list()
        if project_ids is not None:
            if not isinstance(project_ids, list):
                project_ids = [project_ids]
        elif self._project_id is not None:
            project_ids = [self._project_id]
        elif self._project is not None:
            project_ids = [self._project.id]
        else:
            raise exceptions.PlatformException(error='400', message='Must provide project')

        project_ids = ','.join(project_ids)
        query.append('projects={}'.format(project_ids))

        if status is not None:
            query.append('status={}'.format(status))
        if assignment_name is not None:
            query.append('name={}'.format(assignment_name))
        if assignee_id is not None:
            query.append('annotator={}'.format(assignee_id))
        if pages_size is not None:
            query.append('pageSize={}'.format(pages_size))
        if pages_size is None:
            query.append('pageSize={}'.format(500))
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))

        if task_id is None and self._task is not None:
            task_id = self._task.id
        if task_id is not None:
            query.append('taskId={}'.format(task_id))

        if len(query) > 0:
            query_string = '&'.join(query)
            url = '{}?{}'.format(url, query_string)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            assignments = miscellaneous.List(
                [entities.Assignment.from_json(client_api=self._client_api,
                                               _json=_json, project=self._project, dataset=self._dataset,
                                               task=self._task)
                 for _json in response.json()['items']])
        else:
            logger.error('Platform error getting assignments')
            raise exceptions.PlatformException(response)
        return assignments

    @_api_reference.add(path='/assignments/{id}', method='get')
    def get(self,
            assignment_name: str = None,
            assignment_id: str = None):
        """
        Get Assignment object to use it in your code.

        :param str assignment_name: optional - search by name
        :param str assignment_id: optional - search by id
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment

        **Example**:

        .. code-block:: python

            assignment = task.assignments.get(assignment_id='assignment_id')
        """

        if assignment_id is not None:
            url = '/assignments/{}'.format(assignment_id)
            success, response = self._client_api.gen_request(req_type='get',
                                                             path=url)
            if not success:
                raise exceptions.PlatformException('404', 'Assignment not found')
            else:
                assignment = entities.Assignment.from_json(_json=response.json(),
                                                           client_api=self._client_api,
                                                           project=self._project,
                                                           dataset=self._dataset,
                                                           task=self._task)
                # verify input assignment name is same as the given id
                if assignment_name is not None and assignment.name != assignment_name:
                    logger.warning(
                        "Mismatch found in assignments.get: assignment_name is different then assignment.name: "
                        "{!r} != {!r}".format(
                            assignment_name,
                            assignment.name))
        elif assignment_name is not None:
            assignments = [assignment for assignment in self.list() if assignment.name == assignment_name]
            if len(assignments) == 0:
                raise exceptions.PlatformException('404', 'Assignment not found')
            elif len(assignments) > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one assignment exist with the same name: {}'.format(
                                                       assignment_name))
            else:
                assignment = assignments[0]
        else:
            raise exceptions.PlatformException('400', 'Must provide either assignment name or assignment id')

        assert isinstance(assignment, entities.Assignment)
        return assignment

    @property
    def platform_url(self):
        if self.task.id is None or self.project_id is None:
            raise ValueError("must have project and task")

        return self._client_api._get_resource_url(
            "projects/{}/tasks/{}/assignments".format(self.project_id, self.task.id))

    def open_in_web(self,
                    assignment_name: str = None,
                    assignment_id: str = None,
                    assignment: str = None):
        """
        Open the assignment in the platform.

        **Prerequisites**: All users.

        :param str assignment_name: the name of the assignment
        :param str assignment_id: the Id of the assignment
        :param dtlpy.entities.assignment.Assignment assignment: assignment object

        **Example**:

        .. code-block:: python

            task.assignments.open_in_web(assignment_id='assignment_id')
        """
        if assignment_name is not None:
            assignment = self.get(assignment_name=assignment_name)
        if assignment is not None:
            assignment.open_in_web()
        elif assignment_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(assignment_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    @_api_reference.add(path='/assignments/{id}/reassign', method='post')
    def reassign(self,
                 assignee_id: str,
                 assignment: entities.Assignment = None,
                 assignment_id: str = None,
                 task: entities.Task = None,
                 task_id: str = None,
                 wait: bool = True):
        """
        Reassign an assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param str assignee_id: the email of the user that want to assign the assignment
        :param dtlpy.entities.assignment.Assignment assignment: assignment object
        :param assignment_id: the Id of the assignment
        :param dtlpy.entities.task.Task task: task object
        :param str task_id: the Id of the task that include the assignment
        :param bool wait: wait until reassign assignment finish
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment

        **Example**:

        .. code-block:: python

            assignment = task.assignments.reassign(assignee_ids='annotator1@dataloop.ai')
        """
        if assignment_id is None and assignment is None:
            raise exceptions.PlatformException('400', 'Must provide either assignment or assignment_id')
        elif assignment_id is None:
            assignment_id = assignment.id

        if task_id is None and task is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task_id')
        elif task_id is None:
            task_id = task.id

        url = '/assignments/{}/reassign'.format(assignment_id)

        payload = {
            'taskId': task_id,
            'annotator': assignee_id,
            'asynced': wait
        }

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)
        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if 'toAssignment' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="'toAssignment' key is missing in command response: {}"
                                                   .format(response))
            return self.get(assignment_id=command.spec['toAssignment'])
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/assignments/{id}/redistribute', method='post')
    def redistribute(self,
                     workload: entities.Workload,
                     assignment: entities.Assignment = None,
                     assignment_id: str = None,
                     task: entities.Task = None,
                     task_id: str = None,
                     wait: bool = True):
        """
        Redistribute an assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        **Example**:

        :param dtlpy.entities.assignment.Workload workload: list of WorkloadUnit objects. Customize distribution (percentage) between the task assignees. For example: [dl.WorkloadUnit(annotator@hi.com, 80), dl.WorkloadUnit(annotator2@hi.com, 20)]
        :param dtlpy.entities.assignment.Assignment assignment: assignment object
        :param str assignment_id: the Id of the assignment
        :param dtlpy.entities.task.Task task: the task object that include the assignment
        :param str task_id: the Id of the task that include the assignment
        :param bool wait: wait until redistribute assignment finish
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment assignment

        .. code-block:: python

            assignment = task.assignments.redistribute(workload=dl.Workload([dl.WorkloadUnit(assignee_id="annotator1@dataloop.ai", load=50),
                                                                dl.WorkloadUnit(assignee_id="annotator2@dataloop.ai", load=50)]))
        """
        if assignment_id is None and assignment is None:
            raise exceptions.PlatformException('400', 'Must provide either assignment or assignment_id')
        elif assignment_id is None:
            assignment_id = assignment.id

        if task_id is None and task is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task_id')
        elif task_id is None:
            task_id = task.id

        url = '/assignments/{}/redistribute'.format(assignment_id)

        payload = {
            'taskId': task_id,
            'workload': workload.to_json(),
            'asynced': wait
        }

        if self._task is None:
            self._task = self.get(assignment_id=assignment_id).task
        if task is None:
            task = self._task

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)
        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if 'workload' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="workload key is missing in command response: {}"
                                                   .format(response))

            task_assignments = task.assignments.list()
            workers = list()
            for worker in workload:
                workers.append(worker.assignee_id.lower())

            redistributed_assignments = list()
            for ass in task_assignments:
                if ass.annotator in workers:
                    redistributed_assignments.append(ass)
                    workers.remove(ass.annotator)
                    if not workers:
                        break

            return miscellaneous.List(redistributed_assignments)
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/assignments/{id}', method='patch')
    def update(self,
               assignment: entities.Assignment = None,
               system_metadata: bool = False
               ) -> entities.Assignment:
        """
        Update an assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param dtlpy.entities.assignment.Assignment assignment assignment: assignment entity
        :param bool system_metadata: True, if you want to change metadata system
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment assignment

        **Example**:

        .. code-block:: python

            assignment = task.assignments.update(assignment='assignment_entity', system_metadata=False)
        """
        url = '/assignments/{}'.format(assignment.id)

        if system_metadata:
            url += '?system=true'

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url,
                                                         json_req=assignment.to_json())
        if success:
            return entities.Assignment.from_json(_json=response.json(),
                                                 client_api=self._client_api, project=self._project,
                                                 dataset=self._dataset, task=self._task)
        else:
            raise exceptions.PlatformException(response)

    def create(self,
               assignee_id: str,
               task: entities.Task = None,
               filters: entities.Filters = None,
               items: list = None) -> entities.Assignment:
        """
        Create a new assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param str assignee_id: the email of the user that want to assign the assignment
        :param dtlpy.entities.task.Task task: the task object that include the assignment
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param list items: list of items (item Id or objects) to insert to the assignment
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment assignment

        **Example**:

        .. code-block:: python

            assignment = task.assignments.create(assignee_id='annotator1@dataloop.ai')
        """
        return self._create_in_task(assignee_id=assignee_id, task=task, filters=filters, items=items)

    def _create_in_task(self, assignee_id, task, filters=None, items=None) -> entities.Assignment:

        if task is None:
            if self._task is None:
                raise exceptions.PlatformException('400', 'Must provide task')
            task = self._task

        assignments_before = [ass.id for ass in task.assignments.list()]

        if filters is None and items is None:
            raise exceptions.PlatformException('400', 'Must provide either filters or items list')

        workload = entities.Workload.generate(assignee_ids=[assignee_id])
        task = task.add_items(filters=filters, items=items, workload=workload, limit=None)
        assignments = [ass for ass in task.assignments.list() if ass.id not in assignments_before]

        if len(assignments) < 1:
            raise exceptions.PlatformException('Error creating an assignment, '
                                               'Please use task.add_items() to perform this action')

        return assignments[0]

    def __item_operations(self, dataset: entities.Dataset,
                          op, assignment_id=None, assignment_name=None, filters=None, items=None):
        if assignment_id is None and assignment_name is None:
            raise exceptions.PlatformException('400', 'Must provide either assignment name or assignment id')
        elif assignment_id is None:
            assignment_id = self.get(assignment_name=assignment_name).id

        try:
            if filters is None and items is None:
                raise exceptions.PlatformException('400', 'Must provide either filters or items list')

            if filters is None:
                if not isinstance(items, list):
                    items = [items]
                filters = entities.Filters(field='id',
                                           values=[item.id for item in items],
                                           operator=entities.FiltersOperations.IN,
                                           use_defaults=False)

            filters._ref_assignment = True
            filters._ref_assignment_id = assignment_id
            filters._ref_op = op

            return dataset.items.update(filters=filters)
        finally:
            if filters is not None:
                filters._nullify_refs()

    def get_items(self,
                  assignment: entities.Assignment = None,
                  assignment_id=None,
                  assignment_name=None,
                  dataset=None,
                  filters=None
                  ) -> entities.PagedEntities:
        """
        Get all the items in the assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param dtlpy.entities.assignment.Assignment assignment: assignment object
        :param assignment_id: the Id of the assignment
        :param str assignment_name: the name of the assignment
        :param dtlpy.entities.dataset.Dataset dataset: dataset object, the dataset that refer to the assignment
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: pages of the items
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            items = task.assignments.get_items(assignment_id='assignment_id')
        """
        if assignment is None and assignment_id is None and assignment_name is None:
            raise exceptions.PlatformException('400',
                                               'Please provide either assignment,  assignment_id or assignment_name')

        if assignment_id is None:
            if assignment is None:
                assignment = self.get(assignment_name=assignment_name)
            assignment_id = assignment.id

        if dataset is None and self._dataset is None:
            if assignment is None:
                assignment = self.get(assignment_id=assignment_id, assignment_name=assignment_name)
            if assignment.dataset_id is None:
                raise exceptions.PlatformException('400', 'Please provide a dataset entity')
            dataset = repositories.Datasets(client_api=self._client_api, project=self._project).get(
                dataset_id=assignment.dataset_id)
        elif dataset is None:
            dataset = self._dataset

        if filters is None:
            filters = entities.Filters(use_defaults=False)
        filters.add(field='metadata.system.refs.id', values=[assignment_id], operator=entities.FiltersOperations.IN)

        return dataset.items.list(filters=filters)

    def set_status(self,
                   status: str,
                   operation: str,
                   item_id: str,
                   assignment_id: str
                   ) -> bool:
        """
        Set item status within assignment.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param str status: string the describes the status
        :param str operation: the status action need 'create' or 'delete'
        :param str item_id: item id that want to set his status
        :param assignment_id: the Id of the assignment
        :return: True id success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = task.assignments.set_status(assignment_id='assignment_id',
                                        status='complete',
                                        operation='created',
                                        item_id='item_id')
        """
        url = '/assignments/{assignment_id}/items/{item_id}/status'.format(assignment_id=assignment_id, item_id=item_id)
        payload = {
            'operation': operation,
            'status': status
        }
        success, response = self._client_api.gen_request(
            req_type='post',
            path=url,
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        return True
