import logging
from .. import repositories, utilities

logger = logging.getLogger('dataloop.project')


class Project:
    """
    Project object
    """

    def __init__(self, entity_dict):
        self.entity_dict = entity_dict
        self._datasets = repositories.Datasets(project=self)
        self._tasks = repositories.Tasks(project=self)
        self._packages = repositories.Packages(project=self)
        self._artifacts = repositories.Artifacts(project=self)

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def datasets(self):
        return self._datasets

    @property
    def sessions(self):
        return self._sessions

    @property
    def packages(self):
        return self._packages

    @property
    def tasks(self):
        return self._tasks

    @property
    def artifacts(self):
        return self._artifacts
