import traceback
import logging
import attr

from .. import entities, exceptions

logger = logging.getLogger(name=__name__)


@attr.s
class User(entities.BaseEntity):
    """
    User entity
    """
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    name = attr.ib()
    last_name = attr.ib()
    username = attr.ib()
    avatar = attr.ib(repr=False)
    email = attr.ib()
    role = attr.ib()
    type = attr.ib()
    org = attr.ib()
    id = attr.ib()

    # api
    _project = attr.ib(repr=False)
    _client_api = attr.ib(default=None, repr=False)
    _users = attr.ib(repr=False, default=None)

    @staticmethod
    def _protected_from_json(_json, project, client_api, users=None):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform json
        :param project: project entity
        :param client_api: ApiClient entity
        :param users: Users repository
        :return:
        """
        try:
            user = User.from_json(_json=_json,
                                  project=project,
                                  users=users,
                                  client_api=client_api)
            status = True
        except Exception:
            user = traceback.format_exc()
            status = False
        return status, user

    @property
    def project(self):
        if self._project is None:
            raise exceptions.PlatformException(error='2001',
                                               message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    @classmethod
    def from_json(cls, _json, project, client_api, users=None):
        """
        Build a User entity object from a json

        :param _json: _json response from host
        :param project: project entity
        :param client_api: ApiClient entity
        :param users: Users repository
        :return: User object
        """
        return cls(
            createdAt=_json.get('createdAt', None),
            name=_json.get('firstName', None),
            updatedAt=_json.get('updatedAt', None),
            last_name=_json.get('lastName', None),
            username=_json.get('username', None),
            avatar=_json.get('avatar', None),
            email=_json.get('email', None),
            role=_json.get('role', None),
            type=_json.get('type', None),
            org=_json.get('org', None),
            id=_json.get('id', None),
            project=project,
            users=users,
            client_api=client_api)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(User)._project,
                                                        attr.fields(User).name,
                                                        attr.fields(User)._client_api,
                                                        attr.fields(User).users,
                                                        attr.fields(User).last_name))
        _json['firstName'] = self.name
        _json['lastName'] = self.last_name
        return _json
