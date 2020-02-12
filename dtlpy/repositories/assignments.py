import logging

from .. import exceptions, miscellaneous, entities

logger = logging.getLogger(name=__name__)


class Assignments:
    """
    Assignments repository
    """

    def __init__(self, client_api, project=None, task=None, dataset=None):
        self._client_api = client_api
        self._project = project
        self._dataset = dataset
        self._task = task

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
    def list(self, project_ids=None, status=None, name=None, annotator=None, pages_size=None, page_offset=None):
        """
        Get Assignments list

        :param page_offset:
        :param pages_size:
        :param annotator:
        :param name:
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
        elif self.project is not None:
            project_ids = [self.project.id]
        else:
            raise ('400', 'Must provide project')
        project_ids = ','.join(project_ids)
        query.append('projects={}'.format(project_ids))

        if status is not None:
            query.append('status={}'.format(status))
        if name is not None:
            query.append('name={}'.format(name))
        if annotator is not None:
            query.append('annotator={}'.format(annotator))
        if pages_size is not None:
            query.append('pageSize={}'.format(pages_size))
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))

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
            logger.exception('Platform error getting assignments')
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

    def create(self, name, annotator, dataset, status=None, project_id=None, metadata=None, filters=None, items=None):
        """
        Create a new assignment
        :param dataset:
        :param items:
        :param filters:
        :param metadata:
        :param project_id:
        :param status:
        :param annotator:
        :param name:
        :return: Assignment object
        """

        if filters is None and items is None:
            raise exceptions.PlatformException('400', 'Must provide either filters or items list')

        payload = {'name': name,
                   'annotator': annotator}

        if status is not None:
            payload['status'] = status
        if project_id is not None:
            payload['projectId'] = project_id
        if metadata is None:
            metadata = dict()
        metadata['system'] = {'datasetId': dataset.id}
        payload['metadata'] = metadata

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/assignments',
                                                         json_req=payload)
        if success:
            assignment = entities.Assignment.from_json(client_api=self._client_api,
                                                       _json=response.json(), project=self._project,
                                                       dataset=self._dataset, task=self._task)
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(assignment, entities.Assignment)

        self.assign_items(dataset=dataset, assignment_id=assignment.id, filters=filters, items=items)

        return assignment

    def __item_operations(self, dataset, op, assignment_id=None, assignment_name=None, filters=None, items=None):
        if assignment_id is None and assignment_name is None:
            raise exceptions.PlatformException('400', 'Must provide either assignment name or assignment id')
        elif assignment_id is None:
            assignment_id = self.get(assignment_name=assignment_name).id

        try:
            if filters is None and items is None:
                raise exceptions.PlatformException('400', 'Must provide either filters or items list')

            if filters is None:
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

    def get_items(self, assignment_id=None, assignment_name=None, dataset=None):
        """

        :param dataset:
        :param assignment_id:
        :param assignment_name:
        :return:
        """
        if assignment_id is None and assignment_name is None:
            raise exceptions.PlatformException('400', 'Please provide either assignment_id or assignment_name')

        if assignment_id is None:
            assignment_id = self.get(assignment_name=assignment_name).id

        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide a dataset entity')

        if dataset is None:
            dataset = self._dataset

        filters = entities.Filters(field='metadata.system.refs.id', values=assignment_id, operator='in')
        return dataset.items.list(filters=filters)
