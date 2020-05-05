import logging
import json
from .. import exceptions, miscellaneous, entities, repositories

logger = logging.getLogger(name=__name__)
URL_PATH = '/annotationtasks'


class Tasks:
    """
    Tasks repository
    """

    def __init__(self, client_api, project=None, dataset=None, project_id=None):
        self._client_api = client_api
        self._project = project
        self._dataset = dataset
        self._assignments = None
        if project_id is None:
            if self._project is not None:
                project_id = self._project.id
            elif self._dataset is not None:
                if self._dataset._project is not None:
                    project_id = self._dataset._project.id
                elif isinstance(self._dataset.projects, list) and len(self._dataset.projects) > 0:
                    project_id = self._dataset.projects[0]
        self._project_id = project_id

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
             task_name=None,
             pages_size=None,
             page_offset=None,
             recipe=None,
             creator=None,
             assignments=None,
             min_date=None,
             max_date=None):
        """
        Get Annotation Task list

        :param task_name:
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
        elif self._project_id is not None:
            project_ids = [self._project_id]
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
        if task_name is not None:
            query.append('name={}'.format(task_name))
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
            logger.error('Platform error getting annotation task')
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

    def create_qa_task(self, due_date, task, assignee_ids, filters=None, items=None, query=None):
        if filters is None and items is None and query is None:
            query = json.loads(task.query)
        return self.create(task_name='{}_qa'.format(task.name),
                           task_type='qa',
                           task_parent_id=task.id,
                           assignee_ids=assignee_ids,
                           task_owner=task.creator,
                           project_id=task.project_id,
                           recipe_id=task.recipe_id,
                           due_date=due_date,
                           filters=filters,
                           items=items,
                           query=query)

    def create(self,
               task_name,
               due_date,
               assignee_ids=None,
               workload=None,
               dataset=None,
               task_owner=None,
               status='open',
               task_type='annotation',
               task_parent_id=None,
               project_id=None,
               recipe_id=None,
               assignments_ids=None,
               metadata=None,
               filters=None,
               items=None,
               query=None):
        """
        Create a new Annotation Task

        :param query:
        :param metadata:
        :param assignee_ids:
        :param workload:
        :param dataset:
        :param task_owner:
        :param items:
        :param filters:
        :param assignments_ids:
        :param recipe_id:
        :param due_date:
        :param project_id:
        :param status:
        :param task_name:
        :param task_type: "annotation" or "qa"
        :param task_parent_id: optional if type is qa - parent task id
        :return: Annotation Task object
        """
        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide param dataset')

        if query is None:
            if filters is None and items is None:
                query = entities.Filters().prepare(query_only=True)
            elif filters is None:
                if not isinstance(items, list):
                    items = [items]
                query = entities.Filters(field='id',
                                         values=[item.id for item in items],
                                         operator='in').prepare(query_only=True)
            else:
                query = filters.prepare(query_only=True)

        if dataset is None:
            dataset = self._dataset

        if task_owner is None:
            task_owner = self._client_api.info()['user_email']

        if task_type not in ['annotation', 'qa']:
            raise ValueError('task_type must be one of: "annotation", "qa". got: {}'.format(task_type))

        if recipe_id is None:
            recipe_id = dataset.get_recipe_ids()[0]

        if project_id is None:
            if self._project_id is not None:
                project_id = self._project_id
            else:
                raise exceptions.PlatformException('400', 'Must provide a project id')

        if workload is None:
            if assignee_ids is None:
                raise exceptions.PlatformException('400', 'Must provide either workload or assignee_ids')
            else:
                workload = entities.Workload.generate(assignee_ids=assignee_ids)

        if assignments_ids is None:
            assignments_ids = list()

        payload = {'name': task_name,
                   'query': "{}".format(json.dumps(query).replace("'", '"')),
                   'taskOwner': task_owner,
                   'spec': {'type': task_type},
                   'datasetId': dataset.id,
                   'projectId': project_id,
                   'workload': workload.to_json(),
                   'assignmentIds': assignments_ids,
                   'recipeId': recipe_id,
                   'status': status,
                   'dueDate': due_date}

        if task_parent_id is not None:
            payload['spec']['parentTaskId'] = task_parent_id

        if metadata is not None:
            payload['metadata'] = metadata

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

    def add_items(self, task=None,
                  task_id=None, filters=None,
                  items=None, assignee_ids=None,
                  query=None, workload=None,
                  limit=None):
        """
        Add items to Task

        :param query:
        :param assignee_ids:
        :param limit:
        :param workload:
        :param task

        :param filters:
        :param task_id:
        :param items:
        :return:
        """
        if filters is None and items is None and query is None:
            raise exceptions.PlatformException('400', 'Must provide either filters, query or items list')

        if task is None and task_id is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task_id')

        if query is None:
            if filters is None:
                if not isinstance(items, list):
                    items = [items]
                filters = entities.Filters(field='id', values=[item.id for item in items], operator='in')
            query = filters.prepare(query_only=True)

        if workload is None:
            if assignee_ids is None:
                workload = entities.Workload()
            else:
                workload = entities.Workload.generate(assignee_ids=assignee_ids)

        if task_id is None:
            task_id = task.id

        payload = {
            "query": "{}".format(json.dumps(query).replace("'", '"')),
            "workload": workload.to_json()
        }

        if limit is not None:
            payload['limit'] = limit

        url = '{}/{}/addToTask'.format(URL_PATH, task_id)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)

        if success:
            task = entities.Task.from_json(client_api=self._client_api,
                                           _json=response.json(),
                                           project=self._project,
                                           dataset=self._dataset)
        else:
            raise exceptions.PlatformException(response)

        assert isinstance(task, entities.Task)
        return task

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

