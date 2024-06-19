import attr
import logging
from .. import repositories, exceptions, entities

logger = logging.getLogger(name='dtlpy')


@attr.s
class Assignment(entities.BaseEntity):
    """
    Assignment object
    """

    # platform
    name = attr.ib()
    annotator = attr.ib()
    status = attr.ib()
    project_id = attr.ib()
    metadata = attr.ib(repr=False)
    id = attr.ib()
    url = attr.ib(repr=False)
    updated_at = attr.ib(repr=False)
    updated_by = attr.ib(repr=False)
    task_id = attr.ib(repr=False)
    dataset_id = attr.ib(repr=False)
    annotation_status = attr.ib(repr=False)
    item_status = attr.ib(repr=False)
    total_items = attr.ib()
    for_review = attr.ib()
    issues = attr.ib()
    # sdk

    _client_api = attr.ib(repr=False)
    _task = attr.ib(default=None, repr=False)
    _assignments = attr.ib(default=None, repr=False)
    _project = attr.ib(default=None, repr=False)
    _dataset = attr.ib(default=None, repr=False)
    _datasets = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project=None, task=None, dataset=None):
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Assignment has been fetched from a project that is not belong to it')
                project = None

        metadata = _json.get('metadata', dict())
        dataset_id = metadata.get('datasetId', None)
        task_id = metadata.get('taskId', None)
        if dataset_id is None:
            system_metadata = metadata.get('system', dict())
            dataset_id = system_metadata.get('datasetId', None)
        if task_id is None:
            system_metadata = metadata.get('system', dict())
            task_id = system_metadata.get('taskId', None)

        assignment = cls(
            name=_json.get('name', None),
            annotator=_json.get('annotator', None),
            status=_json.get('status', None),
            project_id=_json.get('projectId', None),
            task_id=task_id,
            dataset_id=dataset_id,
            metadata=metadata,
            url=_json.get('url', None),
            id=_json['id'],
            updated_by=_json.get('updatedBy', None),
            updated_at=_json.get('updatedAt', None),
            client_api=client_api,
            project=project,
            dataset=dataset,
            task=task,
            annotation_status=_json.get('annotationStatus', None),
            item_status=_json.get('itemStatus', None),
            total_items=_json.get('totalItems', None),
            for_review=_json.get('forReview', None),
            issues=_json.get('issues', None)
        )

        if dataset is not None:
            if assignment.dataset_id != dataset.id:
                logger.warning('Assignment has been fetched from a dataset that is not belong to it')
                assignment._dataset = None

        if task is not None:
            if assignment.task_id != task.id:
                logger.warning('Assignment has been fetched from a task that is not belong to it')
                assignment._task = None

        return assignment

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/assignments/{}".format(self.project_id, self.id))

    @property
    def assignments(self):
        if self._assignments is None:
            self._assignments = repositories.Assignments(client_api=self._client_api,
                                                         project=self._project,
                                                         task=self._task,
                                                         dataset=self._dataset)
        assert isinstance(self._assignments, repositories.Assignments)
        return self._assignments

    @property
    def project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id,
                                                                                   fetch=None)

        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def datasets(self):
        if self._datasets is None:
            self._datasets = repositories.Datasets(client_api=self._client_api, project=self._project)
        assert isinstance(self._datasets, repositories.Datasets)
        return self._datasets

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.datasets.get(dataset_id=self.dataset_id)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def task(self):
        if self._task is None:
            self._task = self.project.tasks.get(task_id=self.task_id)
        assert isinstance(self._task, entities.Task)
        return self._task

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Assignment)._client_api,
                                                              attr.fields(Assignment)._project,
                                                              attr.fields(Assignment).project_id,
                                                              attr.fields(Assignment)._assignments,
                                                              attr.fields(Assignment)._dataset,
                                                              attr.fields(Assignment)._task,
                                                              attr.fields(Assignment).annotation_status,
                                                              attr.fields(Assignment).updated_at,
                                                              attr.fields(Assignment).updated_by,
                                                              attr.fields(Assignment).item_status,
                                                              attr.fields(Assignment).total_items,
                                                              attr.fields(Assignment).for_review,
                                                              attr.fields(Assignment).issues))

        _json['projectId'] = self.project_id
        return _json

    def update(self, system_metadata=False):
        """
        Update an assignment

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param bool system_metadata: True, if you want to change metadata system
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment assignment

        **Example**:

        .. code-block:: python

            assignment = assignment.update(system_metadata=False)
        """
        return self.assignments.update(assignment=self, system_metadata=system_metadata)

    def open_in_web(self):
        """
        Open the assignment in web platform

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :return:

        **Example**:

        .. code-block:: python

            assignment.open_in_web()
        """
        self._client_api._open_in_web(url=self.platform_url)

    def get_items(self, dataset=None, filters=None):
        """
        Get all the items in the assignment

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param dtlpy.entities.dataset.Dataset dataset: dataset object, the dataset that refer to the assignment
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: pages of the items
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            items = task.assignments.get_items()
        """
        if dataset is None:
            dataset = self.dataset

        return self.assignments.get_items(dataset=dataset, assignment=self, filters=filters)

    def reassign(self, assignee_id, wait=True):
        """
        Reassign an assignment

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param str assignee_id: the email of the user that want to assign the assignment
        :param bool wait: wait until reassign assignment finish
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment

        **Example**:

        .. code-block:: python

            assignment = assignment.reassign(assignee_ids='annotator1@dataloop.ai')
        """
        return self.assignments.reassign(assignment=self,
                                         task=self._task,
                                         task_id=self.metadata['system'].get('taskId'),
                                         assignee_id=assignee_id,
                                         wait=wait)

    def redistribute(self, workload, wait=True):
        """
        Redistribute an assignment

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param dtlpy.entities.assignment.Workload workload: list of WorkloadUnit objects. Customize distribution (percentage) between the task assignees. For example: [dl.WorkloadUnit(annotator@hi.com, 80), dl.WorkloadUnit(annotator2@hi.com, 20)]
        :param bool wait: wait until redistribute assignment finish
        :return: Assignment object
        :rtype: dtlpy.entities.assignment.Assignment assignment

        **Example**:

        .. code-block:: python

            assignment = assignment.redistribute(workload=dl.Workload([dl.WorkloadUnit(assignee_id="annotator1@dataloop.ai", load=50),
                                                         dl.WorkloadUnit(assignee_id="annotator2@dataloop.ai", load=50)]))
        """
        return self.assignments.redistribute(assignment=self,
                                             task=self._task,
                                             task_id=self.metadata['system'].get('taskId'),
                                             workload=workload,
                                             wait=wait)

    def set_status(self, status: str, operation: str, item_id: str):
        """
        Set item status within assignment

        **Prerequisites**: You must be in the role of an *owner*, *developer*, or *annotation manager* who has been assigned as *owner* of the annotation task.

        :param str status: string the describes the status
        :param str operation: the status action need 'create' or 'delete'
        :param str item_id: item id that want to set his status
        :return: True id success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = assignment.set_status(status='complete',
                                    operation='created',
                                    item_id='item_id')
        """
        return self.assignments.set_status(status=status, operation=operation, item_id=item_id, assignment_id=self.id)


@attr.s
class WorkloadUnit:
    """
    WorkloadUnit object
    """

    # platform
    assignee_id = attr.ib(type=str)
    load = attr.ib(type=float, default=0)

    # noinspection PyUnusedLocal
    @load.validator
    def check_load(self, attribute, value):
        if value < 0 or value > 100:
            raise exceptions.PlatformException('400', 'Value must be a number between 0 to 100')

    @classmethod
    def from_json(cls, _json):
        return cls(
            assignee_id=_json.get('assigneeId', None),
            load=_json.get('load', None)
        )

    def to_json(self):
        return {
            'assigneeId': self.assignee_id,
            'load': self.load
        }


@attr.s
class Workload:
    """
    Workload object
    """

    # platform
    workload = attr.ib(type=list)

    def __iter__(self):
        for w_l_u in self.workload:
            yield w_l_u

    @workload.default
    def set_workload(self):
        workload = list()
        return workload

    @classmethod
    def from_json(cls, _json):
        return cls(
            workload=[WorkloadUnit.from_json(workload_unit) for workload_unit in _json]
        )

    @staticmethod
    def _loads_are_correct(loads):
        return round(sum(loads)) == 100

    @staticmethod
    def _get_loads(num_assignees):
        loads = [0 for _ in range(num_assignees)]
        index = 0
        for i in range(10000):
            loads[index] += 1
            if index < num_assignees - 1:
                index += 1
            else:
                index = 0
        loads = [l / 100 for l in loads]
        return loads

    def _redistribute(self):
        load = self._get_loads(num_assignees=len(self.workload))
        for i_w_l, w_l in self.workload:
            w_l.load = load

    @classmethod
    def generate(cls, assignee_ids, loads=None):
        """
        generate the loads for the given assignee
        :param assignee_ids:
        :param loads:
        """
        if not isinstance(assignee_ids, list):
            assignee_ids = [assignee_ids]

        if loads is None:
            div = len(assignee_ids)
            loads = [100 // div + (1 if x < 100 % div else 0) for x in range(div)]
        else:
            if not isinstance(loads, list):
                loads = [loads]
            if not Workload._loads_are_correct(loads=loads):
                raise exceptions.PlatformException('400', 'Loads must summarized to 100')

        if len(assignee_ids) != len(loads):
            raise exceptions.PlatformException('400', 'Assignee ids and loads must be of same length')

        return cls(
            workload=[WorkloadUnit(assignee_id=assignee_id, load=loads[i_assignee_id]) for i_assignee_id, assignee_id in
                      enumerate(assignee_ids)])

    def to_json(self):
        return [workload_unit.to_json() for workload_unit in self.workload]

    def add(self, assignee_id):
        """
        add a assignee

        :param assignee_id:
        """
        self.workload.append(WorkloadUnit(assignee_id=assignee_id))
        if not self._loads_are_correct(loads=[w_l.load for w_l in self.workload]):
            self._redistribute()
