import logging
import time
import numpy as np
import tqdm
import warnings

from .. import exceptions, entities, services, miscellaneous

logger = logging.getLogger(name='dtlpy')

MAX_SLEEP_TIME = 8


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

        :return: list of commands
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

    def get(self,
            command_id: str = None,
            url: str = None
            ) -> entities.Command:
        """
        Get Service command object

        :param str command_id:
        :param str url: command url
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

    def wait(self, command_id, timeout=0, step=None, url=None, backoff_factor=0.1):
        """
        Wait for command to finish

        backoff_factor: A backoff factor to apply between attempts after the second try
        {backoff factor} * (2 ** ({number of total retries} - 1))
        seconds. If the backoff_factor is 0.1, then :func:`.sleep` will sleep
        for [0.0s, 0.2s, 0.4s, ...] between retries. It will never be longer
        than 8 sec

        :param str command_id: Command id to wait to
        :param int timeout: int, seconds to wait until TimeoutError is raised. if 0 - wait until done
        :param int step: int, seconds between polling
        :param str url: url to the command
        :param float backoff_factor: A backoff factor to apply between attempts after the second try
        :return: Command  object
        """
        if step is not None:
            warnings.warn(
                message='step param will be Deprecation from version 1.58.0 use backoff_factor',
                category=DeprecationWarning)
        elapsed = 0
        start = int(time.time())
        if timeout is None or timeout <= 0:
            timeout = np.inf

        command = None
        pbar = tqdm.tqdm(total=100, disable=self._client_api.verbose.disable_progress_bar)
        num_tries = 1
        while elapsed < timeout:
            command = self.get(command_id=command_id, url=url)
            pbar.update(command.progress - pbar.n)
            if not command.in_progress():
                break
            elapsed = int(time.time()) - start
            sleep_time = np.min([timeout - elapsed, backoff_factor * (2 ** (num_tries - 1)), MAX_SLEEP_TIME])
            num_tries += 1
            logger.debug(
                "Command {!r} is running for {:.2f}[s] and now Going to sleep {:.2f}[s]".format(command.id, elapsed,
                                                                                                sleep_time))
            time.sleep(sleep_time)
        pbar.close()
        if command is None:
            raise ValueError('Nothing to wait for')
        if elapsed >= timeout:
            raise TimeoutError("command wait() got timeout. id: {!r}, status: {}, progress {}%".format(
                command.id, command.status, command.progress))
        if command.status != entities.CommandsStatus.SUCCESS:
            raise exceptions.PlatformException(error='424',
                                               message="Command {}: '{}'".format(command.status, command.error))
        return command

    def abort(self, command_id: str):
        """
        Abort Command

        :param str command_id: command id
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
