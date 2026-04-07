import functools
import logging
import enum

from .. import miscellaneous

logger = logging.getLogger('dtlpy')


class EntityScopeLevel(str, enum.Enum):
    PRIVATE = 'private',
    PROJECT = 'project',
    ORG = 'org',
    PUBLIC = 'public'


class BaseEntity(object):
    is_fetched = True

    def print(self, to_return=False, columns=None):
        """
        :param to_return:
        :param columns:
        """
        return miscellaneous.List([self]).print(to_return=to_return, columns=columns)

    def to_df(self, show_all=False, columns=None):
        """
        :param show_all:
        :param columns:
        """
        return miscellaneous.List([self]).to_df(show_all=show_all, columns=columns)


# for auto-complete
from typing import TYPE_CHECKING

RUNTIME = not TYPE_CHECKING
if RUNTIME:
    def base_model(model):
        return model
else:
    from dataclasses import dataclass as base_model


class DlList(list):
    def __init__(self, _list=None, _dict=None, _type=None):
        if _list is None:
            _list = list()
        if _dict is None:
            _dict = list()
        self._dict = _dict
        self._type = _type
        super(DlList, self).__init__(_list)

    def append(self, item) -> None:
        if self._type is not None:
            assert isinstance(item, self._type), f'Cannot append type: {type(item)}. Must be type {self._type}'
        self._dict.append(item.to_json())
        super(DlList, self).append(item)  # append the item to itself (the list)


@base_model
class DlEntity(object):
    is_fetched = True
    _enable_lazy_fetch = False  # Enable lazy fetch feature (override in subclasses)
    _id_param = None  # Parameter name for entity ID in repository.get() (e.g., 'project_id', 'dataset_id')
    _client_api = None  # ApiClient instance (set via __init__ kwargs)

    def __init__(self, _dict=None, **kwargs):
        # using dict by reference and not creating a new one each time
        if _dict is None:
            _dict = dict()
        self._dict = _dict
        self.is_fetched = kwargs.pop('is_fetched', True)
        # this will set all the inputs to right location (using the dl.Property definitions)
        for key, value in kwargs.items():
            if key == "_dict":
                self._dict.update(value.copy())
            else:
                self.__setattr__(key, value)
        self._set_defaults()

    def _set_defaults(self):
        # getting all attribute (that are DlProperty) to set defaults to _dict
        # https://stackoverflow.com/questions/21962769/is-it-possible-to-test-if-object-property-uses-a-descriptor
        if self._enable_lazy_fetch and not self.is_fetched:
            return
        for cls in type(self).__mro__:
            for att, a_type in cls.__dict__.items():
                if isinstance(a_type, DlProperty):
                    _ = self.__getattribute__(att)

    def _get_entity_repository_obj(self):
        """
        Return the repository object used to fetch this entity's data.
        
        Subclasses that enable lazy fetch should override this to return the
        appropriate repository (e.g. self.projects for Project).
        Returning None means lazy fetch is not supported.
        """
        return None

    def _get_entity_data(self):
        """
        Generic method to fetch the whole entity from platform.
        
        Calls _get_entity_repository_obj() to obtain the repository lazily,
        avoiding eager initialization of all repositories at entity construction time.
        
        Returns:
            dict: Full entity data to merge into _dict, or None if fetch fails
        """
        if self._id_param is None:
            return None

        repo = self._get_entity_repository_obj()
        if repo is None:
            return None

        entity_id = self._dict.get('id') if isinstance(self._dict, dict) else None
        get_kwargs = {
            'fetch': True,
            self._id_param: entity_id,
        }
        entity = repo.get(**get_kwargs)
        if entity:
            return entity.to_json()
        return None

    def to_json(self):
        """
        Returns platform JSON format of entity.

        Triggers lazy fetch if entity was not fully fetched yet,
        ensuring the returned dict contains the complete data.

        :return: platform json dict
        :rtype: dict
        """
        if self._enable_lazy_fetch and not self.is_fetched:
            fetched_data = self._get_entity_data()
            if isinstance(fetched_data, dict):
                self._dict.update(fetched_data)
                self.is_fetched = True
                self._set_defaults()
        return self._dict.copy()

    def print(self, to_return=False, columns=None):
        """
        :param to_return:
        :param columns:
        """
        return miscellaneous.List([self]).print(to_return=to_return, columns=columns)

    def to_df(self, show_all=False, columns=None):
        """
        :param show_all:
        :param columns:
        """
        return miscellaneous.List([self]).to_df(show_all=show_all, columns=columns)


class DlProperty:
    def __init__(self, location=None, default='NODEFAULT', _type=None, _kls=None):
        self.location = location
        self._default = default
        self._type = _type
        self._validator = None
        self._kls = _kls

    ##############
    # decorators #
    ##############
    def default(self, method=None):
        @functools.wraps(method)
        def _default(self):
            return method(self)

        self._default = _default
        return self._default

    def validator(self, method):
        @functools.wraps(method)
        def _validator(self, value):
            return method(self, value)

        self._validator = _validator
        return self._validator

    ############
    # privates #
    ############
    @staticmethod
    def _get_class(kls):
        import importlib
        module = importlib.import_module(f'.entities', package='dtlpy')
        kls = getattr(module, kls)
        return kls

    def _get_default(self, instance):
        if callable(self._default):
            default = self._default(self=instance)
        else:
            default = self._default
        return default

    def _to_dict(self, inst):
        if self._kls is not None:
            if isinstance(inst, list) and all(hasattr(v, 'to_json') for v in inst):
                _dict = [v.to_json() for v in inst]
            elif hasattr(inst, 'to_json'):
                _dict = inst.to_json()
            else:
                _dict = inst
        else:
            _dict = inst
        return _dict

    def _to_instance(self, _dict):
        if self._kls is not None:
            kls = self._get_class(kls=self._kls)
            if isinstance(_dict, list) and all(isinstance(v, dict) for v in _dict):
                value = DlList(_list=[kls.from_json(v) for v in _dict],
                               _type=kls,
                               _dict=_dict)
            elif isinstance(_dict, dict):
                value = kls(_dict=_dict, **_dict)
            else:
                value = _dict
        else:
            value = _dict
        return value

    def _navigate_to_parent(self, root_dict):
        """Walk nested dicts along self.location to reach the parent of the target key."""
        _dict = root_dict
        for key in self.location[:-1]:
            _dict = _dict.get(key, dict())
        return _dict

    def _resolve_missing_key(self, instance, parent_dict):
        """
        Resolve a missing key via lazy fetch or default value.

        Attempts lazy fetch first (if enabled and entity not yet fetched).
        Falls back to the configured default otherwise.
        Stores the resolved value into parent_dict unless it is NODEFAULT.

        :return: the resolved value ready for _to_instance
        """
        target_key = self.location[-1]
        value_found = False

        if instance._enable_lazy_fetch and not instance.is_fetched:
            fetched_data = instance._get_entity_data()
            if isinstance(fetched_data, dict):
                instance._dict.update(fetched_data)
                instance.is_fetched = True
                instance._set_defaults()
                parent_dict = self._navigate_to_parent(instance._dict)
                if target_key in parent_dict:
                    value = parent_dict[target_key]
                    value_found = True

        if not value_found:
            value = self._get_default(instance=instance)

        if value == 'NODEFAULT':
            value = None
        else:
            parent_dict[target_key] = value

        return value

    def __get__(self, instance, owner):
        if instance is None:
            return self

        parent_dict = self._navigate_to_parent(instance._dict)
        target_key = self.location[-1]

        if target_key in parent_dict:
            value = parent_dict[target_key]
        else:
            value = self._resolve_missing_key(instance, parent_dict)

        return self._to_instance(_dict=value)

    def __set__(self, instance, value):

        # validate - if validator is set
        if self._validator is not None:
            # instantiate the value before validation
            inst = self._to_instance(_dict=value)
            self._validator(self=instance, value=inst)

        # convert to the value's kls
        value = self._to_dict(inst=value)

        # set value in the dictionary
        _dict = instance._dict
        for key in self.location[:-1]:
            _tmp_dict = _dict.get(key, None)
            # create the dict inside to be able to point
            if _tmp_dict is None:
                _dict[key] = dict()
            _dict = _dict.get(key, None)
        _dict[self.location[-1]] = value
