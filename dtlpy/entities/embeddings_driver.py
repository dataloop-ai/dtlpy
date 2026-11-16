import logging
import attr
import traceback
from enum import Enum
from collections import namedtuple

from .. import repositories, entities
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class EmbeddingsDriverStoreType(str, Enum):
    """ The external vector store of an Embeddings Driver.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - Type
         - Description
       * - ELASTICSEARCH
         - Elasticsearch vector store
       * - POSTGRESQL
         - PostgreSQL vector store (pgvector)
    """
    ELASTICSEARCH = "elasticsearch"
    POSTGRESQL = "postgresql"


class EmbeddingsDriverStatus(str, Enum):
    """ The status of an Embeddings Driver.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - Status
         - Description
       * - ACTIVE
         - Driver is connected to its store
       * - INACTIVE
         - Driver was created but is not active yet
       * - ERROR
         - Driver failed to connect or validate its store
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class EmbeddingsDistanceMetric(str, Enum):
    """ The distance metric used for feature vector similarity.

    Not every store supports every metric - use
    :meth:`dtlpy.repositories.embeddings_drivers.EmbeddingsDrivers.supported_distances` to list the
    metrics a store type accepts.

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - Metric
         - Description
       * - L2
         - Euclidean (L2) distance
       * - COSINE
         - Cosine similarity
       * - INNER_PRODUCT
         - Inner product
       * - L2_NORM
         - Normalized L2 distance
       * - DOT_PRODUCT
         - Dot product
    """
    L2 = "l2"
    COSINE = "cosine"
    INNER_PRODUCT = "inner_product"
    L2_NORM = "l2_norm"
    DOT_PRODUCT = "dot_product"


@attr.s
class FeatureSetSchemaMapping(entities.BaseEntity):
    """
    Feature Set Schema Mapping entity.
    Maps a feature set to the vector field of an embeddings driver's schema.
    """
    id = attr.ib()
    embeddings_driver_id = attr.ib()
    feature_set_id = attr.ib()
    schema_name = attr.ib()
    vector_field = attr.ib()
    external_field = attr.ib()
    data_column = attr.ib()
    distance_metric = attr.ib()
    created_at = attr.ib()
    updated_at = attr.ib()

    @classmethod
    def from_json(cls, _json):
        """
        Build a FeatureSetSchemaMapping entity object from a json

        :param dict _json: _json response from host
        :return: FeatureSetSchemaMapping object
        :rtype: dtlpy.entities.embeddings_driver.FeatureSetSchemaMapping
        """
        return cls(id=_json.get('_id', None),
                   embeddings_driver_id=_json.get('embeddingsDriverId', None),
                   feature_set_id=_json.get('featureSetId', None),
                   schema_name=_json.get('schemaName', None),
                   vector_field=_json.get('vectorField', None),
                   external_field=_json.get('externalField', None),
                   data_column=_json.get('dataColumn', None),
                   distance_metric=_json.get('distanceMetric', None),
                   created_at=_json.get('createdAt', None),
                   updated_at=_json.get('updatedAt', None))

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        return {'_id': self.id,
                'embeddingsDriverId': self.embeddings_driver_id,
                'featureSetId': self.feature_set_id,
                'schemaName': self.schema_name,
                'vectorField': self.vector_field,
                'externalField': self.external_field,
                'dataColumn': self.data_column,
                'distanceMetric': self.distance_metric,
                'createdAt': self.created_at,
                'updatedAt': self.updated_at}


@attr.s
class EmbeddingsDriver(entities.BaseEntity):
    """
    Embeddings Driver entity.
    Binds a dataset to an external vector store through a Dataloop Integration.

    A driver holds one shared store target - `schema_name`, `external_field`, `distance_metric` and
    `data_column`. Every schema mapping of the driver must agree with it, and once the driver has a
    mapping the platform stops accepting changes to those four fields.
    """
    # platform
    id = attr.ib()
    name = attr.ib()
    dataset_id = attr.ib()
    integration_id = attr.ib()
    store_type = attr.ib()
    status = attr.ib()
    status_message = attr.ib()
    schema_name = attr.ib()
    external_field = attr.ib()
    distance_metric = attr.ib()
    data_column = attr.ib()
    project = attr.ib()
    org = attr.ib()
    creator = attr.ib()
    created_at = attr.ib()
    updated_at = attr.ib()

    # sdk
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    # feature sets created alongside the driver - populated by create() only
    created_feature_sets = attr.ib(default=None, repr=False)

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['embeddings_drivers'])
        return reps(
            embeddings_drivers=repositories.EmbeddingsDrivers(client_api=self._client_api,
                                                              project=self.project,
                                                              dataset_id=self.dataset_id),
        )

    @property
    def embeddings_drivers(self):
        assert isinstance(self._repositories.embeddings_drivers, repositories.EmbeddingsDrivers)
        return self._repositories.embeddings_drivers

    @staticmethod
    def _protected_from_json(_json, client_api, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json: entity's object json
        :param client_api: ApiClient entity
        :return: tuple (status, EmbeddingsDriver object or traceback)
        """
        try:
            embeddings_driver = EmbeddingsDriver.from_json(_json=_json,
                                                           client_api=client_api,
                                                           is_fetched=is_fetched)
            status = True
        except Exception:
            embeddings_driver = traceback.format_exc()
            status = False
        return status, embeddings_driver

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build an EmbeddingsDriver entity object from a json

        :param dict _json: _json response from host
        :param client_api: ApiClient entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: EmbeddingsDriver object
        :rtype: dtlpy.entities.embeddings_driver.EmbeddingsDriver
        """
        project_id = _json.get('project', None)
        project = None
        if project_id is not None:
            project = entities.Project.from_json(
                _json={'id': project_id},
                client_api=client_api,
                is_fetched=False  # Not fully fetched yet, will lazy fetch when needed
            )
        inst = cls(id=_json.get('_id', None),
                   name=_json.get('name', None),
                   dataset_id=_json.get('datasetId', None),
                   integration_id=_json.get('integrationId', None),
                   store_type=_json.get('storeType', None),
                   status=_json.get('status', None),
                   status_message=_json.get('statusMessage', None),
                   schema_name=_json.get('schemaName', None),
                   external_field=_json.get('externalField', None),
                   distance_metric=_json.get('distanceMetric', None),
                   data_column=_json.get('dataColumn', None),
                   project=project,
                   org=_json.get('org', None),
                   creator=_json.get('creator', None),
                   created_at=_json.get('createdAt', None),
                   updated_at=_json.get('updatedAt', None),
                   client_api=client_api)
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        return {'_id': self.id,
                'name': self.name,
                'datasetId': self.dataset_id,
                'integrationId': self.integration_id,
                'storeType': self.store_type,
                'status': self.status,
                'statusMessage': self.status_message,
                'schemaName': self.schema_name,
                'externalField': self.external_field,
                'distanceMetric': self.distance_metric,
                'dataColumn': self.data_column,
                'project': self.project.id if self.project is not None else None,
                'org': self.org,
                'creator': self.creator,
                'createdAt': self.created_at,
                'updatedAt': self.updated_at}

    def update(self):
        """
        Update the embeddings driver

        :return: EmbeddingsDriver object
        :rtype: dtlpy.entities.embeddings_driver.EmbeddingsDriver
        """
        return self.embeddings_drivers.update(embeddings_driver=self)

    def delete(self):
        """
        Delete the embeddings driver

        :return: True if success
        :rtype: bool
        """
        return self.embeddings_drivers.delete(embeddings_driver_id=self.id)

    def list_schema_mappings(self):
        """
        List the feature set schema mappings of the driver

        :return: list of FeatureSetSchemaMapping objects
        :rtype: dtlpy.miscellaneous.List
        """
        return self.embeddings_drivers.list_schema_mappings(embeddings_driver_id=self.id)
