import logging
from .. import repositories, utilities

logger = logging.getLogger('dataloop.package')


class Session:
    """
    Session object
    """

    def __init__(self, entity_dict):
        self.entity_dict = entity_dict

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def createdAt(self):
        return self.entity_dict['createdAt']

    @property
    def datasetId(self):
        return self.entity_dict['datasetId']

    @property
    def input(self):
        return self.entity_dict['input']

    @property
    def output(self):
        return self.entity_dict['output']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def projectId(self):
        return self.entity_dict['projectId']

    @property
    def status(self):
        return self.entity_dict['status']

    @property
    def taskId(self):
        return self.entity_dict['metadata']['system']['taskId']
    
    @property
    def reporting_exchange(self):
        return self.entity_dict['feedbackQueue']['exchange']
    
    @property
    def reporting_route(self):
        return self.entity_dict['feedbackQueue']['routing']

