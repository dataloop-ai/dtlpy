import logging
from .. import utilities, entities

logger = logging.getLogger('dataloop.artifact')


class Artifact(entities.Item):
    """
    Artifact object
    """
    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def type(self):
        return self.entity_dict['type']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def description(self):
        return self.entity_dict['description']

    @property
    def creator(self):
        return self.entity_dict['creator']
