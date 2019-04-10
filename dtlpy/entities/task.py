import logging
from .. import utilities, repositories

logger = logging.getLogger('dataloop.pipeline')


class Task:
    """
    Pipeline object
    """

    def __init__(self, entity_dict):
        self.entity_dict = entity_dict
        self._sessions = repositories.Sessions(task=self)

    def print(self):
        utilities.List([self]).print()

    def to_dict(self):
        return self.entity_dict

    @property
    def sessions(self):
        return self._sessions

    @property
    def id(self):
        return self.entity_dict['id']


    @property
    def updatedAt(self):
        return self.entity_dict['updatedAt']

    @property
    def description(self):
        return self.entity_dict['metadata']['system']['description']

    @property
    def mq_details(self):
        return self.entity_dict['metadata']['system']['mq']

    @property
    def input(self):
        return self.entity_dict['input']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def output(self):
        return self.entity_dict['output']

    @property
    def pipeline(self):
        return self.entity_dict['pipeline']

    @property
    def projects(self):
        return self.entity_dict['metadata']['system']['projects']

    @property
    def triggers(self):
        return self.entity_dict['triggers']

    @property
    def version(self):
        return self.entity_dict['version']
