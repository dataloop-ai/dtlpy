from collections import namedtuple
import logging
import attr

from .. import repositories, miscellaneous, services

logger = logging.getLogger(name=__name__)


@attr.s
class Project:
    """
    Project entity
    """

    contributors = attr.ib()
    createdAt = attr.ib()
    creator = attr.ib()
    id = attr.ib()
    name = attr.ib()
    org = attr.ib()
    updatedAt = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient)

    # repositories
    _repositories = attr.ib()

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          'projects triggers datasets plugins packages artifacts times_series deployments '
                          'sessions assignments annotation_tasks')

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 sessions=repositories.Sessions(client_api=self._client_api),
                 triggers=repositories.Triggers(client_api=self._client_api, project=self),
                 datasets=repositories.Datasets(client_api=self._client_api, project=self),
                 plugins=repositories.Plugins(project=self, client_api=self._client_api),
                 packages=repositories.Packages(project=self, client_api=self._client_api),
                 artifacts=repositories.Artifacts(project=self, client_api=self._client_api),
                 times_series=repositories.TimesSeries(project=self, client_api=self._client_api),
                 deployments=repositories.Deployments(client_api=self._client_api, project=self),
                 assignments=repositories.Assignments(project=self, client_api=self._client_api),
                 annotation_tasks=repositories.AnnotationTasks(client_api=self._client_api, project=self))
        return r

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def deployments(self):
        assert isinstance(self._repositories.deployments, repositories.Deployments)
        return self._repositories.deployments

    @property
    def sessions(self):
        assert isinstance(self._repositories.sessions, repositories.Sessions)
        return self._repositories.sessions

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def plugins(self):
        assert isinstance(self._repositories.plugins, repositories.Plugins)
        return self._repositories.plugins

    @property
    def packages(self):
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    @property
    def artifacts(self):
        assert isinstance(self._repositories.artifacts, repositories.Artifacts)
        return self._repositories.artifacts

    @property
    def times_series(self):
        assert isinstance(self._repositories.times_series, repositories.TimesSeries)
        return self._repositories.times_series

    @property
    def assignments(self):
        assert isinstance(self._repositories.assignments, repositories.Assignments)
        return self._repositories.assignments

    @property
    def annotation_tasks(self):
        assert isinstance(self._repositories.annotation_tasks, repositories.AnnotationTasks)
        return self._repositories.annotation_tasks

    @classmethod
    def from_json(cls, _json, client_api):
        """
        Build a Project entity object from a json

        :param _json: _json respons form host
        :param client_api: client_api
        :return: Project object
        """
        return cls(contributors=_json['contributors'],
                   createdAt=_json['createdAt'],
                   updatedAt=_json['updatedAt'],
                   creator=_json['creator'],
                   name=_json['name'],
                   org=_json['org'],
                   id=_json['id'],

                   client_api=client_api)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(Project)._client_api,
                                                       attr.fields(Project)._repositories))

    def print(self):
        miscellaneous.List([self]).print()

    def delete(self, sure=False, really=False):
        """
        Delete the project forever!

        :param sure: are you sure you want to delete?
        :param really: really really?
        :return: True
        """
        return self.projects.delete(project_id=self.id,
                                    sure=sure,
                                    really=really)

    def update(self, system_metadata=False):
        """
        Update the project

        :return: Project object
        """
        return self.projects.update(project=self, system_metadata=system_metadata)

    def checkout(self):
        """
        Checkout the project

        :return:
        """
        self.projects.checkout(identifier=self.name)

    def open_in_web(self):
        """
        Open the project in web platform

        :return:
        """
        self.projects.open_in_web(project=self)
