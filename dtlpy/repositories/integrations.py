"""
Integrations Repository
"""
import base64
import json
import logging
from .. import entities, exceptions, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Integrations:
    """
    Integrations Repository

    The Integrations class allows you to manage data integrations from your external storage (e.g., S3, GCS, Azure)
    into your Dataloop's Dataset storage, as well as sync data in your Dataloop's Datasets with data in your external
    storage.

    For more information on Organization Storage Integration see the `Dataloop documentation <https://dataloop.ai/docs/organization-integrations>`_  and `developers' docs <https://developers.dataloop.ai/tutorials/data_management/>`_.

    """

    def __init__(self, client_api: ApiClient, org: entities.Organization = None,
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

    @_api_reference.add(path='/orgs/{orgId}/integrations/{integrationId}', method='delete')
    def delete(self,
               integrations_id: str,
               sure: bool = False,
               really: bool = False,
               organization_id: str = None
               ) -> bool:
        """
        Delete integrations from the organization.

        **Prerequisites**: You must be an organization *owner* to delete an integration.

        :param organization_id: organization id
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
            if self.project is None and self.org is None and organization_id is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Must provide an identifier in inputs')

        if organization_id is None:
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

    @_api_reference.add(path='/orgs/{orgId}/integrations', method='post')
    def create(self,
               integrations_type: entities.IntegrationType,
               name: str,
               options: dict,
               metadata: dict = None,
               organization_id: str = None,
               ):
        """
        Create an integration between an external storage and the organization.

        **Examples for options include**:
        s3 - {key: "", secret: ""};
        gcs - {key: "", secret: "", content: ""};
        azureblob - {key: "", secret: "", clientId: "", tenantId: ""};
        key_value - {key: "", value: ""}
        aws-sts - {key: "", secret: "", roleArns: ""}
        aws-cross - {}
        gcp-cross - {}
        gcp-workload-identity-federation - {"secret": "", "content": "{}", "clientId": ""}
        private-registry (ECR) - can use generate_ecr_options to generate the options
        private-registry (GAR) - use generate_gar_options to generate the options
        private-registry (ACR) - use generate_azure_container_registry_options to generate the options
        private-registry (DockerHub) - use generate_docker_hub_options to generate the options

        **Prerequisites**: You must be an *owner* in the organization.

        :param IntegrationType integrations_type: integrations type dl.IntegrationType
        :param str name: integrations name
        :param dict options: dict of storage secrets
        :param dict metadata: metadata
        :param str organization_id: organization id
        :return: success
        :rtype: bool

        **Example**:

        .. code-block:: python

            project.integrations.create(integrations_type=dl.IntegrationType.S3,
                            name='S3Integration',
                            options={key: "Access key ID", secret: "Secret access key"})
        """

        if self.project is None and self.org is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if organization_id is None:
            if self.project is not None:
                organization_id = self.project.org.get('id')
            else:
                organization_id = self.org.id

        url_path = '/orgs/{}/integrations'.format(organization_id)
        payload = {"type": integrations_type.value if isinstance(integrations_type,
                                                                 entities.IntegrationType) else integrations_type,
                   'name': name, 'options': options}
        if metadata is not None:
            payload['metadata'] = metadata
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        else:
            integration = entities.Integration.from_json(_json=response.json(), client_api=self._client_api)
        if integration.metadata and isinstance(integration.metadata, list) and len(integration.metadata) > 0:
            for m in integration.metadata:
                if m['name'] == 'status':
                    integration_status = m['value']
                    logger.info('Integration status: {}'.format(integration_status))
        return integration

    @_api_reference.add(path='/orgs/{orgId}/integrations', method='patch')
    def update(self,
               new_name: str = None,
               integrations_id: str = None,
               integration: entities.Integration = None,
               new_options: dict = None,
               organization_id: str = None,
               reload_services: bool = None,
               ):
        """
        Update the integration's name.

        **Prerequisites**: You must be an *owner* in the organization.

        :param str new_name: new name
        :param str integrations_id: integrations id
        :param Integration integration: integration object
        :param dict new_options: new value
        :param str organization_id: organization id
        :param bool reload_services: reload services associated with this integration
        :return: Integration object
        :rtype: dtlpy.entities.integration.Integration

        **Examples for options include**:
        s3 - {key: "", secret: ""};
        gcs - {key: "", secret: "", content: ""};
        azureblob - {key: "", secret: "", clientId: "", tenantId: ""};
        key_value - {key: "", value: ""}
        aws-sts - {key: "", secret: "", roleArns: ""}
        aws-cross - {roleArn: ""}
        gcp-cross - {"email: "", "resourceName": ""}

        **Example**:

        .. code-block:: python

            project.integrations.update(integrations_id='integrations_id', new_options={roleArn: ""})
        """

        if self.project is None and self.org is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')
        if integrations_id is None and integration is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an integrations_id or integration')

        if organization_id is None:
            if self.project is not None:
                organization_id = self.project.org.get('id')
            else:
                organization_id = self.org.id

        if reload_services is None:
            logger.warning(
                "Param reload_services was not provided. If the integration you are updating is used\n"
                "in FaaS services these services will keep using the old value until updated."
            )

        url_path = '/orgs/{org_id}/integrations{query_params}'.format(
            org_id=organization_id,
            query_params='?reloadServices=true' if reload_services else ''
        )
        payload = dict(integrationId=integrations_id if integrations_id is not None else integration.id)
        if new_name is not None:
            payload['name'] = new_name
        if new_options is not None:
            if integration is None:
                integration = self.get(integrations_id=integrations_id)
            payload['credentials'] = dict(options=new_options, type=integration.type)

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return entities.Integration.from_json(_json=response.json(), client_api=self._client_api)

    @_api_reference.add(path='/orgs/{orgId}/integrations/{integrationId}', method='get')
    def get(self, integrations_id: str, organization_id: str = None):
        """
        Get organization integrations. Use this method to access your integration and be able to use it in your code.

        **Prerequisites**: You must be an *owner* in the organization.

        :param str integrations_id: integrations id
        :param str organization_id: organization id
        :return: Integration object
        :rtype: dtlpy.entities.integration.Integration

        **Example**:

        .. code-block:: python

            project.integrations.get(integrations_id='integrations_id')
        """
        if self.project is None and self.org is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if organization_id is None:
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

    @_api_reference.add(path='/orgs/{orgId}/integrations', method='get')
    def list(self, only_available=False, organization_id: str = None):
        """
        List all the organization's integrations with external storage.

        **Prerequisites**: You must be an *owner* in the organization.

        :param bool only_available: if True list only the available integrations.
        :param str organization_id: organization id
        :return: groups list
        :rtype: list

        **Example**:

        .. code-block:: python

            project.integrations.list(only_available=True)
        """
        if self.project is None and self.org is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must have an organization or project')

        if organization_id is None:
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

    @staticmethod
    def generate_gar_options(service_account: str, location: str, email: str = None) -> dict:
        """
        Generates a Google Artifact Registry JSON configuration and returns it as a base64-encoded string.

        Parameters:
            location (str): The region where the repository will be created (e.g., 'us-central1').
            service_account (str): The service_account parameter represents the Google Cloud service account credentials
                                    in the form of a JSON key file. This JSON contains the private key and other metadata
                                    required for authenticating with Google Artifact Registry. It is used to generate a Kubernetes secret
                                    that stores the credentials for pulling container images from the registry.
                                    The JSON key must include fields such as client_email, private_key, and project_id,
                                    and it is typically downloaded from the Google Cloud Console when creating the service account

        Returns:
            str: A base64-encoded string representation of the repository JSON configuration.
        """
        return IntegrationUtils.generate_gar_options(service_account=service_account, location=location, email=email)

    @staticmethod
    def generate_docker_hub_options(username: str, password: str, email: str = None) -> dict:
        """
        Generates a Docker Hub JSON configuration and returns it as a base64-encoded string.

        Parameters:
            username (str): The Docker Hub username.
            password (str): The Docker Hub password.
            email (str): Optional - Docker Hub email.

        Returns:
            str: A base64-encoded string representation of the repository JSON configuration.
        """
        return IntegrationUtils.generate_docker_hub_options(username=username, password=password, email=email)

    @staticmethod
    def generate_azure_container_registry_options(username: str, password: str, location: str) -> dict:
        """
        Generates an Azure Container Registry JSON configuration and returns it as a base64-encoded string.

        Parameters:
            username (str): The Azure username.
            password (str): The Azure password.
            location (str): server URL of Azure Container Registry

        Returns:
            str: A base64-encoded string representation of the repository JSON configuration.
        """
        return IntegrationUtils.generate_docker_hub_options(username=username, password=password, location=location)

    @staticmethod
    def generate_ecr_options(access_key_id: str, secret_access_key: str, account: str, region: str) -> dict:
        """
        Generates an Amazon Elastic Container Registry (ECR) JSON configuration and returns it as a base64-encoded string.

        Parameters:
            access_key_id (str): The AWS access key ID.
            secret_access_key (str): The AWS secret access key.
            account (str): The AWS account ID.
            region (str): The AWS region.

        Returns:
            str: A base64-encoded string representation of the repository JSON configuration.
        """
        return IntegrationUtils.generate_ecr_options(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            account=account,
            region=region
        )


class IntegrationUtils:

    @staticmethod
    def encode(st: str):
        return str(base64.b64encode(bytes(st, 'utf-8')))[2:-1]

    @staticmethod
    def generate_json_key_options(location: str, username: str, password: str, auth: str, email: str = None):
        encoded_pass = {
            "auths": {
                f"{location}": {
                    "username": username,
                    "password": password,
                    "auth": auth
                }
            }
        }

        if email:
            encoded_pass['auths'][f'{location}']['email'] = email

        return {
            "name": "_json_key",
            "spec": {
                "password": IntegrationUtils.encode(json.dumps(encoded_pass))
            }
        }

    @staticmethod
    def generate_gar_options(service_account: str, location: str, email: str = None) -> dict:

        if not service_account:
            raise ValueError('Missing Service Account')
        if not location:
            raise ValueError('Missing Location')

        username = "_json_key"
        cred = f"{username}:{service_account}"
        auth = IntegrationUtils.encode(cred)

        return IntegrationUtils.generate_json_key_options(
            location=location,
            username=username,
            password=service_account,
            auth=auth,
            email=email
        )

    @staticmethod
    def generate_docker_hub_options(username: str, password: str, email: str = None, location='docker.io') -> dict:

        if not username:
            raise ValueError('Missing Username')
        if not password:
            raise ValueError('Missing Password')

        auth = IntegrationUtils.encode('{}:{}'.format(username, password))

        return IntegrationUtils.generate_json_key_options(
            location=location,
            username=username,
            password=password,
            auth=auth,
            email=email
        )

    @staticmethod
    def generate_ecr_options(access_key_id: str, secret_access_key: str, account: str, region: str) -> dict:
        return {
            "name": "AWS",
            "spec": {
                "accessKeyId": access_key_id,
                "secretAccessKey": secret_access_key,
                "account": account,
                "region": region,
            }
        }
