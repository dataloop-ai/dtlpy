import logging
from ..exceptions import PlatformException
import os

logger = logging.getLogger(name=__name__)


class Filters:
    """
    Filters entity to filter items from pages in platform
    """

    def __init__(self):
        self.filter_list = list()
        self.known_operators = ['or', 'and', 'in', 'ne', 'eq', 'gt', 'glob', 'lt']
        self.resource = 'items'
        self.page = 0
        self.page_size = 1000
        self.method = 'and'
        self.sort = dict()
        self.show_hidden = False
        self.show_dirs = False
        self.join = None

    @property
    def default_filter(self):
        and_list = list()
        if self.resource == 'items':
            if not self.show_hidden:
                and_list.append({'hidden': False})
            if not self.show_dirs:
                and_list.append({'type': 'file'})

        default_filter = {
            'items': {
                'resource': 'items',
                'pageSize': self.page_size,
                'page': self.page,
                'filter': {
                    '$and': and_list
                },
                'sort': {'type': 'ascending', 'createdAt': 'descending'},
            },
            'annotations': {
                'resource': 'annotations',
                'filter': dict(),
                'sort': {'label': 'ascending', 'createdAt': 'descending'},
            },
        }
        return default_filter[self.resource]

    def add(self, field, values, operator=None):
        """
        Add filter
        :param field: Metadata field
        :param values: field values
        :param operator: optional - $in, $gt, $lt, $eq, $ne - default = $eq
        :return:
        """
        # add ** if doesnt exist
        if field == 'type':
            if (isinstance(values, str) and values == 'dir') or (isinstance(values, list) and 'dir' in values):
                self.show_dirs = True
        elif field == 'filename':
            if isinstance(values, str):
                if not values.endswith('*') and not os.path.splitext(values)[-1].startswith('.'):
                    if values.endswith('/'):
                        values = values + '**'
                    else:
                        values = values + '/**'
            elif isinstance(values, list):
                for i_value, value in enumerate(values):
                    if isinstance(value, str):
                        if not value.endswith('*') and not os.path.splitext(value)[-1].startswith('.'):
                            if value.endswith('/'):
                                values[i_value] = value + '**'
                            else:
                                values[i_value] = value + '/**'

        # create SingleFilter object and add to self.filter_list
        self.filter_list.append(
            SingleFilter(field=field, values=values, operator=operator)
        )

    def pop(self, field):
        for single_filter in self.filter_list:
            if single_filter.field == field:
                self.filter_list.remove(single_filter)
        if field == 'type':
            self.show_dirs = False

    def pop_join(self, field):
        if self.resource == 'annotations':
            raise PlatformException('400', 'Cannot join to annotations filters')
        if self.join is not None:
            for single_filter in self.join['filter']['$and']:
                if field in single_filter:
                    self.join['filter']['$and'].remove(single_filter)

    def add_join(self, field, values, operator=None):
        if self.resource == 'annotations':
            raise PlatformException('400', 'Cannot join to annotations filters')
        if self.join is None:
            self.join = dict()
        if 'on' not in self.join:
            self.join['on'] = {'resource': 'annotations', 'local': 'itemId', 'forigen': 'id'}
        if 'filter' not in self.join:
            self.join['filter'] = dict()
        if '$and' not in self.join['filter']:
            self.join['filter']['$and'] = list()
        self.join['filter']['$and'].append(SingleFilter(field=field, values=values, operator=operator).prepare())

    def prepare(self, operation=None, update=None):
        """
        To dictionary for platform call
        :return: dict
        """
        # filters exist
        if len(self.filter_list) > 0:
            ###############
            # create json #
            ###############
            _json = dict()
            _json['resource'] = self.resource
            _json['sort'] = self.sort
            if self.resource == 'items':
                _json['page'] = self.page
                _json['pageSize'] = self.page_size

            ###########
            # filters #
            ###########
            # add filters to json
            filters = list()
            for single_filter in self.filter_list:
                filters.append(single_filter.prepare())
            filters_dict = dict()
            filters_dict['${}'.format(self.method)] = filters

            # add items defaults
            if self.resource == 'items':
                if not self.show_hidden:
                    if '$and' not in filters_dict:
                        filters_dict['$and'] = list()
                    filters_dict['$and'] += Filters.hidden()
                if not self.show_dirs:
                    if '$and' not in filters_dict:
                        filters_dict['$and'] = list()
                    filters_dict['$and'] += Filters.no_dirs()

            # add to json
            _json['filter'] = filters_dict

        # no filters
        else:
            _json = self.default_filter

        ########
        # join #
        ########
        if self.join is not None:
            _json['join'] = self.join

        #############
        # operation #
        #############
        if operation is not None:
            if operation == 'update':
                _json[operation] = {'metadata': {'user': update}}
            elif operation == 'delete':
                _json[operation] = True
                _json.pop('sort')
                if self.resource == 'items':
                    _json.pop('page')
                    _json.pop('pageSize')
            else:
                raise PlatformException(error='400',
                                        message='Unknown operation: {}'.format(operation))

        # return json
        return _json

    def sort_by(self, field, value='ascending'):
        if value not in ['ascending', 'descending']:
            raise PlatformException(error='400', message='Sort can be by ascending or descending order only')
        self.sort[field] = value

    @staticmethod
    def hidden():
        hidden = [{'hidden': False}]
        assert isinstance(hidden, list)
        return hidden

    @staticmethod
    def no_dirs():
        no_dirs = [{'type': 'file'}]
        assert isinstance(no_dirs, list)
        return no_dirs


class SingleFilter:
    def __init__(self, field, values, operator=None):
        self.field = field
        self.values = values
        self.operator = operator

    def prepare(self):
        _json = dict()
        if self.operator is None:
            _json[self.field] = self.values
        else:
            value = dict()
            value['${}'.format(self.operator)] = self.values
            _json[self.field] = value

        return _json
