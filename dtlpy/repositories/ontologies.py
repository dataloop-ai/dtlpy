import logging
import traceback

from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Ontologies:
    """
    Ontologies repository
    """

    def __init__(self, client_api: services.ApiClient,
                 recipe: entities.Recipe = None,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None):
        self._client_api = client_api
        self._recipe = recipe
        self._project = project
        self._dataset = dataset

    ############
    # entities #
    ############
    @property
    def recipe(self) -> entities.Recipe:
        if self._recipe is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "recipe". need to set a Recipe entity or use ontology.recipes repository')
        assert isinstance(self._recipe, entities.Recipe)
        return self._recipe

    @recipe.setter
    def recipe(self, recipe: entities.Recipe):
        if not isinstance(recipe, entities.Recipe):
            raise ValueError('Must input a valid Recipe entity')
        self._recipe = recipe

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.ontologies repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.ontologies repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    def __get_project_ids(self, project_ids):
        if project_ids is not None:
            return project_ids if isinstance(project_ids, list) else [project_ids]
        elif self._recipe is not None:
            return self._recipe.project_ids
        elif self._project is not None:
            return [self._project.id]
        elif self._dataset is not None:
            return self._dataset.projects
        else:
            return project_ids

    ###########
    # methods #
    ###########
    def create(self, labels, title=None, project_ids=None, attributes=None) -> entities.Ontology:
        """
        Create a new ontology

        :param labels: recipe tags
        :param title: ontology title, name
        :param project_ids: recipe project/s
        :param attributes: recipe attributes
        :return: Ontology object
        """
        project_ids = self.__get_project_ids(project_ids=project_ids)
        if attributes is None:
            attributes = list()
        elif not isinstance(project_ids, list):
            project_ids = [project_ids]
        # convert to platform label format (root)
        labels = self.labels_to_roots(labels)
        payload = {"roots": labels,
                   "projectIds": project_ids,
                   "attributes": attributes}
        if title is not None:
            payload['title'] = title
        success, response = self._client_api.gen_request(req_type="post",
                                                         path="/ontologies",
                                                         json_req=payload)
        if success:
            logger.info("Ontology was created successfully")
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
        else:
            logger.error("Failed to create Ontology")
            raise exceptions.PlatformException(response)
        return ontology

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Ontology]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_package, package in enumerate(response_items):
            jobs[i_package] = pool.apply_async(entities.Ontology._protected_from_json,
                                               kwds={'client_api': self._client_api,
                                                     '_json': package,
                                                     'project': self._project,
                                                     'dataset': self._dataset,
                                                     'recipe': self._recipe})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        ontologies = miscellaneous.List([r[1] for r in results if r[0] is True])
        return ontologies

    def _list(self, filters: entities.Filters):
        url = '/ontologies?pageOffset={}&pageSize={}'.format(filters.page, filters.page_size)
        project_ids = None
        ids = None
        for single_filter in filters.and_filter_list:
            if single_filter.field == 'projects':
                project_ids = single_filter.values
                break
        for single_filter in filters.and_filter_list:
            if single_filter.field == 'ids':
                ids = single_filter.values
                break

        if project_ids:
            url = '{}&projects={}'.format(url, ','.join(project_ids))
        if ids:
            url = '{}&ids={}'.format(url, ','.join(ids))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def __list(self, filters: entities.Filters) -> entities.PagedEntities:
        """
        List project ontologies
        :return:
        """
        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def list(self, project_ids=None) -> miscellaneous.List[entities.Ontology]:
        """
        List ontologies for recipe

        :return:
        """
        if self._recipe is not None:
            ontologies = [ontology_id for ontology_id in self.recipe.ontologyIds]

            pool = self._client_api.thread_pools(pool_name='entity.create')
            jobs = [None for _ in range(len(ontologies))]
            for i_ontology, ontology_id in enumerate(ontologies):
                jobs[i_ontology] = pool.apply_async(self._protected_get, kwds={'ontology_id': ontology_id})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all results
            results = [j.get() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            return miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            filters = entities.Filters(resource=entities.FiltersResource.ONTOLOGY)
            project_ids = self.__get_project_ids(project_ids=project_ids)
            if project_ids:
                filters.add(field='projects', values=self.__get_project_ids(project_ids=project_ids))
            if self._dataset:
                filters.add(field='ids', values=self._dataset.ontology_ids)
            ontologies = list()
            pages = self.__list(filters=filters)
            for page in pages:
                ontologies += page
            return miscellaneous.List(ontologies)

    def _protected_get(self, ontology_id):
        """
        Same as get but with try-except to catch if error
        :param ontology_id:
        :return:
        """
        try:
            ontology = self.get(ontology_id=ontology_id)
            status = True
        except Exception:
            ontology = traceback.format_exc()
            status = False
        return status, ontology

    def get(self, ontology_id) -> entities.Ontology:
        """
        Get Ontology object

        :param ontology_id: ontology id
        :return: Ontology object
        """
        success, response = self._client_api.gen_request(req_type="get",
                                                         path="/ontologies/{}".format(ontology_id))
        if success:
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
        else:
            raise exceptions.PlatformException(response)
        return ontology

    def delete(self, ontology_id):
        """
        Delete Ontology from platform

        :param ontology_id: ontology_id id
        :return: True
        """
        success, response = self._client_api.gen_request(req_type="delete",
                                                         path="/ontologies/%s" % ontology_id)
        if success:
            logger.debug("Ontology was deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    def update(self, ontology: entities.Ontology, system_metadata=False) -> entities.Ontology:
        """
        Update Ontology metadata

       :param ontology: Ontology object
       :param system_metadata: bool
       :return: Ontology object
       """
        url_path = "/ontologies/%s" % ontology.id
        if system_metadata:
            url_path += "?system=true"
        success, response = self._client_api.gen_request(req_type="put",
                                                         path=url_path,
                                                         json_req=ontology.to_json())
        if success:
            logger.debug("Ontology was updated successfully")
            # update dataset labels
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe)
            if self._recipe is not None and self._recipe._dataset is not None:
                self.recipe.dataset._labels = ontology.labels
            return ontology
        else:
            logger.error("Failed to update ontology:")
            raise exceptions.PlatformException(response)

    @staticmethod
    def labels_to_roots(labels):
        """
        Converts labels dict to a list of platform representation of labels

        :param labels: labels dict
        :return: platform representation of labels
        """
        roots = list()
        if isinstance(labels, dict):
            for label in labels:
                root = {
                    "value": {
                        "tag": label,
                        "color": labels[label],
                        "attributes": list(),
                    },
                    "children": list(),
                }
                roots.append(root)
        elif isinstance(labels, list):
            for label in labels:
                if isinstance(label, entities.Label):
                    root = label.to_root()
                elif "value" in label:
                    root = {
                        "value": label["value"],
                        "children": label.get("children", list()),
                    }
                else:
                    root = {
                        "value": {
                            "tag": label.get("tag", None),
                            "color": label.get("color", "#FFFFFF"),
                            "attributes": label.get("attributes", list()),
                        },
                        "children": label.get("children", list()),
                    }
                roots.append(root)
        for root in roots:
            if not isinstance(root["value"]["color"], str):
                # noinspection PyStringFormat
                root["value"]["color"] = "#%02x%02x%02x" % root["value"]["color"]
        return roots
