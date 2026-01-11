import logging
import copy
from .. import exceptions, entities, miscellaneous, _api_reference, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class FeatureSets:
    """
    Feature Sets repository
    """

    URL = '/features/sets'

    def __init__(
        self,
        client_api: ApiClient,
        project_id: str = None,
        project: entities.Project = None,
        model_id: str = None,
        model: entities.Model = None,
        dataset_id: str = None,
        dataset: entities.Dataset = None,
    ):
        self._project = project
        self._project_id = project_id
        self._model = model
        self._model_id = model_id
        self._dataset = dataset
        self._dataset_id = dataset_id
        self._client_api = client_api

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None and self._project_id is None and self.dataset is not None:
            self._project = self.dataset.project
            self._project_id = self._project.id
        if self._project is None and self._project_id is not None:
            # get from id
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self._project_id)
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001', message='Cannot perform action WITHOUT Project entity in FeatureSets repository.' ' Please checkout or set a project'
            )
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def model(self) -> entities.Model:
        if self._model is None and self._model_id is not None:
            # get from id
            self._model = repositories.Models(client_api=self._client_api).get(model_id=self._model_id)
        if self._model is None:
            raise exceptions.PlatformException(error='2001', message='Cannot perform action WITHOUT Model entity in FeatureSets repository.')
        assert isinstance(self._model, entities.Model)
        return self._model

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None and self._dataset_id is not None:
            # get from id
            self._dataset = repositories.Datasets(client_api=self._client_api).get(dataset_id=self._dataset_id)
        if self._dataset is None:
            return None
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    ###########
    # methods #
    ###########

    def _list(self, filters: entities.Filters):
        # request
        success, response = self._client_api.gen_request(req_type='POST', path='/features/sets/query', json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/features/sets/query', method='post')
    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List Feature Sets

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities
        """
        # Step 1: Initialize filter (create empty if None)
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.FEATURE_SET)

        if filters.resource != entities.FiltersResource.FEATURE_SET:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.FEATURE_SET. Got: {!r}'.format(filters.resource),
            )

        # Step 2: Extract IDs inline (no helper functions, no property access)
        # Extract project_id inline
        if self._project_id is not None:
            project_id = self._project_id
        elif self._project is not None:
            project_id = self._project.id
        else:
            raise exceptions.PlatformException(
                error='2001', message='Cannot perform action WITHOUT Project entity in FeatureSets repository.' ' Please checkout or set a project'
            )

        # Extract dataset_id inline (only when needed for filtering)
        if self._dataset_id is not None:
            dataset_id = self._dataset_id
        elif self._dataset is not None:
            dataset_id = self._dataset.id
        else:
            dataset_id = None  # No dataset filtering needed

        # Set context with project_id
        filters.context = {'projects': [project_id]}

        # Preserve original page and page size values before any operations that might modify them
        received_filter = copy.deepcopy(filters)

        # Step 3: Execute received filter - Run filter with appropriate pagination
        # When dataset_id is None: use original pagination (respect user's page request)
        # When dataset_id is not None: start from page 0 to collect all IDs (pagination applied later)
        if dataset_id is not None:
            page_offset = 0
            received_filter_paged = entities.PagedEntities(
                items_repository=self,
                filters=filters,
                page_offset=page_offset,
                page_size=filters.page_size,
                client_api=self._client_api,
            )
            # Step 5: Dataset_id exists and items exist - extract IDs from all pages
            # Extract feature set IDs from all pages (received_filter_paged.all() will fetch all pages starting from page 0)
            filter_fs_ids = [feature_set.id for feature_set in received_filter_paged.all()]
            
            # Step 6: Run aggregation API (when dataset_id exists)
            payload = {
                "projectId": project_id,
                "datasetIds": [dataset_id],
            }
            success, response = self._client_api.gen_request(req_type="POST", path="/features/vectors/project-count-aggregation", json_req=payload)
            if not success:
                raise exceptions.PlatformException(response)
            result = response.json()
            # Extract dataset feature set IDs from response, filtering out entries where count == 0
            dataset_fs_ids = [item['featureSetId'] for item in result if item.get('count', 0) > 0]

            # Step 7: Intersect IDs
            final_fs_ids = list(set(filter_fs_ids).intersection(set(dataset_fs_ids)))

            # Step 8: Final return path - Create filter with intersected IDs (no join needed)
            intersected_ids_filter = entities.Filters(resource=entities.FiltersResource.FEATURE_SET)
            intersected_ids_filter.add(field='id', operator=entities.FiltersOperations.IN, values=final_fs_ids)
            intersected_ids_filter.page = received_filter.page  # Preserve original pagination
            intersected_ids_filter.page_size = received_filter.page_size
            intersected_ids_filter.context = {'projects': [project_id]}

            filter_paged = entities.PagedEntities(
                items_repository=self,
                filters=intersected_ids_filter,
                page_offset=intersected_ids_filter.page,
                page_size=intersected_ids_filter.page_size,
                client_api=self._client_api,
            )
            filter_paged.get_page()

        else:
            page_offset = filters.page if dataset_id is None else 0

            filter_paged = entities.PagedEntities(
                items_repository=self,
                filters=filters,
                page_offset=page_offset,
                page_size=filters.page_size,
                client_api=self._client_api,
            )
            filter_paged.get_page()

        return filter_paged

    @_api_reference.add(path='/features/sets/{id}', method='get')
    def get(self, feature_set_name: str = None, feature_set_id: str = None) -> entities.Feature:
        """
        Get Feature Set object

        :param str feature_set_name: name of the feature set
        :param str feature_set_id: id of the feature set
        :return: Feature object
        """
        if feature_set_id is not None:
            success, response = self._client_api.gen_request(req_type="GET", path="{}/{}".format(self.URL, feature_set_id))
            if not success:
                raise exceptions.PlatformException(response)
            feature_set = entities.FeatureSet.from_json(client_api=self._client_api, _json=response.json())
        elif feature_set_name is not None:
            if not isinstance(feature_set_name, str):
                raise exceptions.PlatformException(error='400', message='feature_set_name must be string')
            filters = entities.Filters(resource=entities.FiltersResource.FEATURE_SET)
            filters.add(field='name', values=feature_set_name)
            feature_sets = self.list(filters=filters)
            if feature_sets.items_count == 0:
                raise exceptions.PlatformException(error='404', message='Feature set not found. name: {!r}'.format(feature_set_name))
            elif feature_sets.items_count > 1:
                # more than one matching project
                raise exceptions.PlatformException(error='404', message='More than one feature_set with same name. Please "get" by id')
            else:
                feature_set = feature_sets.items[0]
        else:
            raise exceptions.PlatformException(error='400', message='Must provide an identifier in inputs, feature_set_name or feature_set_id')
        return feature_set

    @_api_reference.add(path='/features/sets', method='post')
    def create(
        self, name: str, size: int, set_type: str, entity_type: entities.FeatureEntityType, project_id: str = None, model_id: set = None, org_id: str = None
    ):
        """
        Create a new Feature Set

        :param str name: the Feature name
        :param int size: the length of a single vector in the set
        :param str set_type: string of the feature type: 2d, 3d, modelFC, TSNE,PCA,FFT
        :param entity_type: the entity that feature vector is linked to. Use the enum dl.FeatureEntityType
        :param str project_id: the ID of the project where feature set will be created
        :param str model_id: the ID of the model that creates the vectors
        :param str org_id: the ID of the org where feature set will be created
        :return: Feature Set object
        """
        if project_id is None:
            if self._project is None:
                raise ValueError('Must input a project id')
            else:
                project_id = self._project.id

        payload = {'name': name, 'size': size, 'type': set_type, 'project': project_id, 'modelId': model_id, 'entityType': entity_type}
        if org_id is not None:
            payload['org'] = org_id
        success, response = self._client_api.gen_request(req_type="post", json_req=payload, path=self.URL)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.FeatureSet.from_json(client_api=self._client_api, _json=response.json()[0])

    @_api_reference.add(path='/features/sets/{id}', method='delete')
    def delete(self, feature_set_id: str):
        """
        Delete feature vector

        :param str feature_set_id: feature set id to delete
        :return: success
        :rtype: bool
        """

        success, response = self._client_api.gen_request(req_type="delete", path=f"{self.URL}/{feature_set_id}")

        # check response
        if success:
            logger.debug("Feature Set deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/features/set/{id}', method='patch')
    def update(self, feature_set: entities.FeatureSet) -> entities.FeatureSet:
        """
         Update a Feature Set

         **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.FeatureSet feature_set: FeatureSet object
        :return: FeatureSet
        :rtype: dtlpy.entities.FeatureSet

        **Example**:

         .. code-block:: python

             dl.feature_sets.update(feature_set='feature_set')
        """
        success, response = self._client_api.gen_request(req_type="patch", path=f"{self.URL}/{feature_set.id}", json_req=feature_set.to_json())
        if not success:
            raise exceptions.PlatformException(response)

        logger.debug("feature_set updated successfully")
        # update dataset labels
        feature_set = entities.FeatureSet.from_json(_json=response.json(), client_api=self._client_api, is_fetched=True)
        return feature_set

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Item]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.FeatureSet._protected_from_json, **{'client_api': self._client_api, '_json': item})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items
