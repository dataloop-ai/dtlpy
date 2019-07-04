import logging
import attr
from ..exceptions import PlatformException

logger = logging.getLogger('dataloop.items.filters')


class Filters:
    """
    Filters entity to filter items from pages in platform
    """

    def __init__(self):
        self.filter_dict = dict()
        self.known_fields = ['filename', 'type', 'createdAt']
        self.known_operators = ['or', 'and']

    def __call__(self, field, value, operator=None):
        # if field not in self.known_fields:
        #     raise PlatformException(
        #         error='400',
        #         message='unknown "field": "{}". Must be in: {}'.format(field, self.known_fields))

        if operator is not None:
            if operator not in self.known_operators:
                raise PlatformException(
                    error='400',
                    message='unknown "operator": "{}". Must be in: {}'.format(operator, self.known_fields))
            operator = '${}'.format(operator)
            if operator not in self.filter_dict:
                self.filter_dict[operator] = list()
            self.filter_dict[operator].append({field: {'$glob': value}})
        else:
            if field == 'filename':
                self.filter_dict[field] = {'$glob': value}
            else:
                self.filter_dict[field] = value

    def prepare(self):
        """
        To dictionary for platform call
        :return: dict
        """
        return self.filter_dict
