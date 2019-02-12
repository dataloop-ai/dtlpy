import logging
from .. import repositories, utilities

logger = logging.getLogger('dataloop.item')


class Item:
    """
    Item object
    """

    def __init__(self, entity_dict, dataset):
        self.entity_dict = entity_dict
        self._dataset = dataset
        self._annotations = repositories.Annotations(dataset=dataset, item=self)

    def to_dict(self):
        return self.entity_dict

    def from_dict(self, entity_dict):
        self.entity_dict = entity_dict

    def print(self):
        utilities.List([self]).print()

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def width(self):
        width = None
        if hasattr(self.metadata.system, 'width'):
            width = self.metadata.system.width
        return width

    @property
    def height(self):
        height = None
        if hasattr(self.metadata.system, 'height'):
            height = self.metadata.system.height
        return height

    @property
    def filename(self):
        return self.entity_dict['filename']

    @property
    def type(self):
        return self.entity_dict['type']

    @property
    def metadata(self):
        # build class from metadata dictionary
        class Metadata:
            """
            Metadata object
            """
            def __init__(self, data):
                for name, value in data.items():
                    setattr(self, name, self._wrap(value))

            def _wrap(self, value):
                if isinstance(value, (tuple, list, set, frozenset)):
                    return type(value)([self._wrap(v) for v in value])
                else:
                    return Metadata(value) if isinstance(value, dict) else value

        return Metadata(self.entity_dict['metadata'])

    @metadata.setter
    def metadata(self, metadata):
        self.entity_dict['metadata'] = metadata

    @property
    def system(self):
        return self.entity_dict['metadata']['system']

    @property
    def mimetype(self):
        return self.entity_dict['metadata']['system']['mimetype']

    @property
    def size(self):
        return self.entity_dict['metadata']['system']['size']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def token(self):
        return self.entity_dict['_token']

    @property
    def dataset(self):
        return self._dataset

    @property
    def annotations(self):
        return self._annotations
