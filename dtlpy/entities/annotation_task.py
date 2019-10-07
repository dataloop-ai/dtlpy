import attr
from .. import repositories
from .. import entities


@attr.s
class AnnotationTask:
    """
    AnnotationTask object
    """

    # platform
    name = attr.ib()
    status = attr.ib()
    projectId = attr.ib()
    metadata = attr.ib()
    id = attr.ib()
    url = attr.ib()
    creator = attr.ib()
    dueDate = attr.ib()
    datasetId = attr.ib()
    recipeId = attr.ib()
    query = attr.ib()
    assignmentIds = attr.ib()

    # sdk
    _client_api = attr.ib()
    _current_assignments = attr.ib(default=None)
    _assignments = attr.ib(default=None)
    _project = attr.ib(default=None)

    @classmethod
    def from_json(cls, _json, client_api):
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
            client_api=client_api
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self, filter=attr.filters.exclude(attr.fields(AnnotationTask)._client_api,
                                                             attr.fields(AnnotationTask)._project,
                                                             attr.fields(AnnotationTask)._assignments))

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
    def project(self):
        if self._project is None:
            projects = repositories.Projects(client_api=self._client_api)
            self._project = projects.get(project_id=self.projectId)
        assert isinstance(self._project, entities.Project)
        return self._project
