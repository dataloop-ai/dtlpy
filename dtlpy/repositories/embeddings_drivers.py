import logging
from enum import Enum

from .. import entities, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class EmbeddingsDrivers:
    """
    Embeddings Drivers Repository

    The EmbeddingsDrivers class allows you to manage embeddings drivers, which bind a dataset to an
    external vector store (Elasticsearch, PostgreSQL) so feature vectors are written to and read
    from that store instead of the platform.
    """

    URL = '/embeddings/drivers'

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 project_id: str = None,
                 dataset: entities.Dataset = None,
                 dataset_id: str = None):
        self._client_api = client_api
        self._dataset = dataset
        self._dataset_id = dataset_id
        if dataset_id is None and dataset is not None:
            self._dataset_id = dataset.id
        if project is None:
            if dataset is not None:
                project = dataset.project
            elif project_id is not None:
                project = entities.Project.from_json(
                    _json={'id': project_id},
                    client_api=client_api,
                    is_fetched=False  # Not fully fetched yet, will lazy fetch when needed
                )
        self.project = project

    ###########
    # methods #
    ###########
    def _resolve_project_id(self, project_id: str = None) -> str:
        if project_id is not None:
            return project_id
        if self.project is None:
            raise ValueError('Must insert a project_id. Or create from a project or dataset context')
        return self.project.id

    def _resolve_dataset_id(self, dataset_id: str = None) -> str:
        if dataset_id is not None:
            return dataset_id
        if self._dataset_id is None:
            raise ValueError('Must insert a dataset_id. Or create from a dataset context')
        return self._dataset_id

    @staticmethod
    def _to_json_list(mappings):
        return [m.to_json() if isinstance(m, entities.FeatureSetSchemaMapping) else m for m in mappings]

    @staticmethod
    def _enum_value(value):
        # the SDK enums subclass str, so isinstance(value, str) can't tell a member from a plain string
        return value.value if isinstance(value, Enum) else value

    @_api_reference.add(path='/embeddings/drivers', method='post')
    def create(self,
               name: str,
               integration_id: str,
               store_type: entities.EmbeddingsDriverStoreType,
               dataset_id: str = None,
               project_id: str = None,
               feature_set_schema_mappings: list = None) -> entities.EmbeddingsDriver:
        """
        Create an Embeddings Driver, binding a dataset to an external vector store.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        A dataset can have only one embeddings driver - creating a second one raises ``exceptions.Conflict``.
        Feature sets created from `feature_set_schema_mappings` are returned on the driver's
        `created_feature_sets` attribute - a feature set whose `featureSetId` is empty failed to be
        created, and its `statusMessage` says why.

        :param str name: the embeddings driver name
        :param str integration_id: the integration id holding the vector store credentials
        :param EmbeddingsDriverStoreType store_type: dl.EmbeddingsDriverStoreType (e.g. ELASTICSEARCH)
        :param str dataset_id: the dataset to bind. Uses the repository's dataset if not provided
        :param str project_id: optional - project id. Uses the repository's project if not provided
        :param list feature_set_schema_mappings: optional - schema mapping dicts to create feature sets with
        :return: EmbeddingsDriver object
        :rtype: dtlpy.entities.embeddings_driver.EmbeddingsDriver

        **Example**:

        .. code-block:: python

            dataset.embeddings_drivers.create(
                name='my-embeddings-driver',
                integration_id='integration_id',
                store_type=dl.EmbeddingsDriverStoreType.ELASTICSEARCH,
                feature_set_schema_mappings=[{
                    'featureSetConfig': {'name': 'my-embeddings', 'size': 384},
                    'schemaName': 'my_index',
                    'externalField': 'entity_id',
                    'vectorField': 'embedding',
                    'distanceMetric': 'cosine',
                }],
            )
        """
        payload = {
            'name': name,
            'datasetId': self._resolve_dataset_id(dataset_id),
            'integrationId': integration_id,
            'storeType': self._enum_value(store_type),
            'project': self._resolve_project_id(project_id),
        }
        if feature_set_schema_mappings is not None:
            payload['featureSetSchemaMappings'] = self._to_json_list(feature_set_schema_mappings)

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=self.URL,
                                                         json_req=payload)
        if self._client_api.check_response(success, response, path=self.URL) is False:
            return None

        _json = response.json()
        embeddings_driver = entities.EmbeddingsDriver.from_json(_json=_json['driver'],
                                                                client_api=self._client_api)
        embeddings_driver.created_feature_sets = miscellaneous.List(_json.get('featureSets', list()))
        return embeddings_driver

    @_api_reference.add(path='/embeddings/drivers/{id}', method='get')
    def get(self, embeddings_driver_id: str) -> entities.EmbeddingsDriver:
        """
        Get an Embeddings Driver object.

        :param str embeddings_driver_id: the embeddings driver id
        :return: EmbeddingsDriver object
        :rtype: dtlpy.entities.embeddings_driver.EmbeddingsDriver

        **Example**:

        .. code-block:: python

            driver = dl.embeddings_drivers.get(embeddings_driver_id='embeddings_driver_id')
        """
        path = '{}/{}'.format(self.URL, embeddings_driver_id)
        success, response = self._client_api.gen_request(req_type='get', path=path)
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        return entities.EmbeddingsDriver.from_json(_json=response.json(), client_api=self._client_api)

    @_api_reference.add(path='/embeddings/drivers/dataset/{datasetId}', method='get')
    def list(self,
             dataset_id: str = None,
             page: int = None,
             page_size: int = None) -> miscellaneous.List:
        """
        List the Embeddings Drivers of a dataset.

        :param str dataset_id: the dataset id. Uses the repository's dataset if not provided
        :param int page: optional - page number. Platform default is 1
        :param int page_size: optional - page size. Platform default is 20
        :return: list of EmbeddingsDriver objects
        :rtype: dtlpy.miscellaneous.List

        **Example**:

        .. code-block:: python

            drivers = dataset.embeddings_drivers.list()
        """
        path = '{}/dataset/{}'.format(self.URL, self._resolve_dataset_id(dataset_id))
        query = list()
        if page is not None:
            query.append('page={}'.format(page))
        if page_size is not None:
            query.append('pageSize={}'.format(page_size))
        if query:
            path = '{}?{}'.format(path, '&'.join(query))

        success, response = self._client_api.gen_request(req_type='get', path=path)
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        return miscellaneous.List(
            [entities.EmbeddingsDriver.from_json(_json=_json, client_api=self._client_api)
             for _json in response.json().get('drivers', list())]
        )

    @_api_reference.add(path='/embeddings/drivers/{id}', method='patch')
    def update(self, embeddings_driver: entities.EmbeddingsDriver) -> entities.EmbeddingsDriver:
        """
        Update an Embeddings Driver.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        The platform never changes `dataset_id` or `store_type`, and once the driver has a schema
        mapping it also keeps `schema_name`, `external_field`, `distance_metric` and `data_column`
        as they are. Those fields come back unchanged instead of raising.

        :param dtlpy.entities.embeddings_driver.EmbeddingsDriver embeddings_driver: EmbeddingsDriver object
        :return: updated EmbeddingsDriver object
        :rtype: dtlpy.entities.embeddings_driver.EmbeddingsDriver

        **Example**:

        .. code-block:: python

            driver.name = 'new-name'
            driver = dl.embeddings_drivers.update(embeddings_driver=driver)
        """
        path = '{}/{}'.format(self.URL, embeddings_driver.id)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=path,
                                                         json_req=embeddings_driver.to_json())
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        logger.debug('Embeddings driver updated successfully')
        return entities.EmbeddingsDriver.from_json(_json=response.json(), client_api=self._client_api)

    @_api_reference.add(path='/embeddings/drivers/{id}', method='delete')
    def delete(self, embeddings_driver_id: str) -> bool:
        """
        Delete an Embeddings Driver.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str embeddings_driver_id: the embeddings driver id
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dl.embeddings_drivers.delete(embeddings_driver_id='embeddings_driver_id')
        """
        path = '{}/{}'.format(self.URL, embeddings_driver_id)
        success, response = self._client_api.gen_request(req_type='delete', path=path)
        if self._client_api.check_response(success, response, path=path) is False:
            return False
        logger.debug('Embeddings driver deleted successfully')
        return True

    @_api_reference.add(path='/embeddings/drivers/supported-distances', method='get')
    def supported_distances(self, store_type: entities.EmbeddingsDriverStoreType = None) -> miscellaneous.List:
        """
        List the distance metrics each vector store supports.

        :param EmbeddingsDriverStoreType store_type: optional - limit to a single store type
        :return: list of dicts, each holding a 'storeType' and its 'distanceMetrics'
        :rtype: dtlpy.miscellaneous.List

        **Example**:

        .. code-block:: python

            dl.embeddings_drivers.supported_distances(store_type=dl.EmbeddingsDriverStoreType.ELASTICSEARCH)
        """
        path = '{}/supported-distances'.format(self.URL)
        if store_type is not None:
            path = '{}?storeType={}'.format(path, self._enum_value(store_type))

        success, response = self._client_api.gen_request(req_type='get', path=path)
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        return miscellaneous.List(response.json().get('stores', list()))

    @_api_reference.add(path='/embeddings/drivers/{id}/schema-mappings', method='get')
    def list_schema_mappings(self,
                             embeddings_driver_id: str,
                             feature_set_id: str = None) -> miscellaneous.List:
        """
        List the feature set schema mappings of an Embeddings Driver.

        :param str embeddings_driver_id: the embeddings driver id
        :param str feature_set_id: optional - return only the mapping of this feature set
        :return: list of FeatureSetSchemaMapping objects
        :rtype: dtlpy.miscellaneous.List

        **Example**:

        .. code-block:: python

            mappings = dl.embeddings_drivers.list_schema_mappings(embeddings_driver_id='embeddings_driver_id')
        """
        path = '{}/{}/schema-mappings'.format(self.URL, embeddings_driver_id)
        if feature_set_id is not None:
            path = '{}?featureSetId={}'.format(path, feature_set_id)

        success, response = self._client_api.gen_request(req_type='get', path=path)
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        return miscellaneous.List(
            [entities.FeatureSetSchemaMapping.from_json(_json=_json) for _json in response.json()]
        )

    @_api_reference.add(path='/embeddings/drivers/{id}/schema-mappings/{featureSetId}', method='patch')
    def update_schema_mapping(self,
                              embeddings_driver_id: str,
                              feature_set_id: str,
                              vector_field: str = None,
                              data_column: str = None,
                              distance_metric: entities.EmbeddingsDistanceMetric = None
                              ) -> entities.FeatureSetSchemaMapping:
        """
        Update a feature set schema mapping of an Embeddings Driver.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        Only these three fields can be updated. `vector_field` and `distance_metric` affect the store,
        so changing either one re-validates every mapping of the driver.

        :param str embeddings_driver_id: the embeddings driver id
        :param str feature_set_id: the feature set id of the mapping
        :param str vector_field: optional - the vector field in the external schema
        :param str data_column: optional - the column holding the source data
        :param EmbeddingsDistanceMetric distance_metric: optional - dl.EmbeddingsDistanceMetric
        :return: updated FeatureSetSchemaMapping object
        :rtype: dtlpy.entities.embeddings_driver.FeatureSetSchemaMapping

        **Example**:

        .. code-block:: python

            dl.embeddings_drivers.update_schema_mapping(
                embeddings_driver_id='embeddings_driver_id',
                feature_set_id='feature_set_id',
                vector_field='embedding',
            )
        """
        payload = dict()
        if vector_field is not None:
            payload['vectorField'] = vector_field
        if data_column is not None:
            payload['dataColumn'] = data_column
        if distance_metric is not None:
            payload['distanceMetric'] = self._enum_value(distance_metric)
        if not payload:
            raise ValueError('Must input one of: vector_field, data_column, distance_metric')

        path = '{}/{}/schema-mappings/{}'.format(self.URL, embeddings_driver_id, feature_set_id)
        success, response = self._client_api.gen_request(req_type='patch', path=path, json_req=payload)
        if self._client_api.check_response(success, response, path=path) is False:
            return None
        return entities.FeatureSetSchemaMapping.from_json(_json=response.json())
