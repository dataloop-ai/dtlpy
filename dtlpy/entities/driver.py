import logging
import attr
from enum import Enum
from .. import services, entities

logger = logging.getLogger(name='dtlpy')


class ExternalStorage(str, Enum):
    S3 = "s3"
    GCS = "gcs"
    AZUREBLOB = "azureblob"
    KEY_VALUE = "key_value"
    AWS_STS = 'aws-sts'


@attr.s()
class Driver(entities.BaseEntity):
    """
    Driver entity
    """
    bucket_name = attr.ib()
    creator = attr.ib()
    allow_external_delete = attr.ib()
    allow_external_modification = attr.ib()
    created_at = attr.ib()
    region = attr.ib()
    path = attr.ib()
    type = attr.ib()
    integration_id = attr.ib()
    metadata = attr.ib(repr=False)
    name = attr.ib()
    id = attr.ib()
    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Driver entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Driver object
        """
        inst = cls(bucket_name=_json.get('bucketName', None),
                   creator=_json.get('creator', None),
                   allow_external_delete=_json.get('allowExternalDelete', None),
                   allow_external_modification=_json.get('allowExternalModification', None),
                   created_at=_json.get('createdAt', None),
                   region=_json.get('region', None),
                   type=_json.get('type', None),
                   integration_id=_json.get('integrationId', None),
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
                                                              attr.fields(Driver).bucket_name,
                                                              attr.fields(Driver).allow_external_delete,
                                                              attr.fields(Driver).allow_external_modification,
                                                              attr.fields(Driver).created_at,
                                                              attr.fields(Driver).integration_id,
                                                              attr.fields(Driver).path,
                                                              ))
        output_dict['bucketName'] = self.bucket_name
        output_dict['allowExternalDelete'] = self.allow_external_delete
        output_dict['allowExternalModification'] = self.allow_external_modification
        output_dict['createdAt'] = self.created_at
        output_dict['integrationId'] = self.integration_id
        if self.path is not None:
            output_dict['path'] = self.path

        return output_dict
