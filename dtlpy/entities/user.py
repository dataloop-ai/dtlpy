import traceback
import logging
import attr

from .. import miscellaneous

logger = logging.getLogger(name=__name__)


@attr.s
class User:
    """
    User entity
    """
    createdAt = attr.ib()
    updatedAt = attr.ib()
    firstName = attr.ib()
    lastName = attr.ib()
    username = attr.ib()
    avatar = attr.ib()
    email = attr.ib()
    type = attr.ib()
    org = attr.ib()
    id = attr.ib()
    # api
    project = attr.ib()

    @staticmethod
    def _protected_from_json(_json, project):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param project:
        :return:
        """
        try:
            project = User.from_json(_json=_json,
                                     project=project)
            status = True
        except Exception:
            project = traceback.format_exc()
            status = False
        return status, project

    @classmethod
    def from_json(cls, _json, project):
        """
        Build a User entity object from a json

        :param _json: _json response from host
        :param project: project entity
        :return: User object
        """
        return cls(
            createdAt=_json.get('createdAt', None),
            firstName=_json.get('firstName', None),
            updatedAt=_json.get('updatedAt', None),
            lastName=_json.get('lastName', None),
            username=_json.get('username', None),
            avatar=_json.get('avatar', None),
            email=_json.get('email', None),
            type=_json.get('type', None),
            org=_json.get('org', None),
            id=_json.get('id', None),
            project=project)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self,
                           filter=attr.filters.exclude(attr.fields(User).project))

    def print(self):
        miscellaneous.List([self]).print()
