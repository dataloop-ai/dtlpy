import logging

from .. import exceptions, entities, miscellaneous, _api_reference, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Features:
    """
    Features repository
    """
    URL = '/features/vectors'

    def __init__(self, client_api: ApiClient,
                 project: entities.Project = None,
                 project_id: str = None,
                 item: entities.Item = None,
                 annotation: entities.Annotation = None,
                 feature_set: entities.FeatureSet = None,
                 dataset: entities.Dataset = None):
        if project is not None and project_id is None:
            project_id = project.id
        self._dataset = dataset
        self._project = project
        self._project_id = project_id
        self._item = item
        self._annotation = annotation
        self._feature_set = feature_set
        self._client_api = client_api

    ############
    # entities #
    ############
    @property
    def feature_set(self) -> entities.FeatureSet:
        return self._feature_set

    @property
    def project(self) -> entities.Project:
        if self._project is None and self._project_id is None and self._item is not None:
            self._project = self._item.project
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
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Features repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    ###########
    # methods #
    ###########
    def _list(self, filters: entities.Filters):
        """
        Get dataset feature vectors list. This is a browsing endpoint, for any given path feature count will be returned,
        user is expected to perform another request then for every folder item to actually get the item list.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="{}/query".format(self.URL),
                                                         json_req=filters.prepare(),
                                                         headers={'user_query': filters._user_query}
                                                         )
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/features/vectors', method='post')
    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List of features

        :param dtlpy.entities.filters.Filters filters: Filters to query the features data
        :return: Pages object
        :rtype: dtlpy.entities.paged_entities.PagedEntities
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.FEATURE)
            filters._user_query = 'false'
        # default sorting
        if filters.sort == dict():
            filters.sort_by(field='id')
        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.FEATURE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.FEATURE. Got: {!r}'.format(filters.resource))
        if self._feature_set is not None:
            filters.add(field='featureSetId', values=self._feature_set.id)
        if self._item is not None:
            filters.add(field='entityId', values=self._item.id)
        if self._dataset is not None:
            filters.add(field='datasetId', values=self._dataset.id)
        if self._project_id is None:
            self._project_id = self.project.id
        filters.context = {"projects": [self._project_id]}
        
        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    @_api_reference.add(path='/features/vectors/{id}', method='get')
    def get(self, feature_id: str) -> entities.Feature:
        """
        Get Feature object

        :param str feature_id: feature id
        :return: Feature object
        """

        success, response = self._client_api.gen_request(req_type="GET",
                                                         path="{}/{}".format(self.URL, feature_id))

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Feature.from_json(client_api=self._client_api,
                                          _json=response.json())

    @_api_reference.add(path='/features/vectors', method='post')
    def create(self,
               value,
               project_id: str = None,
               feature_set_id: str = None,
               entity=None,
               version: str = None,
               parent_id: str = None,
               org_id: str = None
               ):
        """
        Create a new Feature vector

        :param immutable value: actual vector - immutable (list of floats [1,2,3]) or list of lists of floats
        :param str project_id: the id of the project where feature will be created
        :param str feature_set_id: ref to a featureSet this vector is a part of
        :param entity: the entity the featureVector is linked to (item, annotation, etc) or list of entities
        :param str version: version of the featureSet generator
        :param str parent_id: optional: parent FeatureSet id - used when FeatureVector is a subFeature
        :param str org_id: the id of the org where featureVector will be created
        :return: Feature vector:
        """
        if project_id is None:
            if self._project is not None:
                project_id = self._project.id
            elif self._project_id is not None:
                project_id = self._project_id
            else:
                raise ValueError('Must insert a project id')

        if feature_set_id is None:
            if self._feature_set is None:
                raise ValueError(
                    'Missing feature_set_id. Must insert the variable or create from context, e.g. feature_set.features.create()')
            feature_set_id = self._feature_set.id
        
        # Additional payload info
        additional_payload = {}
        if version is not None:
            additional_payload['version'] = version
        if parent_id is not None:
            additional_payload['parentId'] = parent_id
        if org_id is not None:
            additional_payload['org'] = org_id
        additional_payload['project'] = project_id
        additional_payload['featureSetId'] = feature_set_id

        if not isinstance(entity, list):
            entity = [entity]
            value = [value]

        if len(value) != len(entity):
            raise ValueError('The number of vectors must be equal to the number of entities')

        payload = []
        for (single_entity, single_value) in zip(entity, value):
            entry = {'entityId': single_entity.id,
                            'value': single_value,
                            'datasetId': single_entity.dataset.id
                        }
            entry.update(additional_payload)
            payload.append(entry)

        success, response = self._client_api.gen_request(req_type="post",
                                                         json_req=payload,
                                                         path=self.URL)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        features = [entities.Feature.from_json(client_api=self._client_api,
                                          _json=feature) for feature in response.json()]
        # return entity
        if len(features) == 1:
            return features[0]
        return features

    @_api_reference.add(path='/features/vectors/{id}', method='delete')
    def delete(self, feature_id: str):
        """
        Delete feature vector

        :param str feature_id: feature id to delete
        :return: success
        :rtype: bool
        """

        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="{}/{}".format(self.URL, feature_id))

        # check response
        if success:
            logger.debug("Feature deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Item]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.Feature._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items
