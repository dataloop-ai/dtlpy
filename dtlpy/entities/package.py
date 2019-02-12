import logging
import datetime

from .. import repositories, utilities

logger = logging.getLogger('dataloop.package')


class Package:
    """
    Package object
    """

    def __init__(self, entity_dict):
        self.entity_dict = entity_dict
        self._artifacts = repositories.Artifacts(package=self)

    def print(self):
        utilities.List([self]).print()

    @property
    def artifacts(self):
        return self._artifacts

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def creator(self):
        return self.entity_dict['creator']

    @property
    def description(self):
        return self.entity_dict['description']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def createdAt(self):
        return print(
            datetime.datetime.utcfromtimestamp(int(self.entity_dict['createdAt'])).strftime('%Y-%m-%d %H:%M:%S'))
