import attr
import traceback
from enum import Enum
from collections import namedtuple

from .. import repositories, entities, services


class CommandsStatus(str, Enum):
    CREATED = 'created'
    MAKING_CHILDREN = 'making-children'
    WAITING_CHILDREN = 'waiting-children'
    IN_PROGRESS = 'in-progress'
    ABORTED = 'aborted'
    CANCELED = 'canceled'
    FINALIZING = 'finalizing'
    SUCCESS = 'success'
    FAILED = 'failed'
    TIMEOUT = 'timeout'


@attr.s
class Command(entities.BaseEntity):
    """
    Com entity
    """
    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    status = attr.ib()
    created_at = attr.ib()
    updated_at = attr.ib()
    type = attr.ib()
    progress = attr.ib()
    spec = attr.ib()
    error = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['commands'])

        commands_repo = repositories.Commands(client_api=self._client_api)

        r = reps(commands=commands_repo)
        return r

    @property
    def commands(self):
        assert isinstance(self._repositories.commands, repositories.Commands)
        return self._repositories.commands

    @staticmethod
    def _protected_from_json(_json, client_api, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform json
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        try:
            command = Command.from_json(_json=_json,
                                        client_api=client_api,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            command = traceback.format_exc()
            status = False
        return status, command

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Command entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Command object
        """
        inst = cls(
            id=_json.get('id', None),
            url=_json.get('url', None),
            status=_json.get('status', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            type=_json.get('type', None),
            progress=_json.get('progress', None),
            spec=_json.get('spec', None),
            error=_json.get('error', None),
            client_api=client_api
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Command)._client_api,
                                                              attr.fields(Command).created_at,
                                                              attr.fields(Command).updated_at))
        # rename
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at

        return _json

    def abort(self):
        """
        abort command

        :return:
        """
        return self.commands.abort(command_id=self.id)

    def in_progress(self):
        """
        Check if command is still in one of the in progress statuses

        :return: Boolean
        """
        return self.status in [entities.CommandsStatus.CREATED,
                               entities.CommandsStatus.MAKING_CHILDREN,
                               entities.CommandsStatus.WAITING_CHILDREN,
                               entities.CommandsStatus.FINALIZING,
                               entities.CommandsStatus.IN_PROGRESS]

    def wait(self, timeout=0, step=5):
        """
        Wait for Command to finish

        :param timeout: int, seconds to wait until TimeoutError is raised. if 0 - wait until done
        :param step: int, seconds between polling
        :return: Command  object
        """
        if not self.in_progress():
            return self

        return self.commands.wait(command_id=self.id,
                                  timeout=timeout,
                                  step=step)
