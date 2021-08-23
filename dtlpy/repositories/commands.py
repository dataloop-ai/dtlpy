import logging
import time
import numpy as np

from .. import exceptions, entities, services, miscellaneous

logger = logging.getLogger(name=__name__)


class Commands:
    """
    Service Commands repository
    """

    def __init__(self, client_api: services.ApiClient):
        self._client_api = client_api

    ############
    # entities #
    ############

    def list(self):
        """
        List of commands
        :return:
        """
        url = '/commands'

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        commands = miscellaneous.List([entities.Command.from_json(_json=_json,
                                                                  client_api=self._client_api) for _json in
                                       response.json()])
        return commands

    def get(self, command_id=None, url=None) -> entities.Command:
        """
        Get Service command object

        :param command_id:
        :param url: command url
        :return: Command object
        """
        if url is None:
            url_path = "/commands/{}".format(command_id)
        else:
            url_path = url.split('v1')[1]

        success, response = self._client_api.gen_request(req_type="get",
                                                         path=url_path)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Command.from_json(client_api=self._client_api,
                                          _json=response.json())

    def wait(self, command_id, timeout=0, step=5, url=None):
        """
        Wait for command to finish

        :param command_id: Command id to wait to
        :param timeout: int, seconds to wait until TimeoutError is raised. if 0 - wait until done
        :param step: int, seconds between polling
        :param url: url to the command
        :return: Command  object
        """
        elapsed = 0
        start = int(time.time())
        if timeout is None or timeout <= 0:
            timeout = np.inf

        command = None
        while elapsed < timeout:
            command = self.get(command_id=command_id, url=url)
            if not command.in_progress():
                break
            elapsed = int(time.time()) - start
            logger.debug("Command {!r} is running for {:.2f}[s]".format(command.id, elapsed))
            sleep_time = np.minimum(timeout - elapsed, step)
            logger.debug("Going to sleep {:.2f}[s]".format(sleep_time))
            time.sleep(sleep_time)
        if command is None:
            raise ValueError('Nothing to wait for')
        if elapsed >= timeout:
            raise TimeoutError("command wait() got timeout. id: {!r}, status: {}, progress {}%".format(
                command.id, command.status, command.progress))
        if command.status != entities.CommandsStatus.SUCCESS:
            raise exceptions.PlatformException(error='424',
                                               message="Command {}: '{}'".format(command.status, command.error))
        return command

    def abort(self, command_id):
        """
        Abort Command

        :param command_id
        :return:
        """
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/commands/{}/abort'.format(command_id))

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return entities.Command.from_json(_json=response.json(),
                                              client_api=self._client_api)
