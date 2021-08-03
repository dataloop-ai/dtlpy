import logging
from enum import Enum
from ..exceptions import PlatformException
import os

logger = logging.getLogger(name=__name__)


class FiltersKnownFields(str, Enum):
    DIR = "dir"
    ANNOTATED = "annotated"
    FILENAME = "filename"
    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"
    LABEL = "label"
    NAME = "name"
    HIDDEN = "hidden"
    TYPE = 'type'


class FiltersResource(str, Enum):
    ITEM = "items"
    ANNOTATION = "annotations"
    EXECUTION = "executions"
    PACKAGE = "packages"
    SERVICE = "services"
    TRIGGER = "triggers"
    MODEL = "models"
    SNAPSHOT = "snapshots"
    WEBHOOK = "webhooks"
    RECIPE = 'recipe'
    DATASET = 'dataset'
    ONTOLOGY = 'ontology'
    TASK = 'tasks'
    PIPELINE = 'pipeline'
    PIPELINE_EXECUTION = 'pipelineState'
    COMPOSITION = 'composition'
    FEATURE = 'feature_vectors'
    FEATURE_SET = 'feature_sets'
    ORGANIZATIONS = 'organizations'


class FiltersOperations(str, Enum):
    OR = "or"
    AND = "and"
    IN = "in"
    NOT_EQUAL = "ne"
    EQUAL = "eq"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EXISTS = "exists"


class FiltersMethod(str, Enum):
    OR = "or"
    AND = "and"


class FiltersOrderByDirection(str, Enum):
    DESCENDING = "descending"
    ASCENDING = "ascending"


class Filters:
    """
    Filters entity to filter items from pages in platform
    """

    def __init__(self, field=None, values=None, operator: FiltersOperations = None,
                 method: FiltersMethod = None, custom_filter=None,
                 resource: FiltersResource = FiltersResource.ITEM, use_defaults=True, context=None):
        self.or_filter_list = list()
        self.and_filter_list = list()
        self._unique_fields = list()
        self.custom_filter = custom_filter
        self.known_operators = ['or', 'and', 'in', 'ne', 'eq', 'gt', 'glob', 'lt', 'exists']
        self._resource = resource
        self.page = 0
        self.page_size = 1000
        self.method = FiltersMethod.AND
        self.sort = dict()
        self.join = None
        self.recursive = True

        # system only - task and assignment attributes
        self._ref_task = False
        self._ref_assignment = False
        self._ref_op = None
        self._ref_assignment_id = None
        self._ref_task_id = None

        self._use_defaults = use_defaults
        self.__add_defaults()
        self.context = context

        if field is not None:
            self.add(field=field, values=values, operator=operator, method=method)

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, resource):
        self._resource = resource
        self.reset()
        self.__add_defaults()

    def reset(self):
        self.or_filter_list = list()
        self.and_filter_list = list()
        self._unique_fields = list()
        self.custom_filter = None
        self.page = 0
        self.page_size = 1000
        self.method = FiltersMethod.AND
        self.sort = dict()
        self.join = None
        self.recursive = True
        self._nullify_refs()

    def _nullify_refs(self):
        self._ref_task = False
        self._ref_assignment = False
        self._ref_op = None
        self._ref_assignment_id = None
        self._ref_task_id = None

    def add(self, field, values, operator: FiltersOperations = None, method: FiltersMethod = None):
        """
        Add filter
        :param field: Metadata field / attribute
        :param values: field values
        :param operator: optional - in, gt, lt, eq, ne
        :param method: Optional - or/and
        :return:
        """
        if method is None:
            method = self.method

        # create SingleFilter object and add to self.filter_list
        if method == FiltersMethod.OR:
            self.or_filter_list.append(SingleFilter(field=field, values=values, operator=operator))
        elif method == FiltersMethod.AND:
            self.__override(field=field, values=values, operator=operator)
        else:
            raise PlatformException('400', 'Unknown method {}, please select from: or/and'.format(method))

    def __override(self, field, values, operator=None):
        if field in self._unique_fields:
            for i_single_filter, single_filter in enumerate(self.and_filter_list):
                if single_filter.field == field:
                    self.and_filter_list.pop(i_single_filter)
        self.and_filter_list.append(
            SingleFilter(field=field, values=values, operator=operator)
        )

    def generate_url_query_params(self, url):
        """
        :param url"
        """
        url = '{}?'.format(url)
        for f in self.and_filter_list:
            if isinstance(f.values, list):
                url = '{}{}={}&'.format(url, f.field, ','.join(f.values))
            else:
                url = '{}{}={}&'.format(url, f.field, f.values)
        return '{}&pageOffset={}&pageSize={}'.format(url, self.page, self.page_size)

    def has_field(self, field):
        """
        :param field:
        """
        for single_filter in self.or_filter_list:
            if single_filter.field == field:
                return True

        for single_filter in self.and_filter_list:
            if single_filter.field == field:
                return True

        return False

    def pop(self, field):
        """
        :param field:
        """
        for single_filter in self.or_filter_list:
            if single_filter.field == field:
                self.or_filter_list.remove(single_filter)

        for single_filter in self.and_filter_list:
            if single_filter.field == field:
                self.and_filter_list.remove(single_filter)

    def pop_join(self, field):
        """
        :param field:
        """
        if self.resource == FiltersResource.ANNOTATION:
            raise PlatformException('400', 'Cannot join to annotations filters')
        if self.join is not None:
            for single_filter in self.join['filter']['$and']:
                if field in single_filter:
                    self.join['filter']['$and'].remove(single_filter)

    def add_join(self, field, values, operator: FiltersOperations = None):
        """
        join a query to the filter
        :param field:
        :param values:
        :param operator: optional - in, gt, lt, eq, ne
        """
        if self.resource != FiltersResource.ITEM:
            raise PlatformException('400', 'Cannot join to {} filters'.format(self.resource))

        if self.join is None:
            self.join = dict()
        if 'on' not in self.join:
            self.join['on'] = {'resource': FiltersResource.ANNOTATION, 'local': 'itemId', 'forigen': 'id'}
        if 'filter' not in self.join:
            self.join['filter'] = dict()
        if '$and' not in self.join['filter']:
            self.join['filter']['$and'] = list()
        self.join['filter']['$and'].append(SingleFilter(field=field, values=values, operator=operator).prepare())

    def __add_defaults(self):
        if self._use_defaults:
            # add items defaults
            if self.resource == FiltersResource.ITEM:
                self._unique_fields = ['type', 'hidden']
                self.add(field='hidden', values=False, method=FiltersMethod.AND)
                self.add(field='type', values='file', method=FiltersMethod.AND)
                self.sort_by(field='createdAt', value=FiltersOrderByDirection.DESCENDING)
            # add service defaults
            elif self.resource == FiltersResource.SERVICE:
                self._unique_fields = ['global']
                self.add(field='global', values=True, operator=FiltersOperations.NOT_EQUAL, method=FiltersMethod.AND)
            elif self.resource == FiltersResource.PACKAGE:
                self._unique_fields = ['global']
                self.add(field='global', values=True, operator=FiltersOperations.NOT_EQUAL, method=FiltersMethod.AND)
            # add annotations defaults
            elif self.resource == FiltersResource.ANNOTATION:
                self._unique_fields = ['type']
                self.add(field='type',
                         values=['box', 'class', 'comparison', 'ellipse', 'point', 'segment', 'polyline', 'binary',
                                 'subtitle', 'cube', 'pose', 'text_mark'], operator=FiltersOperations.IN, method=FiltersMethod.AND)
                self.sort_by(field='label', value=FiltersOrderByDirection.ASCENDING)
                self.sort_by(field='createdAt', value=FiltersOrderByDirection.DESCENDING)

    def __generate_query(self):
        filters_dict = dict()

        if len(self.or_filter_list) > 0:
            or_filters = list()
            for single_filter in self.or_filter_list:
                or_filters.append(
                    single_filter.prepare(recursive=self.recursive and self.resource == FiltersResource.ITEM))
            filters_dict['$or'] = or_filters

        if len(self.and_filter_list) > 0:
            and_filters = list()
            for single_filter in self.and_filter_list:
                and_filters.append(
                    single_filter.prepare(recursive=self.recursive and self.resource == FiltersResource.ITEM))
            filters_dict['$and'] = and_filters

        return filters_dict

    def __generate_custom_query(self):
        filters_dict = dict()
        if 'filter' in self.custom_filter or 'join' in self.custom_filter:
            if 'filter' in self.custom_filter:
                filters_dict = self.custom_filter['filter']
            self.join = self.custom_filter.get('join', self.join)
        else:
            filters_dict = self.custom_filter
        return filters_dict

    def __generate_ref_query(self):
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

        return refs

    def prepare(self, operation=None, update=None, query_only=False, system_update=None, system_metadata=False):
        """
        To dictionary for platform call
        :param operation:
        :param update:
        :param query_only:
        :param system_update:
        :param system_metadata: True, if you want to change metadata system
        :return: dict
        """
        ########
        # json #
        ########
        _json = dict()

        if self.custom_filter is None:
            _json['filter'] = self.__generate_query()
        else:
            _json['filter'] = self.__generate_custom_query()

        ##################
        # filter options #
        ##################
        if not query_only:
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

        #####################
        # operation or refs #
        #####################
        if self._ref_assignment or self._ref_task:
            _json['references'] = {
                'operation': self._ref_op,
                'refs': self.__generate_ref_query()
            }
        elif operation is not None:
            if operation == 'update':
                if update:
                    _json[operation] = {'metadata': {'user': update}}
                else:
                    _json[operation] = dict()
                if system_metadata and system_update:
                    _json['systemSpace'] = True
                    _json[operation]['metadata'] = _json[operation].get('metadata', dict())
                    _json[operation]['metadata']['system'] = system_update
            elif operation == 'delete':
                _json[operation] = True
                _json.pop('sort', None)
                if self.resource == FiltersResource.ITEM:
                    _json.pop('page', None)
                    _json.pop('pageSize', None)
            else:
                raise PlatformException(error='400',
                                        message='Unknown operation: {}'.format(operation))

        if self.context is not None:
            _json['context'] = self.context

        return _json

    def sort_by(self, field, value: FiltersOrderByDirection = FiltersOrderByDirection.ASCENDING):
        """
        :param field:
        :param value: FiltersOrderByDirection.ASCENDING, FiltersOrderByDirection.DESCENDING
        """
        if value not in [FiltersOrderByDirection.ASCENDING, FiltersOrderByDirection.DESCENDING]:
            raise PlatformException(error='400', message='Sort can be by ascending or descending order only')
        self.sort[field] = value


class SingleFilter:
    def __init__(self, field, values, operator: FiltersOperations = None):
        self.field = field
        self.values = values
        self.operator = operator

    @staticmethod
    def __add_recursive(value):
        if not value.endswith('*') and not os.path.splitext(value)[-1].startswith('.'):
            if value.endswith('/'):
                value = value + '**'
            else:
                value = value + '/**'
        return value

    def prepare(self, recursive=False):
        """
        :param recursive:
        """
        _json = dict()
        values = self.values

        if recursive and self.field == 'filename':
            if isinstance(values, str):
                values = self.__add_recursive(value=values)
            elif isinstance(values, list):
                for i_value, value in enumerate(values):
                    values[i_value] = self.__add_recursive(value=value)

        if self.operator is None:
            _json[self.field] = values
        else:
            value = dict()
            value['${}'.format(self.operator)] = values
            _json[self.field] = value

        return _json
