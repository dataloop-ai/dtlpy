import logging
from .. import exceptions, miscellaneous, entities, repositories

logger = logging.getLogger(name=__name__)
URL_PATH = '/annotationtasks'


class Tasks:
    """
    Tasks repository
    """

    def __init__(self, client_api, project=None, dataset=None):
        self._client_api = client_api
        self._project = project
        self._dataset = dataset
        self._assignments = None

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.tasks repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def dataset(self):
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.tasks repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @property
    def assignments(self):
        if self._assignments is None:
            self._assignments = repositories.Assignments(client_api=self._client_api, project=self._project)
        assert isinstance(self._assignments, repositories.Assignments)
        return self._assignments

    ###########
    # methods #
    ###########
    def list(self,
             project_ids=None,
             status=None,
             name=None,
             pages_size=None,
             page_offset=None,
             recipe=None,
             creator=None,
             assignments=None,
             min_date=None,
             max_date=None):
        """
        Get Annotation Task list

        :param name:
        :param project_ids: list of project ids
        :param assignments:
        :param creator:
        :param page_offset:
        :param pages_size:
        :param recipe:
        :param status:
        :param max_date: double
        :param min_date:double
        :return: List of Annotation Task objects
        """

        # url
        url = URL_PATH

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

        if assignments is not None:
            if not isinstance(assignments, list):
                assignments = [assignments]
            assignments = ','.join(assignments)
            query.append('assignments={}'.format(assignments))
        if status is not None:
            query.append('status={}'.format(status))
        if name is not None:
            query.append('name={}'.format(name))
        if pages_size is not None:
            query.append('pageSize={}'.format(pages_size))
        if page_offset is not None:
            query.append('pageOffset={}'.format(page_offset))
        if recipe is not None:
            query.append('recipe={}'.format(recipe))
        if creator is not None:
            query.append('creator={}'.format(creator))
        if min_date is not None:
            query.append('minDate={}'.format(min_date))
        if max_date is not None:
            query.append('maxDate={}'.format(max_date))

        if len(query) > 0:
            query_string = '&'.join(query)
            url = '{}?{}'.format(url, query_string)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            tasks = miscellaneous.List(
                [entities.Task.from_json(client_api=self._client_api,
                                         _json=_json, project=self._project, dataset=self._dataset)
                 for _json in response.json()['items']])
        else:
            logger.exception('Platform error getting annotation task')
            raise exceptions.PlatformException(response)

        return tasks

    def get(self, task_name=None, task_id=None):
        """
        Get an Annotation Task object
        :param task_name: optional - search by name
        :param task_id: optional - search by id
        :return: task_id object

        """

        # url
        url = URL_PATH

        if task_id is not None:
            url = '{}/{}'.format(url, task_id)
            success, response = self._client_api.gen_request(req_type='get',
                                                             path=url)
            if not success:
                raise exceptions.PlatformException('404', 'Annotation task not found')
            else:
                task = entities.Task.from_json(_json=response.json(),
                                               client_api=self._client_api, project=self._project,
                                               dataset=self._dataset)
        elif task_name is not None:
            tasks = [task for task in self.list() if
                     task.name == task_name]
            if len(tasks) == 0:
                raise exceptions.PlatformException('404', 'Annotation task not found')
            elif len(tasks) > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one Annotation task exist with the same name: {}'.format(
                                                       task_name))
            else:
                task = tasks[0]
        else:
            raise exceptions.PlatformException('400', 'Must provide either Annotation task name or Annotation task id')

        assert isinstance(task, entities.Task)
        return task

    def delete(self, task=None, task_name=None, task_id=None):
        """
        Delete an Annotation Task
        :param task_id:
        :param task_name:
        :param task:

        :return: True
        """
        if task_id is None:
            if task is None:
                if task_name is None:
                    raise exceptions.PlatformException('400',
                                                       'Must provide either annotation task, '
                                                       'annotation task name or annotation task id')
                else:
                    task = self.get(task_name=task_name)
                    task_id = task.id

        url = URL_PATH
        url = '{}/{}'.format(url, task_id)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=url)

        if not success:
            raise exceptions.PlatformException(response)
        return True

    def update(self, task=None, system_metadata=False):
        """
        Update an Annotation Task
        :return: Annotation Task object
        """
        url = URL_PATH
        url = '{}/{}'.format(url, task.id)

        if system_metadata:
            url += '?system=true'

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url,
                                                         json_req=task.to_json())
        if success:
            return entities.Task.from_json(_json=response.json(),
                                           client_api=self._client_api, project=self._project, dataset=self._dataset)
        else:
            raise exceptions.PlatformException(response)

    def create_qa_task(self, task, assignees):
        if isinstance(task, entities.Task):
            raise ValueError('task must be of type "Task". got: {}'.format(type(task)))
        return self.create(task_name='{}_qa'.format(task.name),
                           task_type='qa',
                           task_parent_id=task.id,
                           assignees=assignees,
                           task_owner=task.creator,
                           project_id=task.project_id,
                           recipe_id=task.recipeId)

    def create(self, task_name, assignees=None, dataset=None, task_owner=None, status=None,
               task_type='annotation', task_parent_id=None,
               project_id=None,
               recipe_id=None, assignments_ids=None, query=None, due_date=None, filters=None, items=None):
        """
        Create a new Annotation Task

        :param task_name:
        :param assignees:
        :param dataset:
        :param task_owner:
        :param items:
        :param filters:
        :param assignments_ids:
        :param recipe_id:
        :param due_date:
        :param query:
        :param project_id:
        :param status:
        :param task_name:
        :param task_type: "annotation" or "qa"
        :param task_parent_id: optional if type is qa - parent task id
        :return: Annotation Task object
        """
        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide param dataset')

        if dataset is None:
            dataset = self._dataset

        if task_owner is None:
            task_owner = self._client_api.info()['user_email']

        if task_type not in ['annotation', 'qa']:
            raise ValueError('task_type must be one of: "annotation", "qa". got: {}'.format(task_type))

        payload = {'name': task_name,
                   'taskOwner': task_owner,
                   'spec': {'type': task_type},
                   'datasetId': dataset.id}

        if task_parent_id is not None:
            payload['spec']['parentTaskId'] = task_parent_id

        if status is not None:
            payload['status'] = status
        else:
            payload['status'] = 'open'

        if project_id is None:
            if self._project is not None:
                project_id = self._project.id
            else:
                project_id = dataset.project[0]

        payload['projectId'] = project_id

        if recipe_id is not None:
            payload['recipeId'] = recipe_id

        if query is not None:
            payload['query'] = query
        else:
            payload['query'] = '{}'

        if due_date is not None:
            payload['dueDate'] = due_date
        else:
            payload['dueDate'] = 0

        assignments = list()
        if (filters is not None or items is not None) and assignees is not None:
            assignments = self.__create_assignments(name=task_name, filters=filters, items=items, dataset=dataset,
                                                    assignees=assignees, project_id=project_id)
            assignments_ids = [assignment.id for assignment in assignments]
        elif assignments_ids is not None and not isinstance(assignments_ids, list):
            assignments_ids = [assignments_ids]
        else:
            assignments_ids = list()

        payload['assignmentIds'] = assignments_ids

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=URL_PATH,
                                                         json_req=payload)
        if success:
            task = entities.Task.from_json(client_api=self._client_api,
                                           _json=response.json(),
                                           project=self._project,
                                           dataset=self._dataset)
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(task, entities.Task)

        if filters is not None or items is not None:
            self.add_items(dataset=dataset, filters=filters, items=items, task_id=task.id)

        self.__assign(assignments=assignments, task_id=task.id)

        return task

    def __assign(self, assignments, task_id):
        for assignment in assignments:
            assignment.metadata['system']['taskId'] = task_id
            self.assignments.update(assignment=assignment)

    def __item_operations(self, dataset, op, task=None, task_id=None, filters=None, items=None):

        if task is None and task_id is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task id')
        elif task_id is None:
            task_id = task.id

        try:
            if filters is None and items is None:
                raise exceptions.PlatformException('400', 'Must provide either filters or items list')

            if filters is None:
                filters = entities.Filters(field='id', values=[item.id for item in items], operator='in')

            if op == 'delete':
                if task is None:
                    task = self.get(task_id=task_id)
                assignment_ids = task.assignmentIds
                filters._ref_assignment = True
                filters._ref_assignment_id = assignment_ids

            filters._ref_task = True
            filters._ref_task_id = task_id
            filters._ref_op = op
            return dataset.items.update(filters=filters)
        finally:
            if filters is not None:
                filters._nullify_refs()

    def add_items(self, dataset, task=None, task_id=None, filters=None, items=None):
        """

        :param task:
        :param filters:
        :param task_id:
        :param dataset:
        :param items:
        :return:
        """

        return self.__item_operations(dataset=dataset, task_id=task_id, task=task, filters=filters, items=items,
                                      op='create')

    def remove_items(self, dataset, task=None, task_id=None, filters=None, items=None):
        """

        :param task:
        :param filters:
        :param task_id:
        :param dataset:
        :param items:
        :return:
        """
        return self.__item_operations(dataset=dataset, task_id=task_id, task=task, filters=filters, items=items,
                                      op='delete')

    def get_items(self, task_id=None, task_name=None, dataset=None):
        """

        :param dataset:
        :param task_id:
        :param task_name:
        :return:
        """
        if task_id is None and task_name is None:
            raise exceptions.PlatformException('400', 'Please provide either task_id or task_name')
        if task_id is None:
            task_id = self.get(task_name=task_name).id

        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide a dataset entity')
        if dataset is None:
            dataset = self._dataset

        filters = entities.Filters(field='metadata.system.refs.id', values=[task_id], operator='in')
        return dataset.items.list(filters=filters)

    def __create_assignment(self, name, assignee, dataset=None, project_id=None, items=None, filters=None):
        if filters is None and items is None:
            raise exceptions.PlatformException('400', 'Must provide either filters or items list')
        return self.assignments.create(assignment_name=name, annotator=assignee, project_id=project_id, filters=filters,
                                       items=items, dataset=dataset)

    @staticmethod
    def __generate_filter(filters, first_id, last_id, last_page):
        _json = filters.prepare()['filter']
        or_list = [{"id": first_id}, {"id": {"$gt": first_id, "$lt": last_id}}]

        if last_page:
            or_list.append({"id": last_id})

        if '$and' not in _json:
            _json['$and'] = list()

        _json['$and'].append({'$or': or_list})

        return _json

    def __create_assignments(self, name, dataset, assignees, project_id, filters=None, items=None):
        num_assignments = len(assignees)
        assignments = {assignee: None for assignee in
                       assignees}

        if filters is not None:
            filters.sort_by(field='id')
            filtered_items = dataset.items.list(filters=filters)
            if filtered_items.items_count == 0:
                return
            items_per_assignment = (filtered_items.items_count / num_assignments)
            filters.page_size = 1
            filters.page = filtered_items.items_count - 1
            previous_item_id = dataset.items.list(filters=filters).items[-1].id
            last_page = True
            for i_assignment, assignment in enumerate(reversed(list(assignments.keys()))):
                filters.page = max(filters.page - int(items_per_assignment), 0)
                first_item_id = dataset.items.list(filters=filters).items[0].id
                assignment_filters = entities.Filters()
                assignment_filters.custom_filter = self.__generate_filter(filters=filters, first_id=first_item_id,
                                                                          last_id=previous_item_id, last_page=last_page)

                if last_page:
                    last_page = False

                previous_item_id = first_item_id
                assignment_name = '{} ({})'.format(name, i_assignment)
                assignments[assignment] = self.__create_assignment(name=assignment_name, dataset=dataset,
                                                                   assignee=assignment, project_id=project_id,
                                                                   filters=assignment_filters)
        else:
            items_per_assignment = int(len(items) / num_assignments)
            start = 0
            end = items_per_assignment
            for assignment in assignments:
                assignment_items = items[start:end]
                assignments[assignment] = self.__create_assignment(name=name, dataset=dataset,
                                                                   assignee=assignment, project_id=project_id,
                                                                   items=assignment_items)
                start = end
                end = end + items_per_assignment

        return list(assignments.values())
