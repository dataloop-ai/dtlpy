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
        self._sessions = repositories.Sessions(project=self)
        self._packages = repositories.Packages(project=self)

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
