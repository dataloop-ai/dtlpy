import attr
import logging
from .. import repositories, exceptions, entities

logger = logging.getLogger(name=__name__)


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

    # sdk
    _client_api = attr.ib(repr=False)
    _task = attr.ib(default=None, repr=False)
    _assignments = attr.ib(default=None, repr=False)
    _project = attr.ib(default=None, repr=False)
    _dataset = attr.ib(default=None, repr=False)
    _datasets = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project=None, task=None, dataset=None):
        return cls(
            name=_json.get('name', None),
            annotator=_json.get('annotator', None),
            status=_json.get('status', None),
            project_id=_json.get('projectId', None),
            metadata=_json.get('metadata', dict()),
            url=_json.get('url', None),
            id=_json['id'],
            client_api=client_api,
            project=project,
            dataset=dataset,
            task=task
        )

    @property
    def assignments(self):
        if self._assignments is None:
            self._assignments = repositories.Assignments(client_api=self._client_api, project=self.project,
                                                         task=self._task, dataset=self._dataset)
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
    def dataset_id(self):
        dataset_id = self.metadata.get('datasetId', None)
        if dataset_id is None:
            system_metadata = self.metadata.get('system', dict())
            dataset_id = system_metadata.get('datasetId', None)
        return dataset_id

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

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Assignment)._client_api,
                                                              attr.fields(Assignment)._project,
                                                              attr.fields(Assignment).project_id,
                                                              attr.fields(Assignment)._assignments,
                                                              attr.fields(Assignment)._dataset,
                                                              attr.fields(Assignment)._task))
        _json['projectId'] = self.project_id
        return _json

    def update(self, system_metadata=False):
        return self.assignments.update(assignment=self, system_metadata=system_metadata)

    def assign_items(self, dataset=None, filters=None, items=None):
        """

        :param filters:
        :param dataset:
        :param items:
        :return:
        """
        if dataset is None:
            dataset = self.dataset

        return self.assignments.assign_items(dataset=dataset, assignment_id=self.id, filters=filters, items=items)

    def remove_items(self, dataset=None, filters=None, items=None):
        """

        :param dataset:
        :param filters:
        :param items:
        :return:
        """
        if dataset is None:
            dataset = self.dataset

        return self.assignments.remove_items(dataset=dataset, assignment_id=self.id, filters=filters, items=items)

    def get_items(self, dataset=None, filters=None):
        """

        :param dataset:
        :return:
        """
        if dataset is None:
            dataset = self.dataset

        return self.assignments.get_items(dataset=dataset, assignment=self, filters=filters)

    def reassign(self, assignee_id):
        """
        Reassign an assignment
        :return: Assignment object
        """
        return self.assignments.reassign(assignment=self, task=self._task, assignee_id=assignee_id)

    def redistribute(self, workload):
        """
        Redistribute an assignment
        :return: Assignment object
        """
        return self.assignments.redistribute(assignment=self, task=self._task, workload=workload)


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
            workload=[workload_unit.from_json() for workload_unit in _json]
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
        loads = [l/100 for l in loads]
        return loads

    def _redistribute(self):
        load = self._get_loads(num_assignees=len(self.workload))
        for i_w_l, w_l in self.workload:
            w_l.load = load

    @classmethod
    def generate(cls, assignee_ids, loads=None):
        if not isinstance(assignee_ids, list):
            assignee_ids = [assignee_ids]

        if loads is None:
            load = 100 / len(assignee_ids)
            loads = [load for _ in range(len(assignee_ids))]
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
        self.workload.append(WorkloadUnit(assignee_id=assignee_id))
        if not self._loads_are_correct(loads=[w_l.load for w_l in self.workload]):
            self._redistribute()
