import attr

from .. import repositories, exceptions, entities


@attr.s
class Assignment:
    """
    Assignment object
    """

    # platform
    name = attr.ib()
    annotator = attr.ib()
    status = attr.ib()
    projectId = attr.ib()
    metadata = attr.ib(repr=False)
    id = attr.ib()
    url = attr.ib(repr=False)

    # sdk
    _client_api = attr.ib(repr=False)
    _task = attr.ib(default=None, repr=False)
    _assignments = attr.ib(default=None, repr=False)
    _project = attr.ib(default=None, repr=False)
    _dataset = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project=None, task=None, dataset=None):
        return cls(
            name=_json.get('name', None),
            annotator=_json.get('annotator', None),
            status=_json.get('status', None),
            projectId=_json.get('projectId', None),
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
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    def get_project(self):
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.projectId)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self, filter=attr.filters.exclude(attr.fields(Assignment)._client_api,
                                                             attr.fields(Assignment)._project,
                                                             attr.fields(Assignment)._assignments,
                                                             attr.fields(Assignment)._dataset,
                                                             attr.fields(Assignment)._task))

    def update(self, system_metadata=False):
        return self.assignments.update(assignment=self, system_metadata=system_metadata)

    def assign_items(self, dataset=None, filters=None, items=None):
        """

        :param filters:
        :param dataset:
        :param items:
        :return:
        """
        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide dataset')

        if dataset is None:
            dataset = self._dataset

        return self.assignments.assign_items(dataset=dataset, assignment_id=self.id, filters=filters, items=items)

    def remove_items(self, dataset=None, filters=None, items=None):
        """

        :param dataset:
        :param filters:
        :param items:
        :return:
        """
        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide dataset')

        if dataset is None:
            dataset = self._dataset

        return self.assignments.remove_items(dataset=dataset, assignment_id=self.id, filters=filters, items=items)

    def get_items(self, dataset=None):
        """

        :param dataset:
        :return:
        """
        if dataset is None and self._dataset is None:
            raise exceptions.PlatformException('400', 'Please provide dataset')

        if dataset is None:
            dataset = self._dataset

        return self.assignments.get_items(dataset=dataset, assignment_id=self.id)
