from enum import Enum
import json

from .. import miscellaneous


class EntityScopeLevel(str, Enum):
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


class DlEntity(object):
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

    # def __repr__(self):
    #     string = '{}('.format(self.__class__.__name__)
    #     for prop in dir(self):
    #         if isinstance(prop, DlProperty) and prop.repr is True:
    #             string += '{}={}'.format()
    #     params = json.dumps(self._dict, indent=4)
    #     return "{}({})".format(self.__class__.__name__, params)

        # def __repr__(self):
        #     self.print()

        # def __getattribute__(self, attr):
        #     if super(BaseEntity, self).__getattribute__(attr) is None:
        #         pass
        #     return super(BaseEntity, self).__getattribute__(attr)


class DlProperty(object):
    def __init__(self, location, default=None, type=None):
        self.location = location
        self.default = default
        self.type = type

    def __get__(self, instance, owner):
        _dict = instance._dict
        for key in self.location[:-1]:
            _dict = _dict.get(key, dict())
        value = _dict.get(self.location[-1], self.default)
        isinstance(value, self.type)
        return value

    def __set__(self, instance, value):
        _dict = instance._dict
        for key in self.location[:-1]:
            _dict = _dict.get(key, dict())
        _dict[self.location[-1]] = value
