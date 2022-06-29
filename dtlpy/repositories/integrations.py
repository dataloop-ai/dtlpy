"""
Integrations Repository
"""

import logging
from .. import entities, exceptions, services, miscellaneous

logger = logging.getLogger(name='dtlpy')


class Integrations:
    """
    Integrations Repository

    The Integrations class allows you to manage data integrtion from your external storage (e.g., S3, GCS, Azure) into your Dataloop's Dataset storage, as well as sync data in your Dataloop's Datasets with data in your external storage.

    For more information on Organization Storgae Integration see the `Dataloop documentation <https://dataloop.ai/docs/organization-integrations>`_  and `SDK External Storage <https://dataloop.ai/docs/sdk-sync-storage>`_.

    """

    def __init__(self, client_api: services.ApiClient, org: entities.Organization = None,
                 project: entities.Project = None):
        self._client_api = client_api
        self._org = org
        self._project = project

    @property
    def project(self) -> entities.Project:
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def org(self) -> entities.Organization:
        if self._org is None:
            if self.project is not None:
                self._org = entities.Organization.from_json(_json=self.project.org, client_api=self._client_api)
        return self._org

    @org.setter
    def org(self, org: entities.Organization):
        if not isinstance(org, entities.Organization):
            raise ValueError('Must input a valid Organization entity')
        self._org = org

    def delete(self,
               integrations_id: str,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete integrations from the organization.

        **Prerequisites**: You must be an organization *owner* to delete an integration.

        :param str integrations_id: integrations id
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: success
        :rtype: bool

        **Example**:

        .. code-block:: python

            project.integrations.delete(integrations_id='integrations_id', sure=True, really=True)
        """
        if sure and really:
            if self.project is None and self.org is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Must provide an identifier in inputs')

            if self.project is not None:
                organization_id = self.project.org.get('id')
            else:
                organization_id = self.org.id

            url_path = '/orgs/{}/integrations/{}'.format(organization_id, integrations_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path=url_path)
            if not success:
                raise exceptions.PlatformException(response)
            else:
                return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete integrations from SDK. Please login to platform to delete')

    def create(self,
               integrations_type: entities.ExternalStorage,
               name: str,
               options: dict):
        """
        Create an integration between an external storage and the organization.

        **Examples for options include**:
        s3 - {key: "", secret: ""};
        gcs - {key: "", secret: "", content: ""};
        azureblob - {key: "", secret: "", clientId: "", tenantId: ""};
        key_value - {key: "", value: ""}
        aws-sts - {key: "", secret: "", roleArns: ""}

        **Prerequisites**: You must be an *owner* in the organization.

        :param str integrations_type: integrations type dl.ExternalStorage
        :param str name: integrations name
        :param dict options: dict of storage secrets
        :return: success
        :rtype: bool

        **Example**:

        .. code-block:: python

            project.integrations.create(integrations_type=dl.ExternalStorage.S3,
                            name='S3ntegration',
                            options={key: "Access key ID", secret: "Secret access key"})
        """

        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if self.project is not None:
            organization_id = self.project.org.get('id')
        else:
            organization_id = self.org.id

        url_path = '/orgs/{}/integrations'.format(organization_id)
        payload = {"type": integrations_type, 'name': name, 'options': options}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return entities.Integration.from_json(_json=response.json(), client_api=self._client_api)

    def update(self,
               new_name: str,
               integrations_id: str):
        """
        Update the integration's name.

        **Prerequisites**: You must be an *owner* in the organization.

        :param str new_name: new name
        :param str integrations_id: integrations id
        :return: Integration object
        :rtype: dtlpy.entities.integration.Integration

        **Example**:

        .. code-block:: python

            project.integrations.update(integrations_id='integrations_id', new_name="new_integration_name")
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if self.project is not None:
            organization_id = self.project.org.get('id')
        else:
            organization_id = self.org.id

        url_path = '/orgs/{}/integrations/'.format(organization_id)
        payload = dict(name=new_name, id=integrations_id)

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return entities.Integration.from_json(_json=response.json(), client_api=self._client_api)

    def get(self, integrations_id: str):
        """
        Get organization integrations. Use this method to access your integration and be able to use it in your code.

        **Prerequisites**: You must be an *owner* in the organization.

        :param str integrations_id: integrations id
        :return: Integration object
        :rtype: dtlpy.entities.integration.Integration

        **Example**:

        .. code-block:: python

            project.integrations.get(integrations_id='integrations_id')
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if self.project is not None:
            organization_id = self.project.org.get('id')
        else:
            organization_id = self.org.id

        url_path = '/orgs/{}/integrations/{}'.format(organization_id, integrations_id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)
        return entities.Integration.from_json(_json=response.json(), client_api=self._client_api)

    def list(self, only_available=False):
        """
        List all the organization's integrations with external storage.

        **Prerequisites**: You must be an *owner* in the organization.

        :param bool only_available: if True list only the available integrations.
        :return: groups list
        :rtype: list

        **Example**:

        .. code-block:: python

            project.integrations.list(only_available=True)
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if self.project is not None:
            organization_id = self.project.org.get('id')
        else:
            organization_id = self.org.id

        if only_available:
            url_path = '/orgs/{}/availableIntegrations'.format(organization_id)
        else:
            url_path = '/orgs/{}/integrations'.format(organization_id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        available_integrations = miscellaneous.List(response.json())
        return available_integrations
