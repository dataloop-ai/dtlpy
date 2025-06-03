from enum import Enum
import logging
import attr

from .. import entities, exceptions, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class IntegrationType(str, Enum):
    """ The type of the Integration.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - S3
         - S3 Integration - for S3 drivers
       * - AWS_CROSS_ACCOUNT
         - AWS CROSS ACCOUNT Integration - for S3 drivers
       * - AWS_STS
         - AWS STS Integration - for S3 drivers
       * - GCS
         - GCS Integration - for GCS drivers
       * - GCP_CROSS_PROJECT
         - GCP CROSS PROJECT Integration - for GCP drivers
       * - AZUREBLOB
         - AZURE BLOB Integration - for S3 AZUREBLOB and AZURE_DATALAKE_GEN2 drivers
       * - KEY_VALUE
         - KEY VALUE Integration - for save secrets in the platform
       * - GCP_WORKLOAD_IDENTITY_FEDERATION
         - GCP Workload Identity Federation Integration - for GCP drivers
       * - PRIVATE_REGISTRY
         - PRIVATE REGISTRY Integration - for private registry drivers
    """
    S3 = "s3"
    AWS_CROSS_ACCOUNT = 'aws-cross'
    AWS_STS = 'aws-sts'
    GCS = "gcs"
    GCS_CROSS = "gcp-cross"
    AZUREBLOB = "azureblob"
    KEY_VALUE = "key_value"
    GCP_WORKLOAD_IDENTITY_FEDERATION = "gcp-workload-identity-federation",
    PRIVATE_REGISTRY = "private-registry"


@attr.s
class Integration(entities.BaseEntity):
    """
    Integration object
    """
    id = attr.ib()
    name = attr.ib()
    type = attr.ib()
    org = attr.ib()
    created_at = attr.ib()
    creator = attr.ib()
    update_at = attr.ib()
    url = attr.ib()
    _client_api = attr.ib(type=ApiClient, repr=False)
    metadata = attr.ib(default=None, repr=False)
    _project = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls,
                  _json: dict,
                  client_api: ApiClient,
                  is_fetched=True):
        """
        Build a Integration entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Integration object
        """
        inst = cls(id=_json.get('id', None),
                   name=_json.get('name', None),
                   creator=_json.get('creator', None),
                   created_at=_json.get('createdAt', None),
                   update_at=_json.get('updatedAt', None),
                   type=_json.get('type', None),
                   org=_json.get('org', None),
                   client_api=client_api,
                   metadata=_json.get('metadata', None),
                   url=_json.get('url', None))
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Integration)._client_api,
                                                              attr.fields(Integration)._project))
        return _json

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def update(
            self,
            new_name: str = None,
            new_options: dict = None,
            reload_services: bool = None
    ):
        """
        Update the integration's name.

        **Prerequisites**: You must be an *owner* in the organization.

        :param str new_name: new name
        :param dict new_options: new value
        :param bool reload_services: reload services associated with this integration
        :return: Integration object
        :rtype: dtlpy.entities.integration.Integration

        **Examples for options include**:
        s3 - {key: "", secret: ""};
        gcs - {key: "", secret: "", content: ""};
        azureblob - {key: "", secret: "", clientId: "", tenantId: ""};
        key_value - {key: "", value: ""}
        aws-sts - {key: "", secret: "", roleArns: ""}
        aws-cross - {roleArns: ""}

        **Example**:

        .. code-block:: python

            project.integrations.update(integrations_id='integrations_id', new_name="new_integration_name")
        """
        if self.project is not None:
            identifier = self.project
        elif self.org is not None:
            identifier = repositories.organizations.Organizations(client_api=self._client_api).get(
                organization_id=self.org)
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        identifier.integrations.update(
            new_name=new_name,
            integrations_id=self.id,
            integration=self,
            new_options=new_options,
            reload_services=reload_services
        )

    def delete(self,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete integrations from the Organization

        :param bool sure: are you sure you want to delete?
        :param bool really: really really?
        :return: True
        :rtype: bool
        """
        if self.project is not None:
            identifier = self.project
        elif self.org is not None:
            identifier = repositories.organizations.Organizations(client_api=self._client_api).get(
                organization_id=self.org)
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        return identifier.integrations.delete(integrations_id=self.id, sure=sure, really=really)
