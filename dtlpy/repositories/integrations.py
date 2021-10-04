"""
Integrations Repository
"""

import logging
from .. import entities, exceptions, services, miscellaneous

logger = logging.getLogger(name=__name__)


class Integrations:
    """
    Datasets repository
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

    def delete(self, integrations_id: str,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete integrations from the Organization
        :param integrations_id:
        :param sure: are you sure you want to delete?
        :param really: really really?
        :return: True
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

    def create(self, integrations_type, name, options):
        """
        Add integrations to the Organization
        :param integrations_type: "s3" , "gcs", "azureblob"
        :param name: integrations name
        :param options: s3 - {key: "", secret: ""},
                        gcs - {key: "", secret: "", content: ""},
                        azureblob - {key: "", secret: "", clientId: "", tenantId: ""}
        :return: True
        """

        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

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

    def update(self, new_name: str):
        """
        Update the integrations name
        :param new_name:
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if self.project is not None:
            organization_id = self.project.org.get('id')
        else:
            organization_id = self.org.id

        url_path = '/orgs/{}/integrations/'.format(organization_id)
        payload = dict(name=new_name)

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return entities.Integration.from_json(_json=response.json(), client_api=self._client_api)

    def get(self, integrations_id: str):
        """
        get organization integrations
        :param integrations_id:
        :return organization integrations:
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

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
        list all organization integrations
        :param only_available: bool - if True list only the available integrations
        :return groups list:
        """
        if self.project is None and self.org is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

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
