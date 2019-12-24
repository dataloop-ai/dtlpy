import logging
from .. import entities, miscellaneous, PlatformException

logger = logging.getLogger(name=__name__)


class Bots:
    """
    Bots repository
    """

    def __init__(self, client_api, project):
        self._client_api = client_api
        self.project = project

    def list(self):
        """
        Get project's bots list.
        :return: List of Bots objects
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/bots'.format(self.project.id))

        if success:
            bots_json = response.json()
            pool = self._client_api.thread_pools(pool_name='entity.create')
            jobs = [None for _ in range(len(bots_json))]
            # return triggers list
            for i_bot, bot in enumerate(bots_json):
                jobs[i_bot] = pool.apply_async(entities.Bot._protected_from_json,
                                               kwds={'project': self.project,
                                                     '_json': bot})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all results
            results = [j.get() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            bots = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.exception('Platform error getting bots')
            raise PlatformException(response)
        return bots

    def get(self, bot_name=None, bot_id=None):
        """
        Get a Bot object
        :param bot_name: get bot by name
        :param bot_id: get bot by id
        :return: Bot object

        """
        if bot_id is not None:
            success, response = self._client_api.gen_request(req_type='post',
                                                             path='/projects/{}/bots/{}'.format(self.project.id,
                                                                                                bot_id))
            if success:
                bot = entities.Bot.from_json(_json=response.json(),
                                             project=self.project)
            else:
                raise PlatformException(response)
        elif bot_name is not None:
            bots = self.list()
            bot = [bot for bot in bots if bot.name == bot_name]
            if not bot:
                # list is empty
                raise PlatformException('404', 'Bot not found. Name: {}'.format(bot_name))
                # project = None
            elif len(bot) > 1:
                # more than one matching project
                raise PlatformException('404', 'More than one bot with same name. Please "get" by id')
            else:
                bot = bot[0]
        else:
            raise PlatformException('400', 'Must choose by "bot_id" or "bot_name"')
        assert isinstance(bot, entities.Bot)
        return bot

    def delete(self, bot_id=None):
        """
        Delete a Bot
        :param bot_id: bot id to delete
        :return: True
        """
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path='/projects/{}/bots/{}'.format(self.project.id,
                                                                                            bot_id))
        if not success:
            raise PlatformException(response)
        logger.info('Bot {} deleted successfully'.format(bot_id))
        return True

    def create(self, name):
        """
        Create a new Bot
        :return: Bot object
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/bots'.format(self.project.id),
                                                         json_req={'name': name})
        if success:
            bot = entities.Bot.from_json(_json=response.json(),
                                         project=self.project)
        else:
            raise PlatformException(response)
        assert isinstance(bot, entities.Bot)
        return bot
