import logging
import traceback
from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name='dtlpy')


class Ontologies:
    """
    Ontologies Repository

    The Ontologies class allows users to manage ontologies and their properties. Read more about ontology in our `SDK docs <https://dataloop.ai/docs/sdk-ontology>`_.
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
    def create(self,
               labels,
               title=None,
               project_ids=None,
               attributes=None
               ) -> entities.Ontology:
        """
        Create a new ontology.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param labels: recipe tags
        :param str title: ontology title, name
        :param list project_ids: recipe project/s
        :param list attributes: recipe attributes
        :return: Ontology object
        :rtype: dtlpy.entities.ontology.Ontology

        **Example**:

        .. code-block:: python

            recipe.ontologies.create(labels='labels_entity',
                                  title='new_ontology',
                                  project_ids='project_ids')
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
            if self._recipe:
                self._recipe.ontology_ids.append(ontology.id)
                self._recipe.update()
        else:
            logger.error("Failed to create Ontology")
            raise exceptions.PlatformException(response)
        return ontology

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Ontology]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_package, package in enumerate(response_items):
            jobs[i_package] = pool.submit(entities.Ontology._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': package,
                                             'project': self._project,
                                             'dataset': self._dataset,
                                             'recipe': self._recipe})

        # get all results
        results = [j.result() for j in jobs]
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
        List project ontologies.
        
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
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

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param project_ids:
        :return: list of all the ontologies

        **Example**:

        .. code-block:: python

            recipe.ontologies.list(project_ids='project_ids')
        """
        if self._recipe is not None:
            ontologies = [ontology_id for ontology_id in self.recipe.ontology_ids]

            pool = self._client_api.thread_pools(pool_name='entity.create')
            jobs = [None for _ in range(len(ontologies))]
            for i_ontology, ontology_id in enumerate(ontologies):
                jobs[i_ontology] = pool.submit(self._protected_get, **{'ontology_id': ontology_id})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            logger.warning('Deprecation Warning - return type will be pageEntity from version 1.46.0 not a list')
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
            logger.warning('Deprecation Warning - return type will be pageEntity from version 1.46.0 not a list')
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

    def get(self, ontology_id: str) -> entities.Ontology:
        """
        Get Ontology object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str ontology_id: ontology id
        :return: Ontology object
        :rtype: dtlpy.entities.ontology.Ontology

        **Example**:

        .. code-block:: python

            recipe.ontologies.get(ontology_id='ontology_id')
        """
        success, response = self._client_api.gen_request(req_type="get",
                                                         path="/ontologies/{}".format(ontology_id))
        if success:
            ontology = entities.Ontology.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   recipe=self._recipe,
                                                   dataset=self._dataset,
                                                   project=self._project)
        else:
            raise exceptions.PlatformException(response)
        return ontology

    def delete(self, ontology_id):
        """
        Delete Ontology from the platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param ontology_id: ontology id
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            recipe.ontologies.delete(ontology_id='ontology_id')
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
        Update the Ontology metadata.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

       :param dtlpy.entities.ontology.Ontology ontology: Ontology object
       :param bool system_metadata: bool - True, if you want to change metadata system
       :return: Ontology object
       :rtype: dtlpy.entities.ontology.Ontology

       **Example**:

        .. code-block:: python

            recipe.ontologies.delete(ontology='ontology_entity')
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
        Converts labels dictionary to a list of platform representation of labels.

        :param dict labels: labels dict
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

    def update_attributes(self,
                          ontology_id: str,
                          title: str,
                          key: str,
                          attribute_type: entities.AttributesTypes,
                          scope: list = None,
                          optional: bool = None,
                          multi: bool = None,
                          values: list = None,
                          attribute_range: entities.AttributesRange = None):
        """
        ADD a new attribute or update if exist

        :param str ontology_id: ontology_id
        :param str title: attribute title
        :param str key: the key of the attribute must br unique
        :param AttributesTypes attribute_type: dl.AttributesTypes your attribute type
        :param list scope: list of the labels or * for all labels
        :param bool optional: optional attribute
        :param bool multi: if can get multiple selection
        :param list values: list of the attribute values ( for checkbox and radio button)
        :param dict or AttributesRange attribute_range: dl.AttributesRange object
        :return: true in success
        :rtype: bool

        **Example**:

        .. code-block:: python

            ontology.update_attributes(key='1',
                                       title='checkbox',
                                       attribute_type=dl.AttributesTypes.CHECKBOX,
                                       values=[1,2,3])
        """
        if not title:
            raise exceptions.PlatformException(400, "title must be provided")
        url_path = '/ontologies/{ontology_id}/attributes'.format(ontology_id=ontology_id)

        # build attribute json
        attribute_json = {
            'title': title,
            'key': key,
            'type': attribute_type,
        }

        if optional is not None:
            attribute_json['optional'] = optional

        if multi is not None:
            attribute_json['multi'] = multi

        if values is not None:
            if not isinstance(values, list):
                values = [values]
            for val in values:
                if not isinstance(val, str):
                    raise exceptions.PlatformException(400, 'Attributes values type must be list of strings')
            attribute_json['values'] = values

        if attribute_range is not None:
            attribute_json['range'] = attribute_range.to_json()

        if scope is not None:
            if not isinstance(scope, list):
                scope = [scope]
        else:
            scope = ['*']
        attribute_json['scope'] = scope

        json_req = {
            'items': [attribute_json],
            'upsert': True
        }

        success, response = self._client_api.gen_request(req_type="PATCH",
                                                         path=url_path,
                                                         json_req=json_req)
        if not success:
            raise exceptions.PlatformException(response)
        return True

    def delete_attributes(self, ontology_id, keys: list):
        """
        Delete a bulk of attributes

        :param str ontology_id: ontology id
        :param list keys: Keys of attributes to delete
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            ontology.delete_attributes(['1'])
        """

        if not isinstance(keys, list):
            keys = [keys]
        url_path = '/ontologies/{ontology_id}/attributes'.format(ontology_id=ontology_id)
        json_req = {
            'keys': keys
        }
        success, response = self._client_api.gen_request(req_type="DELETE",
                                                         path=url_path,
                                                         json_req=json_req)
        if not success:
            raise exceptions.PlatformException(response)
        return True
