import os
import logging
import datetime

from .. import repositories, utilities, entities

logger = logging.getLogger('dataloop.package')


class Package(entities.Item):
    """
    Package object
    """
    @property
    def description(self):
        return self.entity_dict['description']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def version(self):
        return int(os.path.splitext(self.entity_dict['name'])[0])
