"""
Messages Repository
"""
import json
import logging
from urllib.parse import urlencode, quote
from .. import entities, miscellaneous, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Messages:
    """
    Messages Repository

    The Messages class allows the user to manage Messages.
    """

    def __init__(self, client_api: ApiClient):
        self._client_api = client_api

    # @_api_reference.add(path='/inbox/message/user', method='get')
    def _list(self, context: entities.NotificationEventContext = None, checkpoint: dict = None, new_only=True) -> \
            miscellaneous.List[entities.Message]:
        """
        Get messages by context.

        :param str context: Message context
        :param dict checkpoint: checkpoint
        :param bool new_only: get only new messages
        :return: List of Messages
        :rtype: list

        **Example**:

        .. code-block:: python

            messages = dl.messages.list(context={project: id})
        """
        user = self._client_api.info()['user_email']

        if not user:
            raise exceptions.PlatformException(error='400',
                                               message='No user in JWT, please login')

        url = '/inbox/message/user/{}'.format(user)

        query_params = {
            'newOnly': new_only,
            'checkpointPagination': {
                "pageSize": 1000,
                "sort": {"key": "id", "direction": "descending"}
            }
        }

        context_extent = None

        if context:
            context_extent = "contextExtent=" + quote(json.dumps(context).replace(" ", ""), safe=":,").strip()

        if checkpoint:
            query_params['checkpointPagination']['checkpoint'] = checkpoint

        checkpoint_pagination = "checkpointPagination=" + quote(
            json.dumps(query_params['checkpointPagination']).replace(" ", ""), safe=":,").strip()

        url = "{}?{}".format(url, checkpoint_pagination)

        if context_extent:
            url = "{}&{}".format(url, context_extent)

        success, response = self._client_api.gen_request(req_type='get', path=url)

        if success:
            pool = self._client_api.thread_pools('entity.create')
            message_json = response.json()
            items = message_json.get('items', list())
            jobs = [None for _ in range(len(items))]
            for i_message, message in enumerate(items):
                jobs[i_message] = pool.submit(
                    entities.Message._protected_from_json,
                    **{'client_api': self._client_api, '_json': message}
                )

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            messages = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            raise exceptions.PlatformException(response)
        return messages
