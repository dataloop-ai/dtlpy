import logging

from .. import exceptions, miscellaneous, entities, repositories, services

logger = logging.getLogger(name='dtlpy')


class Assignments:
    """
    Assignments repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
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
    def list(self, project_ids=None, status=None, assignment_name=None, assignee_id=None, pages_size=None,
             page_offset=None, task_id=None) -> miscellaneous.List[entities.Assignment]:
        """
        Get Assignments list

        :param project_ids: list of project ids
        :param status:
        :param assignment_name:
        :param assignee_id:
        :param pages_size:
        :param page_offset:
        :param task_id:
        :return: List of Assignment objects
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
            raise ('400', 'Must provide project')

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

    def get(self, assignment_name=None, assignment_id=None):
        """
        Get a Project object
        :param assignment_name: optional - search by name
        :param assignment_id: optional - search by id
        :return: Project object

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

    def open_in_web(self, assignment_name=None, assignment_id=None, assignment=None):
        """
        :param assignment_name:
        :param assignment_id:
        :param assignment:
        """
        if assignment_name is not None:
            assignment = self.get(assignment_name=assignment_name)
        if assignment is not None:
            assignment.open_in_web()
        elif assignment_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(assignment_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def reassign(self, assignee_id, assignment=None, assignment_id=None, task=None, task_id=None, wait=True):
        """
        Reassign an assignment
        :param assignee_id:
        :param assignment:
        :param assignment_id:
        :param task:
        :param task_id:
        :param wait: wait the command to finish
        :return: Assignment object
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

    def redistribute(self, workload, assignment=None, assignment_id=None, task=None, task_id=None, wait=True):
        """
        Redistribute an assignment
        :param workload:
        :param assignment:
        :param assignment_id:
        :param task:
        :param task_id:
        :param wait: wait the command to finish
        :return: Assignment object
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
                workers.append(worker.assignee_id)

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

    def update(self, assignment: entities.Assignment = None, system_metadata=False) -> entities.Assignment:
        """
        Update an assignment
        :param assignment: assignment entity
        :param system_metadata: bool - True, if you want to change metadata system
        :return: Assignment object
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

    def create(self, assignee_id, task=None, filters=None, items=None) -> entities.Assignment:
        """
        Create a new assignment
        :param assignee_id: the assignee for the assignment
        :param task: task entity
        :param filters: Filters entity or a dictionary containing filters parameters
        :param items: list of items
        :return: Assignment object
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
        task = task.add_items(filters=filters, items=items, workload=workload, limit=0)
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

    def get_items(self, assignment: entities.Assignment = None,
                  assignment_id=None, assignment_name=None, dataset=None, filters=None) -> entities.PagedEntities:
        """
        Get all the items in the assignment
        :param assignment: assignment entity
        :param assignment_id: assignment id
        :param assignment_name: assignment name
        :param dataset: dataset entity
        :param filters: Filters entity or a dictionary containing filters parameters
        :return:
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

    def set_status(self, status: str, operation: str, item_id: str, assignment_id: str):
        """
        Set item status within assignment
        @param status: str
        @param operation: created/deleted
        @param item_id: str
        @param assignment_id: str
        @return: Boolean
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
