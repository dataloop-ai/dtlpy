import logging
import attr
from enum import Enum
from collections import namedtuple
from .. import entities, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class ExternalStorage(str, Enum):
    """ The type of the Integration.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - S3
         - AWS S3 drivers
       * - GCS
         - Google GCS drivers
       * - AZUREBLOB
         - Microsoft AZURE BLOB drivers
       * - AZURE_DATALAKE_GEN2
         - Microsoft AZURE GEN2 drivers
    """
    S3 = "s3"
    GCS = "gcs"
    AZUREBLOB = "azureblob"
    AZURE_DATALAKE_GEN2 = 'azureDatalakeGen2'
    KEY_VALUE = "key_value"
    AWS_STS = 'aws-sts'


@attr.s()
class Driver(entities.BaseEntity):
    """
    Driver entity
    """
    creator = attr.ib()
    allow_external_delete = attr.ib()
    allow_external_modification = attr.ib()
    created_at = attr.ib()
    type = attr.ib()
    integration_id = attr.ib()
    integration_type = attr.ib()
    metadata = attr.ib(repr=False)
    name = attr.ib()
    id = attr.ib()
    path = attr.ib()
    # api
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['drivers'])
        return reps(
            drivers=repositories.Drivers(client_api=self._client_api),
        )

    @property
    def drivers(self):
        assert isinstance(self._repositories.drivers, repositories.Drivers)
        return self._repositories.drivers

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Driver entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Driver object
        """
        inst = cls(creator=_json.get('creator', None),
                   allow_external_delete=_json.get('allowExternalDelete', None),
                   allow_external_modification=_json.get('allowExternalModification', None),
                   created_at=_json.get('createdAt', None),
                   type=_json.get('type', None),
                   integration_id=_json.get('integrationId', None),
                   integration_type=_json.get('integrationType', None),
                   metadata=_json.get('metadata', None),
                   name=_json.get('name', None),
                   id=_json.get('id', None),
                   client_api=client_api,
                   path=_json.get('path', None))

        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        output_dict = attr.asdict(self,
                                  filter=attr.filters.exclude(attr.fields(Driver)._client_api,
                                                              attr.fields(Driver).allow_external_delete,
                                                              attr.fields(Driver).allow_external_modification,
                                                              attr.fields(Driver).created_at,
                                                              attr.fields(Driver).integration_id,
                                                              attr.fields(Driver).integration_type,
                                                              attr.fields(Driver).path
                                                              ))
        output_dict['allowExternalDelete'] = self.allow_external_delete
        output_dict['allowExternalModification'] = self.allow_external_modification
        output_dict['createdAt'] = self.created_at
        output_dict['integrationId'] = self.integration_id
        output_dict['integrationType'] = self.integration_type

        if self.path is not None:
            output_dict['path'] = self.path

        return output_dict

    def delete(self, sure=False, really=False):
        """
        Delete a driver forever!

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param bool sure: are you sure you want to delete?
        :param bool really: really really?
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            driver.delete(sure=True, really=True)
        """
        return self.drivers.delete(driver_id=self.id,
                                   sure=sure,
                                   really=really)


@attr.s()
class AzureBlobDriver(Driver):
    container_name = attr.ib(default=None)

    def to_json(self):
        _json = super().to_json()
        _json['containerName'] = self.container_name
        return _json

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Driver entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Driver object
        """
        inst = super().from_json(_json, client_api, is_fetched=True)
        inst.container_name = _json.get('containerName', None)
        return inst


@attr.s()
class GcsDriver(Driver):
    bucket = attr.ib(default=None)

    def to_json(self):
        _json = super().to_json()
        _json['bucket'] = self.bucket
        return _json

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Driver entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Driver object
        """
        inst = super().from_json(_json, client_api, is_fetched=True)
        inst.bucket = _json.get('bucket', None)
        return inst


@attr.s()
class S3Driver(Driver):
    bucket_name = attr.ib(default=None)
    region = attr.ib(default=None)
    storage_class = attr.ib(default=None)

    def to_json(self):
        _json = super().to_json()
        _json['bucketName'] = self.bucket_name
        if self.region is not None:
            _json['region'] = self.region
        if self.storage_class is not None:
            _json['storageClass'] = self.storage_class
        return _json

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Driver entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Driver object
        """
        inst = super().from_json(_json, client_api, is_fetched=True)
        inst.bucket_name = _json.get('bucketName', None)
        inst.region = _json.get('region', None)
        inst.storage_class = _json.get('storageClass', None)
        return inst
