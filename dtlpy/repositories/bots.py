import logging
from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name='dtlpy')


class Bots:
    """
    Bots repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project):
        self._client_api = client_api
        self._project = project

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.bots repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def list(self) -> miscellaneous.List[entities.Bot]:
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
                jobs[i_bot] = pool.submit(entities.Bot._protected_from_json,
                                          **{'project': self.project,
                                             'bots': self,
                                             'client_api': self._client_api,
                                             '_json': bot})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            bots = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.error('Platform error getting bots')
            raise exceptions.PlatformException(response)
        return bots

    def get(self, bot_email=None, bot_id=None, bot_name=None):
        """
        Get a Bot object
        :param bot_email: get bot by email
        :param bot_id: get bot by id
        :param bot_name: get bot by name
        :return: Bot object

        """
        if bot_id is None:
            if bot_name is not None:
                bots = self.list()
                bot = [bot for bot in bots if bot.name == bot_name]

            elif bot_email is not None:
                bots = self.list()
                bot = [bot for bot in bots if bot.email == bot_email]
            else:
                raise exceptions.PlatformException('400', 'Must choose by "bot_id" or "bot_name"')
            if not bot:
                # list is empty
                raise exceptions.PlatformException('404', 'Bot not found. Name: {}'.format(bot_email))
                # project = None
            elif len(bot) > 1:
                # more than one matching project
                raise exceptions.PlatformException('404', 'More than one bot with same name. Please "get" by id')
            else:
                bot_id = bot[0].id

        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/bots/{}'.format(self.project.id,
                                                                                            bot_id))
        if success:
            bot = entities.Bot.from_json(_json=response.json(),
                                         project=self.project,
                                         bots=self, client_api=self._client_api)
            # verify input bot name and bot email are same as the given id
            if bot_name is not None and bot.name != bot_name:
                logger.warning(
                    "Mismatch found in bots.get: bot_name is different then bot.name: "
                    "{!r} != {!r}".format(
                        bot_name,
                        bot.name))
            if bot_email is not None and bot.email != bot_email:
                logger.warning(
                    "Mismatch found in bots.get: bot_email is different then bot.email: "
                    "{!r} != {!r}".format(
                        bot_email,
                        bot.email))
        else:
            raise exceptions.PlatformException(response)

        assert isinstance(bot, entities.Bot)
        return bot

    def delete(self, bot_id=None, bot_email=None):
        """
        Delete a Bot
        :param bot_id: bot id to delete
        :param bot_email: bot email to delete
        :return: True
        """
        if bot_id is None:
            if bot_email is None:
                raise exceptions.PlatformException(error='400',
                                                   message='must input one of bot_id or bot_email to delete')
            bot = self.get(bot_email=bot_email)
            bot_id = bot.id
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path='/projects/{}/bots/{}'.format(self.project.id,
                                                                                            bot_id))
        if not success:
            raise exceptions.PlatformException(response)
        logger.info('Bot {} deleted successfully'.format(bot_id))
        return True

    def create(self, name, return_credentials: bool = False):
        """
        Create a new Bot
        :param name:
        :param return_credentials: with True well return the password when create
        :return: Bot object
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/bots'.format(self.project.id),
                                                         json_req={'name': name,
                                                                   'returnCredentials': return_credentials})
        if success:
            bot = entities.Bot.from_json(_json=response.json(),
                                         project=self.project,
                                         bots=self, client_api=self._client_api)
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(bot, entities.Bot)
        return bot
