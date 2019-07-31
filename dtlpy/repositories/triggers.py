from .. import utilities
from .. import exceptions
from .. import entities


class Triggers:
    """
    Triggers repository
    """

    def __init__(self, client_api, project):
        self.client_api = client_api
        self.project = project

    def create(self, deployment_ids, filters=None, resource=None, actions=None, active=True):
        """
        Create a Trigger

        :param deployment_ids: Id of deployments to be triggered
        :param filters: optional - Item/Annotation metadata filters, default = none
        :param resource: optional - dataset/item/annotation, default = item
        :param actions: optional - Created/Updated/Deleted, default = create
        :param active: optional - True/False, default = True
        :return: Trigger entity
        """
        # defaults
        if filters is None:
            filters = dict()
        if resource is None:
            resource = 'Item'
        if actions is None:
            actions = ['Created']
        elif not isinstance(actions, list):
            actions = [actions]

        # deployment ids
        if not isinstance(deployment_ids, list):
            deployment_ids = [deployment_ids]

        # payload
        payload = {'deploymentIds': deployment_ids,
                   'project': self.project.id,
                   'filter': filters,
                   'resource': resource,
                   'actions': actions,
                   'active': active}

        # request
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/triggers',
                                                        json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Trigger.from_json(_json=response.json(),
                                          client_api=self.client_api,
                                          project=self.project)

    def get(self, trigger_id):
        """
        Get Trigger object

        :param trigger_id:
        :return: Trigger object
        """
        # request
        success, response = self.client_api.gen_request(
            req_type="get",
            path="/triggers/{}".format(trigger_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Trigger.from_json(client_api=self.client_api,
                                          _json=response.json(),
                                          project=self.project)

    def delete(self, trigger_id):
        """
        Delete Trigger object

        :param trigger_id:
        :return: True
        """
        # request
        success, response = self.client_api.gen_request(
            req_type="delete",
            path="/triggers/{}".format(trigger_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, trigger):
        """

        :param trigger: Trigger entity
        :return: Trigger entity
        """
        assert isinstance(trigger, entities.Trigger)

        # payload
        payload = trigger.to_json()

        # request
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/triggers',
                                                        json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Trigger.from_json(_json=response.json(),
                                          client_api=self.client_api,
                                          project=self.project)

    def list(self):
        """
        List project triggers
        :return:
        """
        # request
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/triggers')
        if not success:
            raise exceptions.PlatformException(response)

        # return triggers list
        triggers = utilities.List()
        for trigger in response.json()['items']:
            triggers.append(entities.Trigger.from_json(client_api=self.client_api,
                                                       _json=trigger,
                                                       project=self.project))
        return triggers
