import traceback
import logging
import attr

from .. import miscellaneous, entities

logger = logging.getLogger(name=__name__)


@attr.s
class Bot(entities.User):
    """
    Bot entity
    """

    def delete(self):
        """
        Delete the bot

        :return: True
        """
        return self.project.bots.delete(bot_id=self.id)
