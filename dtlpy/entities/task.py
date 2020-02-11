import attr
from .. import repositories, entities, exceptions


@attr.s
class Task:
    """
    Task object
    """

    # platform
    name = attr.ib()
    status = attr.ib()
    projectId = attr.ib()
    metadata = attr.ib(repr=False)
    id = attr.ib()
    url = attr.ib(repr=False)
    creator = attr.ib()
    dueDate = attr.ib()
    datasetId = attr.ib()
    recipeId = attr.ib(repr=False)
    query = attr.ib(repr=False)
    assignmentIds = attr.ib(repr=False)

    # sdk
    _client_api = attr.ib(repr=False)
    _current_assignments = attr.ib(default=None, repr=False)
    _assignments = attr.ib(default=None, repr=False)
    _project = attr.ib(default=None, repr=False)
    _dataset = attr.ib(default=None, repr=False)
    _tasks = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project=None, dataset=None):
        return cls(
            name=_json.get('name', None),
            status=_json.get('status', None),
            projectId=_json.get('projectId', None),
            metadata=_json.get('metadata', dict()),
            url=_json.get('url', None),
            id=_json['id'],
            creator=_json.get('creator', None),
            dueDate=_json.get('dueDate', 0),
            datasetId=_json.get('datasetId', None),
            recipeId=_json.get('recipeId', None),
            query=_json.get('query', None),
            assignmentIds=_json.get('assignmentIds', list()),
            dataset=dataset,
            project=project,
            client_api=client_api
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self, filter=attr.filters.exclude(attr.fields(Task)._client_api,
                                                             attr.fields(Task)._project,
                                                             attr.fields(Task)._tasks,
                                                             attr.fields(Task)._dataset,
                                                             attr.fields(Task)._current_assignments,
                                                             attr.fields(Task)._assignments))

    @property
    def current_assignments(self):
        if self._current_assignments is None:
            self._current_assignments = list()
            for assignment in self.assignmentIds:
                self._current_assignments.append(self._assignments.get(assignment_id=assignment))
        return self._current_assignments

    @property
    def assignments(self):
        if self._assignments is None:
            self._assignments = repositories.Assignments(client_api=self._client_api, project=self.project)
        assert isinstance(self._assignments, repositories.Assignments)
        return self._assignments

    @property
    def tasks(self):
        if self._tasks is None:
            self._tasks = repositories.Tasks(client_api=self._client_api, project=self.project, dataset=self.dataset)
        assert isinstance(self._tasks, repositories.Tasks)
        return self._tasks

    @property
    def project(self):
        if self._project is None:
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project". need to "get_project()" ')
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def dataset(self):
        if self._dataset is None:
            self.get_dataset()
            if self._dataset is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "dataset". need to "get_dataset()" ')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    def get_project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.projectId)

    def get_dataset(self):
        if self._dataset is None:
            self._dataset = repositories.Datasets(client_api=self._client_api, project=self._project).get(
                dataset_id=self.datasetId)

    def update(self, system_metadata=False):
        return self.project.tasks.update(task=self, system_metadata=system_metadata)

    def create_assignment(self, name, assignee, items=None, filters=None):
        """

        :param name:
        :param assignee:
        :param items:
        :param filters:
        :return:
        """
        assignment = self.assignments.create(name=name, annotator=assignee, project_id=self.projectId, filters=filters,
                                             items=items, dataset=self.dataset)
        assignment.metadata['system']['taskId'] = self.id
        assignment.update(system_metadata=True)
        self.assignmentIds.append(assignment.id)
        self.update()
        self.add_items(filters=filters, items=items)
        return assignment

    def add_items(self, filters=None, items=None):
        """

        :param filters:
        :param items:
        :return:
        """
        return self.tasks.add_items(dataset=self.dataset, task=self, filters=filters, items=items)

    def remove_items(self, filters=None, items=None):
        """

        :param filters:
        :param items:
        :return:
        """
        return self.tasks.remove_items(dataset=self.dataset, task=self, filters=filters, items=items)

    def get_items(self):
        """

        :return:
        """
        return self.tasks.get_items(task_id=self.id, dataset=self.dataset)
