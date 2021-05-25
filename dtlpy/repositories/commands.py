import logging
import time

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

    def get(self, command_id=None) -> entities.Command:
        """
        Get Service command object

        :param command_id:
        :return: Command object
        """
        url_path = "/commands/{}".format(command_id)

        success, response = self._client_api.gen_request(req_type="get",
                                                         path=url_path)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Command.from_json(client_api=self._client_api,
                                          _json=response.json())

    def wait(self, command_id, timeout=60):
        """
        Get Command  object

        :param timeout seconds
        :param command_id:
        :return: Command  object
        """
        wait_time = 0
        sleep_between_retries = 5
        now = int(time.time())

        command = None
        while wait_time < timeout:
            command = self.get(command_id=command_id)
            if command.in_progress():
                wait_time = int(time.time()) - now
                logger.debug("Command {} wait {} seconds".format(command.id, wait_time))
                if timeout - wait_time <= 0:
                    break
                elif timeout - wait_time <= sleep_between_retries:
                    logger.debug("Going to sleep {}".format(timeout - wait_time))
                    time.sleep(timeout - wait_time)
                else:
                    logger.debug("Going to sleep {}".format(sleep_between_retries))
                    time.sleep(sleep_between_retries)
                continue
            else:
                break

        if wait_time >= timeout:
            raise TimeoutError("command wait() got time out id: {}, status: {}, progress {}%".format(
                command.id, command.status, command.progress))
        if command.status != entities.CommandsStatus.SUCCESS:
            if command.error is not None:
                raise exceptions.PlatformException(error='409',
                                                   message="Dataset clone has been {} with error '{}'"
                                                   .format(command.status, command.error))
            else:
                raise exceptions.PlatformException(error='409',
                                                   message="Dataset clone has been {}"
                                                   .format(command.status))
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
