import datetime
import logging
import json
from typing import Union, List

from .. import exceptions, miscellaneous, entities, repositories, services

logger = logging.getLogger(name='dtlpy')
URL_PATH = '/annotationtasks'


class Tasks:
    """
    Tasks Repository

    The Tasks class allows the user to manage tasks and their properties. For more information, read in our SDK documentation about `Creating Tasks <https://dataloop.ai/docs/sdk-create-task>`_, `Redistributing and Reassigning Tasks <https://dataloop.ai/docs/sdk-redistribute-task>`_, and `Task Assignment <https://dataloop.ai/docs/sdk-task-assigment>`_.
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None,
                 project_id: str = None):
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
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.tasks repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.tasks repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @property
    def assignments(self) -> repositories.Assignments:
        if self._assignments is None:
            self._assignments = repositories.Assignments(client_api=self._client_api, project=self._project)
        assert isinstance(self._assignments, repositories.Assignments)
        return self._assignments

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Task]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]

        for i_task, task in enumerate(response_items):
            jobs[i_task] = pool.submit(
                entities.Task._protected_from_json,
                **{
                    'client_api': self._client_api,
                    '_json': task,
                    'project': self._project,
                    'dataset': self._dataset
                }
            )

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        tasks = miscellaneous.List([r[1] for r in results if r[0] is True])
        return tasks

    def _list(self, filters: entities.Filters):
        url = '{}/query'.format(URL_PATH)
        query = filters.prepare()
        query['context'] = dict(projectIds=[self._project_id])
        success, response = self._client_api.gen_request(
            req_type='post',
            path=url,
            json_req=filters.prepare()
        )

        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def query(self, filters=None, project_ids=None):
        """
        List all tasks by filter.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who has been assigned the task.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param list project_ids: list of project ids
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            dataset.tasks.query(project_ids='project_ids')
        """
        if project_ids is None:
            if self._project_id is not None:
                project_ids = self._project_id
            else:
                raise exceptions.PlatformException('400', 'Please provide param project_ids')

        if not isinstance(project_ids, list):
            project_ids = [project_ids]

        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.TASK)
        else:
            if not isinstance(filters, entities.Filters):
                raise exceptions.PlatformException('400', 'Unknown filters type')
            if filters.resource != entities.FiltersResource.TASK:
                raise exceptions.PlatformException('400', 'Filter resource must be task')

        if filters.context is None:
            filters.context = {'projectIds': project_ids}

        if self._project_id is not None:
            filters.add(field='projectId', values=self._project_id)

        if self._dataset is not None:
            filters.add(field='datasetId', values=self._dataset.id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       project_id=self._project_id,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    ###########
    # methods #
    ###########
    def list(
            self,
            project_ids=None,
            status=None,
            task_name=None,
            pages_size=None,
            page_offset=None,
            recipe=None,
            creator=None,
            assignments=None,
            min_date=None,
            max_date=None,
            filters: entities.Filters = None
    ) -> Union[miscellaneous.List[entities.Task], entities.PagedEntities]:
        """
        List all Annotation Tasks.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who has been assigned the task.

        :param project_ids: list of project ids
        :param str status: status
        :param str task_name: task name
        :param int pages_size: pages size
        :param int page_offset: page offset
        :param dtlpy.entities.recipe.Recipe recipe: recipe entity
        :param str creator: creator
        :param dtlpy.entities.assignment.Assignment recipe assignments: assignments entity
        :param double min_date: double min date
        :param double max_date: double max date
        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return: List of Annotation Task objects

        **Example**:

        .. code-block:: python

            dataset.tasks.list(project_ids='project_ids',pages_size=100, page_offset=0)
        """
        # url
        url = URL_PATH + '/query'

        if filters is None:
            filters = entities.Filters(use_defaults=False, resource=entities.FiltersResource.TASK)
        else:
            return self.query(filters=filters, project_ids=project_ids)

        if self._dataset is not None:
            filters.add(field='datasetId', values=self._dataset.id)

        if project_ids is not None:
            if not isinstance(project_ids, list):
                project_ids = [project_ids]
        elif self._project_id is not None:
            project_ids = [self._project_id]
        else:
            raise ('400', 'Must provide project')
        filters.context = {"projectIds": project_ids}

        if assignments is not None:
            if not isinstance(assignments, list):
                assignments = [assignments]
            assignments = [
                assignments_entity.id if isinstance(assignments_entity, entities.Assignment) else assignments_entity
                for assignments_entity in assignments]
            filters.add(field='assignmentIds', values=assignments, operator=entities.FiltersOperations.IN)
        if status is not None:
            filters.add(field='status', values=status)
        if task_name is not None:
            filters.add(field='name', values=task_name)
        if pages_size is not None:
            filters.page_size = pages_size
        if pages_size is None:
            filters.page_size = 500
        if page_offset is not None:
            filters.page = page_offset
        if recipe is not None:
            if not isinstance(recipe, list):
                recipe = [recipe]
            recipe = [recipe_entity.id if isinstance(recipe_entity, entities.Recipe) else recipe_entity
                      for recipe_entity in recipe]
            filters.add(field='recipeId', values=recipe, operator=entities.FiltersOperations.IN)
        if creator is not None:
            filters.add(field='creator', values=creator)
        if min_date is not None:
            filters.add(field='dueDate', values=min_date, operator=entities.FiltersOperations.GREATER_THAN)
        if max_date is not None:
            filters.add(field='dueDate', values=max_date, operator=entities.FiltersOperations.LESS_THAN)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=filters.prepare())
        if success:
            tasks = miscellaneous.List(
                [entities.Task.from_json(client_api=self._client_api,
                                         _json=_json, project=self._project, dataset=self._dataset)
                 for _json in response.json()['items']])
            logger.warning('Deprecation Warning - return type will be pageEntity from version 1.46.0 not a list')
        else:
            logger.error('Platform error getting annotation task')
            raise exceptions.PlatformException(response)

        return tasks

    def get(self, task_name=None, task_id=None) -> entities.Task:
        """
        Get an Annotation Task object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who has been assigned the task.

        :param str task_name: optional - search by name
        :param str task_id: optional - search by id
        :return: task object
        :rtype: dtlpy.entities.task.Task

        **Example**:

        .. code-block:: python

            dataset.tasks.get(task_id='task_id')
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
            # verify input task name is same as the given id
            if task_name is not None and task.name != task_name:
                logger.warning(
                    "Mismatch found in tasks.get: task_name is different then task.name:"
                    " {!r} != {!r}".format(
                        task_name,
                        task.name))
        elif task_name is not None:
            tasks = self.list(filters=entities.Filters(field='name',
                                                       values=task_name,
                                                       resource=entities.FiltersResource.TASK))
            if tasks.items_count == 0:
                raise exceptions.PlatformException('404', 'Annotation task not found')
            elif tasks.items_count > 1:
                raise exceptions.PlatformException('404',
                                                   'More than one Annotation task exist with the same name: {}'.format(
                                                       task_name))
            else:
                task = tasks[0][0]
        else:
            raise exceptions.PlatformException('400', 'Must provide either Annotation task name or Annotation task id')

        assert isinstance(task, entities.Task)
        return task

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/tasks".format(self.project.id))

    def open_in_web(self,
                    task_name: str = None,
                    task_id: str = None,
                    task: entities.Task = None):
        """
        Open the task in the web platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who has been assigned the task.

        :param str task_name: task name
        :param str task_id: task id
        :param dtlpy.entities.task.Task task: task entity

        **Example**:

        .. code-block:: python

            dataset.tasks.open_in_web(task_id='task_id')
        """
        if task_name is not None:
            task = self.get(task_name=task_name)
        if task is not None:
            task.open_in_web()
        elif task_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(task_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def delete(self,
               task: entities.Task = None,
               task_name: str = None,
               task_id: str = None,
               wait: bool = True):
        """
        Delete an Annotation Task.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who created that task.

        :param dtlpy.entities.task.Task task: task entity
        :param str task_name: task name
        :param str task_id: task id
        :param bool wait: wait for the command to finish
        :return: True is success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.tasks.delete(task_id='task_id')
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
                                                         path=url,
                                                         json_req={'asynced': wait})

        if not success:
            raise exceptions.PlatformException(response)
        response_json = response.json()
        command = entities.Command.from_json(_json=response_json,
                                             client_api=self._client_api)
        if not wait:
            return command
        command = command.wait(timeout=0)
        if 'deleteTaskId' not in command.spec:
            raise exceptions.PlatformException(error='400',
                                               message="deleteTaskId key is missing in command response: {}"
                                               .format(response))
        return True

    def update(self,
               task: entities.Task = None,
               system_metadata=False
               ) -> entities.Task:
        """
        Update an Annotation Task.

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who created that task.

        :param dtlpy.entities.task.Task task: task entity
        :param bool system_metadata: True, if you want to change metadata system
        :return: Annotation Task object
        :rtype: dtlpy.entities.task.Task

        **Example**:

        .. code-block:: python

            dataset.tasks.update(task='task_entity')
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

    def create_qa_task(self,
                       task: entities.Task,
                       assignee_ids,
                       due_date=None,
                       filters=None,
                       items=None,
                       query=None,
                       workload=None,
                       metadata=None,
                       available_actions=None,
                       wait=True,
                       batch_size=None,
                       max_batch_workload=None,
                       allowed_assignees=None,
                       ) -> entities.Task:
        """
        Create a new QA Task.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        :param dtlpy.entities.task.Task task: parent task
        :param list assignee_ids: list of assignee
        :param float due_date: date by which the task should be finished; for example, due_date = datetime.datetime(day= 1, month= 1, year= 2029).timestamp()
        :param entities.Filters filters: filter to the task
        :param List[entities.Item] items: item to insert to the task
        :param entities.Filters query: filter to the task
        :param List[WorkloadUnit] workload: list WorkloadUnit for the task assignee
        :param dict metadata: metadata for the task
        :param list available_actions: list of available actions to the task
        :param bool wait: wait for the command to finish
        :param int batch_size: Pulling batch size (items) . Restrictions - Min 3, max 100
        :param int max_batch_workload: Max items in assignment . Restrictions - Min batchSize + 2 , max batchSize * 2
        :param list allowed_assignees:  It’s like the workload, but without percentage.
        :return: task object
        :rtype: dtlpy.entities.task.Task

        **Example**:

        .. code-block:: python

            dataset.tasks.create_qa_task(task= 'task_entity',
                                        due_date = datetime.datetime(day= 1, month= 1, year= 2029).timestamp(),
                                        assignee_ids =[ 'annotator1@dataloop.ai', 'annotator2@dataloop.ai'])
        """
        source_filter = entities.filters.SingleFilter(
            field='metadata.system.refs',
            values={
                "id": task.id,
                "type": "task",
                "metadata":
                    {
                        "status":
                            {
                                "$exists": True
                            }
                    }
            },
            operator=entities.FiltersOperations.MATCH
        )

        if query is not None:
            and_list = query.get('filter', query).get('$and', None)
            if and_list is not None:
                and_list.append(source_filter.prepare())
            else:
                if 'filter' not in query:
                    query['filter'] = {}
                query['filter']['$and'] = [source_filter.prepare()]

        else:
            if filters is None and items is None:
                filters = entities.Filters()
            if filters:
                filters.and_filter_list.append(source_filter)

        return self.create(task_name='{}_qa'.format(task.name),
                           task_type='qa',
                           task_parent_id=task.id,
                           assignee_ids=assignee_ids,
                           workload=workload,
                           task_owner=task.creator,
                           project_id=task.project_id,
                           recipe_id=task.recipe_id,
                           due_date=due_date,
                           filters=filters,
                           items=items,
                           query=query,
                           metadata=metadata,
                           available_actions=available_actions,
                           wait=wait,
                           batch_size=batch_size,
                           max_batch_workload=max_batch_workload,
                           allowed_assignees=allowed_assignees,
                           )

    def create(self,
               task_name,
               due_date=None,
               assignee_ids=None,
               workload=None,
               dataset=None,
               task_owner=None,
               task_type='annotation',
               task_parent_id=None,
               project_id=None,
               recipe_id=None,
               assignments_ids=None,
               metadata=None,
               filters=None,
               items=None,
               query=None,
               available_actions=None,
               wait=True,
               check_if_exist: entities.Filters = False,
               limit=None,
               batch_size=None,
               max_batch_workload=None,
               allowed_assignees=None,
               ) -> entities.Task:
        """
        Create a new Annotation Task.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        :param str task_name: task name
        :param float due_date: date by which the task should be finished; for example, due_date = datetime.datetime(day= 1, month= 1, year= 2029).timestamp()
        :param list assignee_ids: list of assignee
        :param List[WorkloadUnit] workload: list WorkloadUnit for the task assignee
        :param entities.Dataset dataset: dataset entity
        :param str task_owner: task owner
        :param str task_type: "annotation" or "qa"
        :param str task_parent_id: optional if type is qa - parent task id
        :param str project_id: project id
        :param str recipe_id: recipe id
        :param list assignments_ids: assignments ids
        :param dict metadata: metadata for the task
        :param entities.Filters filters: filter to the task
        :param List[entities.Item] items: item to insert to the task
        :param entities.Filters query: filter to the task
        :param list available_actions: list of available actions to the task
        :param bool wait: wait for the command to finish
        :param entities.Filters check_if_exist: dl.Filters check if task exist according to filter
        :param int limit: task limit
        :param int batch_size: Pulling batch size (items) . Restrictions - Min 3, max 100
        :param int max_batch_workload: Max items in assignment . Restrictions - Min batchSize + 2 , max batchSize * 2
        :param list allowed_assignees:  It’s like the workload, but without percentage.
        :return: Annotation Task object
        :rtype: dtlpy.entities.task.Task

        **Example**:

        .. code-block:: python

            dataset.tasks.create(task= 'task_entity',
                                due_date = datetime.datetime(day= 1, month= 1, year= 2029).timestamp(),
                                assignee_ids =[ 'annotator1@dataloop.ai', 'annotator2@dataloop.ai'])
        """

        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide param dataset')
        if due_date is None:
            due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).timestamp()
        if query is None:
            if filters is None and items is None:
                query = entities.Filters().prepare()
            elif filters is None:
                if not isinstance(items, list):
                    items = [items]
                query = entities.Filters(field='id',
                                         values=[item.id for item in items],
                                         operator=entities.FiltersOperations.IN,
                                         use_defaults=False).prepare()
            else:
                query = filters.prepare()

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

        if workload is None and assignee_ids is not None:
            workload = entities.Workload.generate(assignee_ids=assignee_ids)

        if assignments_ids is None:
            assignments_ids = list()

        payload = {'name': task_name,
                   'query': "{}".format(json.dumps(query).replace("'", '"')),
                   'taskOwner': task_owner,
                   'spec': {'type': task_type},
                   'datasetId': dataset.id,
                   'projectId': project_id,
                   'assignmentIds': assignments_ids,
                   'recipeId': recipe_id,
                   'dueDate': due_date * 1000,
                   'asynced': wait}

        if check_if_exist:
            if check_if_exist.resource != entities.FiltersResource.TASK:
                raise exceptions.PlatformException(
                    '407', 'Filter resource for check_if_exist param must be {}, got {}'.format(
                        entities.FiltersResource.TASK, check_if_exist.resource
                    )
                )
            payload['checkIfExist'] = {'query': check_if_exist.prepare()}

        if workload:
            payload['workload'] = workload.to_json()

        if limit:
            payload['limit'] = limit

        if available_actions is not None:
            payload['availableActions'] = [action.to_json() for action in available_actions]

        if task_parent_id is not None:
            payload['spec']['parentTaskId'] = task_parent_id

        if batch_size is not None or allowed_assignees is not None or max_batch_workload is not None:
            if metadata is None:
                metadata = {}
            if 'system' not in metadata:
                metadata['system'] = {}
            if batch_size is not None:
                metadata['system']['batchSize'] = batch_size
            if max_batch_workload is not None:
                metadata['system']['maxBatchWorkload'] = max_batch_workload
            if allowed_assignees is not None:
                metadata['system']['allowedAssignees'] = allowed_assignees

        if metadata is not None:
            payload['metadata'] = metadata

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=URL_PATH,
                                                         json_req=payload)
        if success:

            response_json = response.json()
            if check_if_exist is not None and 'name' in response_json:
                return entities.Task.from_json(
                    _json=response.json(),
                    client_api=self._client_api,
                    project=self._project,
                    dataset=self._dataset
                )

            command = entities.Command.from_json(_json=response_json,
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if 'createTaskPayload' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="createTaskPayload key is missing in command response: {}"
                                                   .format(response))
            task = self.get(task_id=command.spec['createdTaskId'])
        else:
            raise exceptions.PlatformException(response)

        assert isinstance(task, entities.Task)
        return task

    def __item_operations(self, dataset: entities.Dataset, op, task=None, task_id=None, filters=None, items=None):

        if task is None and task_id is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task id')
        elif task_id is None:
            task_id = task.id

        try:
            if filters is None and items is None:
                raise exceptions.PlatformException('400', 'Must provide either filters or items list')

            if filters is None:
                filters = entities.Filters(field='id',
                                           values=[item.id for item in items],
                                           operator=entities.FiltersOperations.IN,
                                           use_defaults=False)

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

    def add_items(self,
                  task: entities.Task = None,
                  task_id=None,
                  filters: entities.Filters = None,
                  items=None,
                  assignee_ids=None,
                  query=None,
                  workload=None,
                  limit=None,
                  wait=True) -> entities.Task:
        """
        Add items to a Task.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        :param dtlpy.entities.task.Task task: task entity
        :param str task_id: task id
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param list items: list of items to add to the task
        :param list assignee_ids: list to assignee who works in the task
        :param dict query: query to filter the items use it
        :param list workload: list of the work load ber assignee and work load
        :param int limit: task limit
        :param bool wait: wait for the command to finish
        :return: task entity
        :rtype: dtlpy.entities.task.Task

        **Example**:

        .. code-block:: python

            dataset.tasks.add_items(task= 'task_entity',
                                items = [items])
        """
        if filters is None and items is None and query is None:
            raise exceptions.PlatformException('400', 'Must provide either filters, query or items list')

        if task is None and task_id is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task_id')

        if query is None:
            if filters is None:
                if not isinstance(items, list):
                    items = [items]
                filters = entities.Filters(field='id',
                                           values=[item.id for item in items],
                                           operator=entities.FiltersOperations.IN,
                                           use_defaults=False)
            query = filters.prepare()

        if workload is None and assignee_ids is not None:
            workload = entities.Workload.generate(assignee_ids=assignee_ids)

        if task_id is None:
            task_id = task.id

        payload = {
            "query": "{}".format(json.dumps(query).replace("'", '"')),
        }

        if workload is not None:
            payload["workload"] = workload.to_json()

        if limit is not None:
            payload['limit'] = limit

        payload['asynced'] = wait

        url = '{}/{}/addToTask'.format(URL_PATH, task_id)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)

        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if task is None:
                task = self.get(task_id=task_id)
            if 'addToTaskPayload' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="addToTaskPayload key is missing in command response: {}"
                                                   .format(response))
        else:
            raise exceptions.PlatformException(response)

        assert isinstance(task, entities.Task)
        return task

    def remove_items(self,
                     task: entities.Task = None,
                     task_id=None,
                     filters: entities.Filters = None,
                     query=None,
                     items=None,
                     wait=True):
        """
        remove items from Task.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        :param dtlpy.entities.task.Task task: task entity
        :param str task_id: task id
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param dict query: query yo filter the items use it
        :param list items: list of items to add to the task
        :param bool wait: wait for the command to finish
        :return: True if success and an error if failed
        :rtype: bool

        **Examples**:

        .. code-block:: python

            dataset.tasks.remove_items(task= 'task_entity',
                                        items = [items])

        """
        if filters is None and items is None and query is None:
            raise exceptions.PlatformException('400', 'Must provide either filters, query or items list')

        if task is None and task_id is None:
            raise exceptions.PlatformException('400', 'Must provide either task or task_id')

        if query is None:
            if filters is None:
                if not isinstance(items, list):
                    items = [items]
                filters = entities.Filters(field='id',
                                           values=[item.id for item in items],
                                           operator=entities.FiltersOperations.IN,
                                           use_defaults=False)
            query = filters.prepare()

        if task_id is None:
            task_id = task.id

        payload = {"query": "{}".format(json.dumps(query).replace("'", '"')), 'asynced': wait}

        url = '{}/{}/removeFromTask'.format(URL_PATH, task_id)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)

        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)

            if 'removeFromTaskId' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="removeFromTaskId key is missing in command response: {}"
                                                   .format(response))
        else:
            raise exceptions.PlatformException(response)
        return True

    def get_items(self,
                  task_id: str = None,
                  task_name: str = None,
                  dataset: entities.Dataset = None,
                  filters: entities.Filters = None) -> entities.PagedEntities:
        """
        Get the task items to use in your code.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        If a filters param is provided, you will receive a PagedEntity output of the task items. If no filter is provided, you will receive a list of the items.

        :param str task_id: task id
        :param str task_name: task name
        :param dtlpy.entities.dataset.Dataset dataset: dataset entity
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: list of the items or PagedEntity output of items
        :rtype: list or dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            dataset.tasks.get_items(task_id= 'task_id')
        """
        if task_id is None and task_name is None:
            raise exceptions.PlatformException('400', 'Please provide either task_id or task_name')
        if task_id is None:
            task_id = self.get(task_name=task_name).id

        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide a dataset entity')
        if dataset is None:
            dataset = self._dataset

        if filters is None:
            filters = entities.Filters(use_defaults=False)
        filters.add(field='metadata.system.refs.id', values=[task_id], operator=entities.FiltersOperations.IN)

        return dataset.items.list(filters=filters)

    def set_status(self, status: str, operation: str, task_id: str, item_ids: List[str]):
        """
        Update an item status within a task.

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned to be *owner* of the annotation task.

        :param str status: string the describes the status
        :param str operation:  'create' or 'delete'
        :param str task_id: task id
        :param list item_ids: List[str] id items ids
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.tasks.set_status(task_id= 'task_id', status='complete', operation='create')
        """
        url = '/assignments/items/tasks/{task_id}/status'.format(task_id=task_id)
        payload = {
            'itemIds': item_ids,
            'statusPayload': {
                'operation': operation,
                'status': status
            }
        }

        success, response = self._client_api.gen_request(
            req_type='post',
            path=url,
            json_req=payload
        )

        if not success:
            raise exceptions.PlatformException(response)

        return True
