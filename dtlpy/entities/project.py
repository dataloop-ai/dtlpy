import logging
from .. import repositories, utilities
import attr

logger = logging.getLogger('dataloop.project')


@attr.s
class Project:
    """
    Project entity
    """
    client_api = attr.ib()
    contributors = attr.ib()
    createdAt = attr.ib()
    creator = attr.ib()
    id = attr.ib()
    name = attr.ib()
    org = attr.ib()
    updatedAt = attr.ib()

    # repositories
    _projects = attr.ib()
    _datasets = attr.ib()
    _tasks = attr.ib()
    _packages = attr.ib()
    _artifacts = attr.ib()

    @_projects.default
    def set_projects(self):
        return repositories.Projects(client_api=self.client_api)

    @property
    def projects(self):
        assert isinstance(self._projects, repositories.Projects)
        return self._projects

    @_datasets.default
    def set_datasets(self):
        return repositories.Datasets(project=self, client_api=self.client_api)

    @property
    def datasets(self):
        assert isinstance(self._datasets, repositories.Datasets)
        return self._datasets

    @_tasks.default
    def set_tasks(self):
        return repositories.Tasks(project=self, client_api=self.client_api)

    @property
    def tasks(self):
        assert isinstance(self._tasks, repositories.Tasks)
        return self._tasks

    @_packages.default
    def set_packages(self):
        return repositories.Packages(project=self, client_api=self.client_api)

    @property
    def packages(self):
        assert isinstance(self._packages, repositories.Packages)
        return self._packages

    @_artifacts.default
    def set_artifacts(self):
        return repositories.Artifacts(project=self, client_api=self.client_api)

    @property
    def artifacts(self):
        assert isinstance(self._artifacts, repositories.Artifacts)
        return self._artifacts

    @classmethod
    def from_json(cls, _json, client_api):
        """
        Build a Project entity object from a json

        :param _json: _json respons form host
        :param client_api: client_api
        :return: Project object
        """
        return cls(
            client_api=client_api,
            contributors=_json['contributors'],
            createdAt=_json['createdAt'],
            creator=_json['creator'],
            id=_json['id'],
            name=_json['name'],
            org=_json['org'],
            updatedAt=_json['updatedAt']
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.include(attr.fields(Project).contributors,
                                                       attr.fields(Project).createdAt,
                                                       attr.fields(Project).creator,
                                                       attr.fields(Project).id,
                                                       attr.fields(Project).name,
                                                       attr.fields(Project).org,
                                                       attr.fields(Project).updatedAt))

    def print(self):
        utilities.List([self]).print()

    def delete(self, sure=False, really=False):
        """
        Delete a project forever!
        :param sure: are you sure you want to delete?
        :param really: really really?
        :return: True
        """
        return self.projects.delete(project_id=self.id,
                                    sure=sure,
                                    really=really)

    def update(self, system_metadata=False):
        """
        Update a project
        :return: Project object
        """
        return self.projects.update(project=self, system_metadata=system_metadata)
