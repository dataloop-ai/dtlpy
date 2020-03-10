import logging
from ..exceptions import PlatformException
import os

logger = logging.getLogger(name=__name__)


class Filters:
    """
    Filters entity to filter items from pages in platform
    """

    def __init__(self, field=None, values=None, operator=None, method=None):
        self.or_filter_list = list()
        self.and_filter_list = list()
        self.custom_filter = None
        self.known_operators = ['or', 'and', 'in', 'ne', 'eq', 'gt', 'glob', 'lt']
        self.resource = 'items'
        self.page = 0
        self.page_size = 1000
        self.method = 'and'
        self.sort = dict()
        self.show_hidden = False
        self.show_dirs = False
        self.join = None
        self._ref_task = False
        self._ref_assignment = False
        self._ref_op = None
        self._ref_assignment_id = None
        self._ref_task_id = None

        if field is not None and values is not None:
            self.add(field=field, values=values, operator=operator, method=method)

    def _nullify_refs(self):
        self._ref_task = False
        self._ref_assignment = False
        self._ref_op = None
        self._ref_assignment_id = None
        self._ref_task_id = None

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
                'filter': {
                    '$and': and_list
                },
                'sort': {'type': 'ascending', 'createdAt': 'descending'},
            },
            'annotations': {
                'filter': dict(),
                'sort': {'label': 'ascending', 'createdAt': 'descending'},
            },
        }
        return default_filter[self.resource]

    def add(self, field, values, operator=None, method=None):
        """
        Add filter
        :param method: Optional - or/and
        :param field: Metadata field / attribute
        :param values: field values
        :param operator: optional - in, gt, lt, eq, ne
        :return:
        """
        if method is None:
            method = self.method

        # add ** if doesnt exist
        if self.resource == 'items':
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
        if method == 'or':
            self.or_filter_list.append(
                SingleFilter(field=field, values=values, operator=operator)
            )
        elif method == 'and':
            self.and_filter_list.append(
                SingleFilter(field=field, values=values, operator=operator)
            )
        else:
            raise PlatformException('400', 'Unknown method {}, please select from: or/and'.format(method))

    def pop(self, field):
        for single_filter in self.or_filter_list:
            if single_filter.field == field:
                self.or_filter_list.remove(single_filter)

        for single_filter in self.and_filter_list:
            if single_filter.field == field:
                self.and_filter_list.remove(single_filter)

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

    def __has_filters(self):
        if self.and_filter_list or self.or_filter_list:
            return True
        else:
            return False

    def prepare(self, operation=None, update=None):
        """
        To dictionary for platform call
        :return: dict
        """
        # filters exist
        if self.__has_filters() or self.custom_filter is not None:
            ###############
            # create json #
            ###############
            _json = dict()

            ###########
            # filters #
            ###########
            # add filters to json
            if self.custom_filter is None:
                filters_dict = dict()

                if len(self.or_filter_list) > 0:
                    or_filters = list()
                    for single_filter in self.or_filter_list:
                        or_filters.append(single_filter.prepare())
                    filters_dict['$or'] = or_filters

                if len(self.and_filter_list) > 0:
                    and_filters = list()
                    for single_filter in self.and_filter_list:
                        and_filters.append(single_filter.prepare())
                    filters_dict['$and'] = and_filters

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

            else:
                if 'filter' in self.custom_filter or 'join' in self.custom_filter:
                    if 'filter' in self.custom_filter:
                        _json['filter'] = self.custom_filter['filter']
                    self.join = self.custom_filter.get('join', self.join)
                else:
                    _json['filter'] = self.custom_filter

        # no filters
        else:
            _json = self.default_filter

        ##################
        # filter options #
        ##################
        if len(self.sort) > 0:
            _json['sort'] = self.sort
        _json['page'] = self.page
        _json['pageSize'] = self.page_size
        _json['resource'] = self.resource

        ########
        # join #
        ########
        if self.join is not None:
            _json['join'] = self.join

        #############
        # operation #
        #############
        if self._ref_assignment or self._ref_task:
            refs = list()
            if self._ref_task:
                task_refs = list()
                if not isinstance(self._ref_task_id, list):
                    self._ref_task_id = [self._ref_task_id]

                for ref_id in self._ref_task_id:
                    task_refs.append({'type': 'task', 'id': ref_id})

                refs += task_refs

            if self._ref_assignment:
                assignment_refs = list()
                if not isinstance(self._ref_assignment_id, list):
                    self._ref_assignment_id = [self._ref_assignment_id]

                for ref_id in self._ref_assignment_id:
                    assignment_refs.append({'type': 'assignment', 'id': ref_id})

                refs += assignment_refs

            _json['references'] = {
                'operation': self._ref_op,
                'refs': refs
            }

        elif operation is not None:
            if operation == 'update':
                _json[operation] = {'metadata': {'user': update}}
            elif operation == 'delete':
                _json[operation] = True
                _json.pop('sort', None)
                if self.resource == 'items':
                    _json.pop('page', None)
                    _json.pop('pageSize', None)
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
