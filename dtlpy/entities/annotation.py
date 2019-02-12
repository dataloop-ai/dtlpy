import logging
from .. import utilities

logger = logging.getLogger('dataloop.annotation')


class Annotation:
    """
    Annotations object
    """
    def __init__(self, entity_dict, dataset, item):
        self.entity_dict = entity_dict
        self._dataset = dataset
        self._item = item

    def to_dict(self):
        return self.entity_dict

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def attributes(self):
        return self.entity_dict['attributes']

    @property
    def coordinates(self):
        return self.entity_dict['coordinates']

    @property
    def type(self):
        return self.entity_dict['type']

    @property
    def metadata(self):
        return self.entity_dict['metadata']

    @property
    def label(self):
        return self.entity_dict['label']

    @property
    def dataset(self):
        return self._dataset

    @property
    def item(self):
        return self._item
