import logging

from .. import exceptions, miscellaneous, entities, repositories

logger = logging.getLogger(name=__name__)


class Assignments:
    """
    Assignments repository
    """

    def __init__(self, client_api, project=None, task=None, dataset=None, project_id=None):
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
    def task(self):
        if self._task is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "task". need to set an Task entity or use task.assignments repository')
        assert isinstance(self._task, entities.Task)
        return self._task

    @task.setter
    def task(self, task):
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
    def project(self):
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.assignments repository')
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
    def list(self, project_ids=None, status=None, assignment_name=None, assignee_id=None, pages_size=None,
             page_offset=None, task_id=None):
        """
        Get Assignments list

        :param task_id:
        :param page_offset:
        :param pages_size:
        :param assignee_id:
        :param assignment_name:
        :param status:
        :param project_ids: list of project ids
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
                                                           client_api=self._client_api, project=self._project,
                                                           dataset=self._dataset, task=self._task)
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

    def delete(self, assignment=None, assignment_name=None, assignment_id=None):
        """
        Delete an assignment
        :param assignment_id:
        :param assignment_name:
        :param assignment:

        :return: True
        """
        if assignment_id is None:
            if assignment is None:
                if assignment_name is None:
                    raise exceptions.PlatformException('400',
                                                       'Must provide either assignment, '
                                                       'assignment name or assignment id')
                else:
                    assignment = self.get(assignment_name=assignment_name)
                    assignment_id = assignment.id
        url = '/assignments/{}'.format(assignment_id)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=url)

        if not success:
            raise exceptions.PlatformException(response)
        return True

    def reassign(self, assignee_id, assignment=None, assignment_id=None, task=None, task_id=None):
        """
        Reassign an assignment
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
            'annotator': assignee_id
        }

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)
        if success:
            if task is None:
                task = self._task
            return entities.Assignment.from_json(_json=response.json(),
                                                 client_api=self._client_api, project=self._project,
                                                 dataset=self._dataset, task=task)
        else:
            raise exceptions.PlatformException(response)

    def redistribute(self, workload, assignment=None, assignment_id=None, task=None, task_id=None):
        """
        Redistribute an assignment
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
            'workload': workload.to_json()
        }

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)
        if success:
            if task is None:
                task = self._task
            redistributed_assignments = list()
            for redistributed_assignment in response.json():
                redistributed_assignments.append(entities.Assignment.from_json(_json=redistributed_assignment,
                                                                               client_api=self._client_api,
                                                                               project=self._project,
                                                                               dataset=self._dataset, task=task))
            return miscellaneous.List(redistributed_assignments)
        else:
            raise exceptions.PlatformException(response)

    def update(self, assignment=None, system_metadata=False):
        """
        Update an assignment
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

    # def create(self, assignment_name, assignee_id,
    #            dataset=None, project_id=None,
    #            filters=None, items=None,
    #            status=None, metadata=None):
    #     """
    #     Create a new assignment
    #     :param dataset:
    #     :param items:
    #     :param filters:
    #     :param metadata:
    #     :param project_id:
    #     :param status:
    #     :param assignee_id:
    #     :param assignment_name:
    #     :return: Assignment object
    #     """
    #
    #     if filters is None and items is None:
    #         raise exceptions.PlatformException('400', 'Must provide either filters or items list')
    #
    #     if dataset is None and self._dataset is None:
    #         raise exceptions.PlatformException('400', 'Please provide a dataset entity')
    #     elif dataset is None:
    #         dataset = self._dataset
    #
    #     if project_id is None:
    #         if self.project_id is None:
    #             raise exceptions.PlatformException('400', 'Please provide a project_id')
    #         project_id = self.project_id
    #
    #     payload = {'name': assignment_name,
    #                'projectId': project_id,
    #                'annotator': assignee_id}
    #
    #     if status is not None:
    #         payload['status'] = status
    #
    #     if metadata is None:
    #         metadata = dict()
    #     metadata['system'] = {'datasetId': dataset.id}
    #     payload['metadata'] = metadata
    #
    #     if self._task is not None:
    #         payload['metadata']['system']['taskId'] = self._task.id
    #
    #     success, response = self._client_api.gen_request(req_type='post',
    #                                                      path='/assignments',
    #                                                      json_req=payload)
    #     if success:
    #         assignment = entities.Assignment.from_json(client_api=self._client_api,
    #                                                    _json=response.json(), project=self._project,
    #                                                    dataset=dataset, task=self._task)
    #     else:
    #         raise exceptions.PlatformException(response)
    #     assert isinstance(assignment, entities.Assignment)
    #
    #     if self._task is not None:
    #         self.task.assignmentIds.append(assignment.id)
    #         self.task.update()
    #
    #     self.assign_items(dataset=dataset, assignment_id=assignment.id, filters=filters, items=items)
    #
    #     return assignment

    def create(self, assignee_id, task=None,
               assignment_name=None,
               dataset=None, project_id=None,
               filters=None, items=None,
               status=None, metadata=None):
        """
        Create a new assignment
        :param task:
        :param dataset:
        :param items:
        :param filters:
        :param metadata:
        :param project_id:
        :param status:
        :param assignee_id:
        :param assignment_name:
        :return: Assignment object
        """
        if assignment_name:
            logger.warning('DEPRECATED - Param {} will be deprecated after v1.17.0'.format(assignment_name))
        if dataset:
            logger.warning('DEPRECATED - Param {} will be deprecated after v1.17.0'.format(dataset))
        if project_id:
            logger.warning('DEPRECATED - Param {} will be deprecated after v1.17.0'.format(project_id))
        if status:
            logger.warning('DEPRECATED - Param {} will be deprecated after v1.17.0'.format(status))
        if metadata:
            logger.warning('DEPRECATED - Param {} will be deprecated after v1.17.0'.format(metadata))

        return self._create_in_task(assignee_id=assignee_id, task=task, filters=filters, items=items)

    def _create_in_task(self, assignee_id, task, filters=None, items=None):

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

    def __item_operations(self, dataset, op, assignment_id=None, assignment_name=None, filters=None, items=None):
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
                filters = entities.Filters(field='id', values=[item.id for item in items], operator='in')

            filters._ref_assignment = True
            filters._ref_assignment_id = assignment_id
            filters._ref_op = op

            return dataset.items.update(filters=filters)
        finally:
            if filters is not None:
                filters._nullify_refs()

    def assign_items(self, dataset, assignment_id=None, assignment_name=None, filters=None, items=None):
        """

        :param assignment_name:
        :param filters:
        :param assignment_id:
        :param dataset:
        :param items:
        :return:
        """
        return self.__item_operations(dataset=dataset, assignment_id=assignment_id, filters=filters, items=items,
                                      op='create', assignment_name=assignment_name)

    def remove_items(self, dataset, assignment_id=None, assignment_name=None, filters=None, items=None):
        """

        :param assignment_name:
        :param assignment_id:
        :param dataset:
        :param filters:
        :param items:
        :return:
        """
        return self.__item_operations(dataset=dataset, assignment_id=assignment_id, filters=filters, items=items,
                                      op='delete', assignment_name=assignment_name)

    def get_items(self, assignment=None, assignment_id=None, assignment_name=None, dataset=None, filters=None):
        """

        :param filters:
        :param assignment:
        :param dataset:
        :param assignment_id:
        :param assignment_name:
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
            filters = entities.Filters()
        filters.add(field='metadata.system.refs.id', values=[assignment_id], operator='in')

        return dataset.items.list(filters=filters)
