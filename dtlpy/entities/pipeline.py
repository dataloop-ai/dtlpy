import logging
from .. import utilities

logger = logging.getLogger('dataloop.pipeline')


class Pipeline:
    """
    Pipeline object
    """

    def __init__(self, entity_dict):
        self.entity_dict = entity_dict

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def description(self):
        return self.entity_dict['description']

    @property
    def arch(self):
        return self.entity_dict['arch']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def type(self):
        return self.entity_dict['type']
