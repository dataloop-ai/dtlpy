from collections import namedtuple
import traceback
import logging
import attr

from .. import repositories, miscellaneous, services, entities

logger = logging.getLogger(name=__name__)


@attr.s()
class Project:
    """
    Project entity
    """

    _contributors = attr.ib(repr=False)
    createdAt = attr.ib()
    creator = attr.ib()
    id = attr.ib()
    name = attr.ib()
    org = attr.ib()
    updatedAt = attr.ib(repr=False)
    role = attr.ib()
    account = attr.ib()

    # name change
    feature_constraints = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)

    # repositories
    _repositories = attr.ib(repr=False)

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          'projects triggers datasets items packages codebases artifacts times_series services '
                          'executions assignments tasks bots webhooks')
        datasets = repositories.Datasets(client_api=self._client_api, project=self)

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 webhooks=repositories.Webhooks(client_api=self._client_api, project=self),
                 items=repositories.Items(client_api=self._client_api, datasets=datasets),
                 datasets=datasets,
                 executions=repositories.Executions(client_api=self._client_api),
                 triggers=repositories.Triggers(client_api=self._client_api, project=self),
                 packages=repositories.Packages(project=self, client_api=self._client_api),
                 codebases=repositories.Codebases(project=self, client_api=self._client_api),
                 artifacts=repositories.Artifacts(project=self, client_api=self._client_api),
                 times_series=repositories.TimesSeries(project=self, client_api=self._client_api),
                 services=repositories.Services(client_api=self._client_api, project=self),
                 assignments=repositories.Assignments(project=self, client_api=self._client_api),
                 tasks=repositories.Tasks(client_api=self._client_api, project=self),
                 bots=repositories.Bots(client_api=self._client_api, project=self))
        return r

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def packages(self):
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    @property
    def codebases(self):
        assert isinstance(self._repositories.codebases, repositories.Codebases)
        return self._repositories.codebases

    @property
    def webhooks(self):
        assert isinstance(self._repositories.webhooks, repositories.Webhooks)
        return self._repositories.webhooks

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
    def tasks(self):
        assert isinstance(self._repositories.tasks, repositories.Tasks)
        return self._repositories.tasks

    @property
    def bots(self):
        assert isinstance(self._repositories.bots, repositories.Bots)
        return self._repositories.bots

    @property
    def contributors(self):
        return miscellaneous.List([entities.User.from_json(_json=_json,
                                                           project=self) for _json in self._contributors])

    @staticmethod
    def _protected_from_json(_json, client_api):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :return:
        """
        try:
            project = Project.from_json(_json=_json,
                                        client_api=client_api)
            status = True
        except Exception:
            project = traceback.format_exc()
            status = False
        return status, project

    @classmethod
    def from_json(cls, _json, client_api):
        """
        Build a Project entity object from a json

        :param _json: _json response from host
        :param client_api: client_api
        :return: Project object
        """
        return cls(contributors=_json['contributors'],
                   feature_constraints=_json.get('featureConstraints', None),
                   createdAt=_json['createdAt'],
                   updatedAt=_json['updatedAt'],
                   creator=_json['creator'],
                   account=_json.get('account', None),
                   name=_json['name'],
                   role=_json.get('role', None),
                   org=_json['org'],
                   id=_json['id'],

                   client_api=client_api)

    # noinspection PyShadowingBuiltins
    @classmethod
    def dummy(cls, project_id, client_api, name=None):
        """
        Build a Project entity object from a json

        :param project_id: id
        :param name : name
        :param client_api: client_api
        :return: Project object
        """
        return cls(contributors=None,
                   createdAt=None,
                   updatedAt=None,
                   creator=None,
                   name=name,
                   org=None,
                   id=project_id,

                   client_api=client_api)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        output_dict = attr.asdict(self,
                                  filter=attr.filters.exclude(attr.fields(Project)._client_api,
                                                              attr.fields(Project)._repositories,
                                                              attr.fields(Project).feature_constraints,
                                                              attr.fields(Project)._contributors))
        output_dict['contributors'] = self._contributors
        output_dict['featureConstraints'] = self.feature_constraints

        return output_dict

    def print(self, to_return=False):
        return miscellaneous.List([self]).print(to_return=to_return)

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
        self.projects.checkout(project=self)

    def open_in_web(self):
        """
        Open the project in web platform

        :return:
        """
        self.projects.open_in_web(project=self)
