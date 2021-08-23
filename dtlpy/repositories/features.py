import logging
import time
import numpy as np

from .. import exceptions, entities, services, miscellaneous

logger = logging.getLogger(name=__name__)


class Features:
    """
    Features repository
    """
    URL = '/features/vectors'

    def __init__(self, client_api: services.ApiClient,
                 project: entities.Project = None,
                 item: entities.Item = None,
                 annotation: entities.Annotation = None,
                 feature_set: entities.FeatureSet = None):
        self._project = project
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
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Datasets repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    ###########
    # methods #
    ###########
    def _list(self, filters: entities.Filters):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="{}/query".format(self.URL),
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List of features

        :param filters: Filters to query the features data
        :return: Pages object
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.FEATURE)
        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.FEATURE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.FEATURE. Got: {!r}'.format(filters.resource))
        if self._feature_set is not None:
            filters.custom_filter = {'featureSetId': self._feature_set.id}
        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def get(self, feature_id=None) -> entities.Feature:
        """
        Get Feature object

        :param feature_id:
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

    def create(self, value, feature_set_id=None, entity_id=None, version=None, parent_id=None):
        """
        Create a new Feature vector

        :param value: the vector (list of floats)
        :param feature_set_id: FeatureSet id
        :param entity_id: id of the entity the feature vector is linked to (item.id, annotation.id etc)
        :param version:
        :param parent_id: optional: parent FeatureSet id
        :return:
        """
        context = dict()
        if 'project' not in context:
            if self._project is None:
                raise ValueError('Must input a project id in context')
            else:
                context['project'] = self._project.id
        if feature_set_id is None:
            if self._feature_set is None:
                raise ValueError(
                    'Missing feature_set_id. Input the variable or create from context - feature_set.features.create()')
            feature_set_id = self._feature_set.id

        payload = {'context': context,
                   'entityId': entity_id,
                   'value': value,
                   'featureSetId': feature_set_id}
        if version is not None:
            payload['version'] = version
        if parent_id is not None:
            payload['parentId'] = parent_id
        success, response = self._client_api.gen_request(req_type="post",
                                                         json_req=payload,
                                                         path=self.URL)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Feature.from_json(client_api=self._client_api,
                                          _json=response.json()[0])

    def delete(self, feature_id):
        """
        Delete feature vector
        :param feature_id: feature id to delete

        return success: bool
        """

        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="{}/{}".format(self.URL, feature_id))

        # check response
        if success:
            logger.debug("Feature deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)
