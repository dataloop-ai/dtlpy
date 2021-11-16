import logging
from .. import exceptions, entities, services, miscellaneous

logger = logging.getLogger(name=__name__)


class FeatureSets:
    """
    Feature Sets repository
    """
    URL = '/features/sets'

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
        self._project = project
        self._client_api = client_api

    ############
    # entities #
    ############
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
    def list(self):
        """
        List of features
        :return:
        """

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=self.URL)
        if not success:
            raise exceptions.PlatformException(response)

        features = miscellaneous.List([entities.FeatureSet.from_json(_json=_json,
                                                                     client_api=self._client_api) for _json in
                                       response.json()])
        return features

    def get(self, feature_set_id=None) -> entities.Feature:
        """
        Get Feature object

        :param feature_set_id:id of entity to GET
        :return: Feature object
        """

        success, response = self._client_api.gen_request(req_type="GET",
                                                         path="{}/{}".format(self.URL, feature_set_id))

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.FeatureSet.from_json(client_api=self._client_api,
                                             _json=response.json())

    def create(self, name: str,
               size: int,
               set_type: str,
               entity_type: entities.FeatureEntityType,
               project_id=None,
               tags=None,
               org_id=None):
        """
        Create a new Feature Set

        :param name: str - the Feature name
        :param size: str - the Feature size
        :param set_type: str - the Feature type
        :param entity_type: entities.FeatureEntityType
        :param project_id: project id
        :param tags:
        :param org_id: org id
        :return:
        """
        if tags is None:
            tags = list()
        if project_id is None:
            if self._project is None:
                raise ValueError('Must input a project id')
            else:
                project_id = self._project.id

        payload = {'name': name,
                   'size': size,
                   'tags': tags,
                   'type': set_type,
                   'project': project_id,
                   'entityType': entity_type}
        if org_id is not None:
            payload['org'] = org_id
        success, response = self._client_api.gen_request(req_type="post",
                                                         json_req=payload,
                                                         path=self.URL)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.FeatureSet.from_json(client_api=self._client_api,
                                             _json=response.json()[0])

    def delete(self, feature_set_id):
        """
        Delete feature vector
        :param feature_set_id: feature set id to delete

        return success: bool
        """

        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="{}/{}".format(self.URL, feature_set_id))

        # check response
        if success:
            logger.debug("Feature Set deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Item]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.FeatureSet._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items