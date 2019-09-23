from .. import exceptions, entities, utilities
import logging

logger = logging.getLogger(name=__name__)


class Sessions:
    """
    Deployment Sessions repository
    """

    def __init__(self, client_api, deployment=None):
        self._deployment = deployment
        self.client_api = client_api

    @property
    def deployment(self):
        assert isinstance(self._deployment, entities.Deployment)
        return self._deployment

    def create(self, deployment_id=None, sync=False, session_input=None,
               resource='item', item_id=None, dataset_id=None):
        """
        Create deployment entity
        :param item_id:
        :param resource:
        :param sync:
        :param deployment_id:
        :param session_input:
        :param dataset_id:
        :return:
        """
        if deployment_id is None:
            if self.deployment is None:
                raise exceptions.PlatformException('400', 'Please provide deployment id')
            deployment_id = self.deployment.id

        # payload
        if session_input is None:
            payload = {resource: {
                'item_id': item_id,
                'dataset_id': dataset_id}
            }
        else:
            payload = session_input

        # request url
        url_path = '/deployment_sessions/{deployment_id}'.format(deployment_id=deployment_id)
        if sync:
            url_path += '?sync=true'

        # request
        success, response = self.client_api.gen_request(req_type='post',
                                                        path=url_path,
                                                        json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Session.from_json(_json=response.json(),
                                          client_api=self.client_api,
                                          deployment=self.deployment)

    def list(self):
        """
        List deployment sessions
        :return:
        """
        url_path = '/deployment_sessions'

        if self.deployment is not None:
            url_path += '/{}'.format(self.deployment.id)

        # request
        success, response = self.client_api.gen_request(req_type='get',
                                                        path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        # return triggers list
        if self.deployment is None:
            logging.warning('Listing deployment sessions without deployment entity will return deployment'
                            ' session objects with no deployment.\nto properly list deployment sessions use '
                            'deployment.deployment_sessions.list() method')
        sessions = utilities.List()
        for deployment_session in response.json()['items']:
            sessions.append(entities.Session.from_json(client_api=self.client_api,
                                                       _json=deployment_session,
                                                       deployment=self.deployment))
        return sessions

    def get(self, session_id=None):
        """
        Get Deployment session object

        :param session_id:
        :return: Deployment session object
        """
        # get by id
        # request
        success, response = self.client_api.gen_request(
            req_type="get",
            path="/deployment_sessions/{}".format(session_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Session.from_json(client_api=self.client_api,
                                          _json=response.json(),
                                          deployment=self.deployment)

    def progress_update(self, session_id, status=None, percent_complete=None, message=None, output=None):
        """
        Update Session Progress

        :param session_id:
        :param status:
        :param percent_complete:
        :param message:
        :param output:
        :return:
        """
        # create payload
        payload = dict()
        if status is not None:
            payload['status'] = status
        if percent_complete is not None:
            payload['percentComplete'] = percent_complete
        if message is not None:
            payload['message'] = message
        if output is not None:
            payload['output'] = output

        # request
        success, response = self.client_api.gen_request(
            req_type="post",
            path="/deployment_sessions/{}/progress".format(session_id),
            json_req=payload
        )

        # exception handling
        if success:
            return entities.Session.from_json(_json=response.json(),
                                              client_api=self.client_api,
                                              deployment=self.deployment)
        else:
            raise exceptions.PlatformException(response)
