import logging
from .. import repositories, utilities

logger = logging.getLogger('dataloop.package')


class Session:
    """
    Session object
    """

    def __init__(self, entity_dict, project):
        self.entity_dict = entity_dict
        self._project = project
        self._artifacts = repositories.Artifacts(session=self)

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def dataset(self):
        return self.entity_dict['dataset']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def package(self):
        return self.entity_dict['package']

    @property
    def pipeline(self):
        return self.entity_dict['pipe']

    @property
    def previous_session(self):
        return self.entity_dict['previous_session']

    @property
    def status(self):
        return self.entity_dict['status']

    @property
    def project(self):
        return self.entity_dict['project']

    @property
    def createdAt(self):
        return self.entity_dict['createdAt']

    @property
    def artifacts(self):
        return self._artifacts
