import os
import logging

from .. import repositories, utilities

logger = logging.getLogger('dataloop.dataset')


class Dataset:
    """
    Dataset object
    """

    def __init__(self, entity_dict, project=None):
        self.entity_dict = entity_dict
        self._project = project
        self._items = repositories.Items(dataset=self)
        self._classes = dict()

    def __copy__(self):
        return Dataset(entity_dict=self.entity_dict, project=self.project)

    def to_dict(self):
        return self.entity_dict

    def __get_local_path__(self):
        if self.project is not None:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'projects', self.project.name,
                                      'datasets', self.name)
        else:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'datasets', '%s_%s' % (self.name, self.id))
        return local_path

    def print(self):
        utilities.List([self]).print()

    @staticmethod
    def parse_classes(classes):
        label_dict = dict()
        for label, color_str in classes.items():
            if color_str is None:
                color = None
            elif color_str.startswith('rgb'):
                color = tuple(eval(color_str.lstrip('rgb')))
            elif color_str.startswith('#'):
                color = tuple(int(color_str.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            else:
                logger.warning('Unknown color scheme: %s' % color_str)
                color = (255, 0, 0)
            label_dict[label] = color
        return label_dict

    @staticmethod
    def serialize_classes(labels_dict):
        dataset_classes_dict = dict()
        for label, color in labels_dict.items():
            dataset_classes_dict[label] = '#%02x%02x%02x' % color
        return dataset_classes_dict

    @property
    def project(self):
        return self._project

    @property
    def id(self):
        return self.entity_dict['id']

    @property
    def name(self):
        return self.entity_dict['name']

    @property
    def classes(self):
        if len(self._classes) == 0:
            self._classes = self.parse_classes(self.entity_dict['classes'])
        return self._classes

    @property
    def items(self):
        return self._items

    def label_to_color(self, label):
        return self.classes[label]
