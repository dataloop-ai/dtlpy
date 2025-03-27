import urllib.parse
import logging
import json
import os
import io
from enum import Enum

from .. import exceptions, entities

logger = logging.getLogger(name='dtlpy')


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
    DPK = "dpks"
    APP = "apps"
    SERVICE = "services"
    TRIGGER = "triggers"
    MODEL = "models"
    WEBHOOK = "webhooks"
    RECIPE = 'recipe'
    DATASET = 'datasets'
    ONTOLOGY = 'ontology'
    TASK = 'tasks'
    PIPELINE = 'pipeline'
    PIPELINE_EXECUTION = 'pipelineState'
    COMPOSITION = 'composition'
    FEATURE = 'feature_vectors'
    FEATURE_SET = 'feature_sets'
    ORGANIZATIONS = 'organizations'
    DRIVERS = 'drivers'
    SETTINGS = 'setting'
    RESOURCE_EXECUTION = 'resourceExecution'
    METRICS = 'metrics'


class FiltersOperations(str, Enum):
    OR = "or"
    AND = "and"
    IN = "in"
    NOT_EQUAL = "ne"
    EQUAL = "eq"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EXISTS = "exists"
    MATCH = "match"
    NIN = 'nin'


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

    def __init__(
            self,
            field=None,
            values=None,
            operator: FiltersOperations = None,
            method: FiltersMethod = None,
            custom_filter=None,
            resource: FiltersResource = FiltersResource.ITEM,
            use_defaults=True,
            context=None,
            page_size=None,
    ):
        if page_size is None:
            if resource in [FiltersResource.EXECUTION,
                            FiltersResource.PIPELINE_EXECUTION,
                            FiltersResource.DPK]:
                page_size = 100
            else:
                page_size = 1000

        self.or_filter_list = list()
        self.and_filter_list = list()
        self._unique_fields = list()
        self.custom_filter = custom_filter
        self.known_operators = ['or', 'and', 'in', 'ne', 'eq', 'gt', 'lt', 'exists']
        self._resource = resource
        self.page = 0
        self.page_size = page_size
        self.method = FiltersMethod.AND
        self.sort = dict()
        self.join = None
        self.recursive = True

        # system only - task and assignment attributes
        self._user_query = 'true'
        self._ref_task = False
        self._ref_assignment = False
        self._ref_op = None
        self._ref_assignment_id = None
        self._ref_task_id = None
        self._system_space = None

        self._use_defaults = use_defaults
        self.__add_defaults()
        self.context = context

        if field is not None:
            self.add(field=field, values=values, operator=operator, method=method)

    def __validate_page_size(self):
        max_page_size = self.__max_page_size
        if self.page_size > max_page_size:
            logger.warning('Cannot list {} with page size greater than {}. Changing page_size to {}.'.format(
                self.resource, max_page_size, max_page_size
            ))
            self.page_size = max_page_size

    @property
    def __max_page_size(self):
        page_size = 1000
        if self.resource in [FiltersResource.EXECUTION, FiltersResource.PIPELINE_EXECUTION]:
            page_size = 100
        return page_size

    @property
    def resource(self):
        return f'{self._resource.value}' if isinstance(self._resource, FiltersResource) else f'{self._resource}'

    @resource.setter
    def resource(self, resource):
        self._resource = resource
        self.reset()
        self.__add_defaults()

    @property
    def system_space(self):
        return self._system_space

    @system_space.setter
    def system_space(self, val: bool):
        self._system_space = val

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

        :param str field: Metadata field / attribute
        :param values: field values
        :param dl.FiltersOperations operator: optional - in, gt, lt, eq, ne
        :param dl.FiltersMethod method: Optional - or/and

        **Example**:

        .. code-block:: python

            filter.add(field='metadata.user', values=['1','2'], operator=dl.FiltersOperations.IN)
        """
        if method is None:
            method = self.method
        if 'metadata.system.refs.metadata' in field and self.resource == FiltersResource.ITEM:
            logger.warning('Filtering by metadata.system.refs.metadata may cause incorrect results. please use match operator')

        # create SingleFilter object and add to self.filter_list
        if method == FiltersMethod.OR:
            self.or_filter_list.append(SingleFilter(field=field, values=values, operator=operator))
        elif method == FiltersMethod.AND:
            self.__override(field=field, values=values, operator=operator)
        else:
            raise exceptions.PlatformException(error='400',
                                               message='Unknown method {}, please select from: or/and'.format(method))

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
        generate url query params

        :param str url:
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
        is filter has field

        :param str field: field to check
        :return: Ture is have it
        :rtype: bool
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
        Pop filed

        :param str field: field to pop
        """
        for single_filter in self.or_filter_list:
            if single_filter.field == field:
                self.or_filter_list.remove(single_filter)

        for single_filter in self.and_filter_list:
            if single_filter.field == field:
                self.and_filter_list.remove(single_filter)

    def pop_join(self, field):
        """
        Pop join

        :param str field: field to pop
        """
        if self.join is not None:
            for single_filter in self.join['filter']['$and']:
                if field in single_filter:
                    self.join['filter']['$and'].remove(single_filter)

    def add_join(self, field,
                 values,
                 operator: FiltersOperations = None,
                 method: FiltersMethod = FiltersMethod.AND
                 ):
        """
        join a query to the filter

        :param str field: Metadata field / attribute
        :param str or list values: field values
        :param dl.FiltersOperations operator: optional - in, gt, lt, eq, ne
        :param method: optional - str - FiltersMethod.AND, FiltersMethod.OR

        **Example**:

        .. code-block:: python

            filter.add_join(field='metadata.user', values=['1','2'], operator=dl.FiltersOperations.IN)
        """
        if self.resource not in [FiltersResource.ITEM, FiltersResource.ANNOTATION]:
            raise exceptions.PlatformException(error='400',
                                               message='Cannot join to {} filters'.format(self.resource))

        if self.join is None:
            self.join = dict()
        if 'on' not in self.join:
            if self.resource == FiltersResource.ITEM:
                self.join['on'] = {'resource': FiltersResource.ANNOTATION.value, 'local': 'itemId', 'forigen': 'id'}
            else:
                self.join['on'] = {'resource': FiltersResource.ITEM.value, 'local': 'id', 'forigen': 'itemId'}
        if 'filter' not in self.join:
            self.join['filter'] = dict()
        join_method = '$' + method
        if join_method not in self.join['filter']:
            self.join['filter'][join_method] = list()
        self.join['filter'][join_method].append(SingleFilter(field=field, values=values, operator=operator).prepare())

    def __add_defaults(self):
        if self._use_defaults:
            # add items defaults
            if self.resource == FiltersResource.ITEM:
                self._unique_fields = ['type', 'hidden']
                self.add(field='hidden', values=False, method=FiltersMethod.AND)
                self.add(field='type', values='file', method=FiltersMethod.AND)
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
                values = [annotation_type.value for annotation_type in entities.AnnotationType]
                values.remove(entities.AnnotationType.NOTE.value)
                values += ["text", "ref_image"]  # Prompt Annotation Types
                self.add(field='type', values=values, operator=FiltersOperations.IN, method=FiltersMethod.AND)

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

        :param str operation: operation
        :param update: update
        :param bool query_only: query only
        :param system_update: system update
        :param system_metadata: True, if you want to change metadata system
        :return: dict of the filter
        :rtype: dict
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

            self.__validate_page_size()

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
                raise exceptions.PlatformException(error='400',
                                                   message='Unknown operation: {}'.format(operation))

        if self.context is not None:
            _json['context'] = self.context
        if self._system_space is not None:
            _json['systemSpace'] = self._system_space
        return _json

    def print(self, indent=2):
        print(json.dumps(self.prepare(), indent=indent))

    def sort_by(self, field, value: FiltersOrderByDirection = FiltersOrderByDirection.ASCENDING):
        """
        sort the filter

        :param str field: field to sort by it
        :param dl.FiltersOrderByDirection value: FiltersOrderByDirection.ASCENDING, FiltersOrderByDirection.DESCENDING

        **Example**:

        .. code-block:: python

            filter.sort_by(field='metadata.user', values=dl.FiltersOrderByDirection.ASCENDING)
        """
        if value not in [FiltersOrderByDirection.ASCENDING, FiltersOrderByDirection.DESCENDING]:
            raise exceptions.PlatformException(error='400', message='Sort can be by ascending or descending order only')
        self.sort[field] = value.value if isinstance(value, FiltersOrderByDirection) else value

    def platform_url(self, resource) -> str:
        """
        Build a url with filters param to open in web browser

        :param str resource: dl entity to apply filter on. currently only supports dl.Dataset
        :return: url string
        :rtype: str
        """
        _json = self.prepare()
        # add the view option
        _json['view'] = 'icons'
        # convert from enum to string
        _json["resource"] = f'{_json["resource"]}'
        # convert the dictionary to a json string
        _json['dqlFilter'] = json.dumps({'filter': _json.pop('filter'),
                                         'join': _json.pop('join', None),
                                         'sort': _json.get('sort', None)})
        # set the page size as the UI default
        _json['pageSize'] = 100
        _json['page'] = _json['page']
        # build the url for the dataset data browser
        if isinstance(resource, entities.Dataset):
            url = resource.platform_url + f'?{urllib.parse.urlencode(_json)}'
        else:
            raise NotImplementedError('Not implemented for resource type: {}'.format(type(resource)))
        return url

    def open_in_web(self, resource):
        """
        Open the filter in the platform data browser (in a new web browser)

        :param str resource: dl entity to apply filter on. currently only supports dl.Dataset
        """
        if isinstance(resource, entities.Dataset):
            resource._client_api._open_in_web(url=self.platform_url(resource=resource))
        else:
            raise NotImplementedError('Not implemented for resource type: {}'.format(type(resource)))

    def save(self, project: entities.Project, filter_name: str):
        """
        Save the current DQL filter to the project

        :param project: dl.Project
        :param filter_name: the saved filter's name
        :return: True if success
        """
        _json_filter = self.prepare()
        shebang_dict = {"type": "dql",
                        "shebang": "dataloop",
                        "metadata": {
                            "version": "1.0.0",
                            "system": {
                                "mimetype": "dql"
                            },
                            "dltype": "filter",
                            "filterFieldsState": [],
                            "resource": "items",
                            "filter": _json_filter.pop('filter'),
                            "join": _json_filter.pop('join')
                        }
                        }
        b_dataset = project.datasets._get_binaries_dataset()
        byte_io = io.BytesIO()
        byte_io.name = filter_name
        byte_io.write(json.dumps(shebang_dict).encode())
        byte_io.seek(0)
        b_dataset.items.upload(local_path=byte_io,
                               remote_path='/.dataloop/dqlfilters/items',
                               remote_name=filter_name)
        return True

    @classmethod
    def load(cls, project: entities.Project, filter_name: str) -> 'Filters':
        """
        Load a saved filter from the project by name

        :param project: dl.Project entity
        :param filter_name: filter name
        :return: dl.Filters
        """
        b_dataset = project.datasets._get_binaries_dataset()
        f = entities.Filters(custom_filter={
            'filter': {'$and': [{'filename': f'/.dataloop/dqlfilters/items/{filter_name}'}]},
            'page': 0,
            'pageSize': 1000,
            'resource': 'items'
        })
        pages = b_dataset.items.list(filters=f)
        if pages.items_count == 0:
            raise exceptions.NotFound(
                f'Saved filter not found: {filter_name}. Run `Filters.list()` to list existing filters')
        with open(pages.items[0].download()) as f:
            data = json.load(f)
            custom_filter = data['metadata']['filter']
            custom_filter['join'] = data['metadata']['join']
        return cls(custom_filter=custom_filter)

    @staticmethod
    def list(project: entities.Project) -> list:
        """
        List all saved filters for a project
        :param project: dl.Project entity
        :return: a list of all the saved filters' names
        """
        b_dataset = project.datasets._get_binaries_dataset()
        f = entities.Filters(use_defaults=False,
                             field='dir',
                             values='/.dataloop/dqlfilters/items')
        pages = b_dataset.items.list(filters=f)
        all_filter_items = list(pages.all())
        names = [i.name for i in all_filter_items]
        return names


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
        To dictionary for platform call

        :param recursive:recursive
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
            op = self.operator.value if isinstance(self.operator, FiltersOperations) else self.operator
            value['${}'.format(op)] = values
            _json[self.field] = value

        return _json

    def print(self, indent=2):
        print(json.dumps(self.prepare(), indent=indent))
