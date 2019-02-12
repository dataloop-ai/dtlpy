import logging
from .. import utilities

logger = logging.getLogger('dataloop.artifact')


class Artifact:
    """
    Artifact object
    """
    def __init__(self, entity_dict):
        self.entity_dict = entity_dict

    def print(self):
        utilities.List([self]).print()

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
