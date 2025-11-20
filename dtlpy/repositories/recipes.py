import logging
import traceback
import urllib.parse

from .. import entities, miscellaneous, repositories, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Recipes:
    """
    Recipes Repository

    The Recipes class allows you to manage recipes and their properties.
    For more information on Recipes, see our `documentation <https://dataloop.ai/docs/ontology>`_ and `developers' documentation <https://developers.dataloop.ai/tutorials/recipe_and_ontology/recipe/chapter/>`_.
    """

    def __init__(self,
                 client_api: ApiClient,
                 dataset: entities.Dataset = None,
                 project: entities.Project = None,
                 project_id: str = None):
        self._client_api = client_api
        self._dataset = dataset
        self._project = project
        self._project_id = project_id
        if project_id is None and project is not None:
            self._project_id = project.id

    ############
    # entities #
    ############
    @property
    def platform_url(self):
        if self._project_id is None:
            project_id = self.dataset.project.id
        else:
            project_id = self._project_id
        return self._client_api._get_resource_url("projects/{}/recipes".format(project_id))

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            if self._project_id is None:
                if self._dataset is None:
                    raise exceptions.PlatformException(
                        error='2001',
                        message='Missing "Project". need to set a Project entity or use project.recipes repository'
                    )
                else:
                    self._project = self._dataset.project
                    self._project_id = self._project.id
            else:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=self._project_id)
                self._project_id = self._project.id

        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project
        self._project_id = project.id

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.recipes repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    ###########
    # methods #
    ###########
    @_api_reference.add(path='/recipes', method='post')
    def create(self,
               project_ids=None,
               ontology_ids=None,
               labels=None,
               recipe_name=None,
               attributes=None,
               annotation_instruction_file=None
               ) -> entities.Recipe:
        """
        Create a new Recipe.
        Note: If the param ontology_ids is None, an ontology will be created first.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str project_ids: project ids
        :param str or list ontology_ids: ontology ids
        :param labels: labels
        :param str recipe_name: recipe name
        :param attributes: attributes
        :param str annotation_instruction_file: file path or url of the recipe instruction
        :return: Recipe entity
        :rtype: dtlpy.entities.recipe.Recipe

        **Example**:

        .. code-block:: python

            dataset.recipes.create(recipe_name='My Recipe', labels=labels))
        """
        if labels is None:
            labels = list()
        if attributes is None:
            attributes = list()
        if project_ids is None:
            if self._dataset is not None:
                project_ids = [self._dataset.project.id]
            else:
                # get from cache
                project = self._client_api.state_io.get('project')
                if project is not None:
                    # build entity from json
                    p = entities.Project.from_json(_json=project, client_api=self._client_api)
                    project_ids = [p.id]
                else:
                    # get from self.project property
                    try:
                        project_ids = [self.project.id]
                    except exceptions.PlatformException:
                        raise exceptions.PlatformException('Must provide project_ids')
        if ontology_ids is None:
            ontolgies = repositories.Ontologies(client_api=self._client_api,
                                                recipe=None)
            ontology = ontolgies.create(labels=labels,
                                        project_ids=project_ids,
                                        attributes=attributes)
            ontology_ids = [ontology.id]
        elif not isinstance(ontology_ids, list):
            ontology_ids = [ontology_ids]
        if recipe_name is None:
            recipe_name = self._dataset.name + " Default Recipe" if self._dataset is not None else "Default Recipe"
        payload = {'title': recipe_name,
                   'projectIds': project_ids,
                   'ontologyIds': ontology_ids,
                   'uiSettings': {
                       "allowObjectIdAutoAssign": True,
                       "studioV2App": True
                   }}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/recipes',
                                                         json_req=payload)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               dataset=self._dataset)
            if annotation_instruction_file:
                recipe.add_instruction(annotation_instruction_file=annotation_instruction_file)
        else:
            logger.error('Failed to create Recipe')
            raise exceptions.PlatformException(response)

        if self._dataset is not None:
            self._dataset.switch_recipe(recipe.id)
        return recipe

    def list(self, filters: entities.Filters = None) -> miscellaneous.List[entities.Recipe]:
        """
        List recipes for a dataset.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: list of all recipes
        :retype: list

        **Example**:

        .. code-block:: python

            dataset.recipes.list()
        """
        if self._dataset is not None:
            try:
                recipes = [recipe_id for recipe_id in self._dataset.metadata['system']['recipes']]
            except KeyError:
                recipes = list()

            pool = self._client_api.thread_pools(pool_name='entity.create')
            jobs = [None for _ in range(len(recipes))]
            for i_recipe, recipe_id in enumerate(recipes):
                jobs[i_recipe] = pool.submit(self._protected_get, **{'recipe_id': recipe_id})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            recipes = miscellaneous.List([r[1] for r in results if r[0] is True])
        elif self._project_id is not None:
            if filters is None:
                filters = entities.Filters(resource=entities.FiltersResource.RECIPE)
            # assert type filters
            elif not isinstance(filters, entities.Filters):
                raise exceptions.PlatformException(error='400',
                                                   message='Unknown filters type: {!r}'.format(type(filters)))
            if filters.resource != entities.FiltersResource.RECIPE:
                raise exceptions.PlatformException(
                    error='400',
                    message='Filters resource must to be FiltersResource.RECIPE. Got: {!r}'.format(filters.resource))
            if not filters.has_field('projects'):
                filters.add(field='projects', values=[self._project_id])

            recipes = entities.PagedEntities(items_repository=self,
                                             filters=filters,
                                             page_offset=filters.page,
                                             page_size=filters.page_size,
                                             project_id=self._project_id,
                                             client_api=self._client_api)
            recipes.get_page()
        else:
            raise exceptions.PlatformException('400', 'Must have project or dataset entity in repository')

        return recipes

    def _list(self, filters: entities.Filters):
        url = filters.generate_url_query_params('/recipes')
        encoded_url = urllib.parse.quote(url, safe='/:?=&')
        # request
        success, response = self._client_api.gen_request(req_type='get', path=encoded_url)
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Recipe]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_rec, rec in enumerate(response_items):
            jobs[i_rec] = pool.submit(entities.Recipe._protected_from_json,
                                      **{'client_api': self._client_api,
                                         '_json': rec,
                                         'project': self._project,
                                         'dataset': self._dataset})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        recipes = miscellaneous.List([r[1] for r in results if r[0] is True])
        return recipes

    def _protected_get(self, recipe_id):
        """
        Same as get but with try-except to catch if error
        :param recipe_id:
        :return:
        """
        try:
            recipe = self.get(recipe_id=recipe_id)
            status = True
        except Exception:
            recipe = traceback.format_exc()
            status = False
        return status, recipe

    @_api_reference.add(path='/recipes/{id}', method='get')
    def get(self, recipe_id: str) -> entities.Recipe:
        """
        Get a Recipe object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str recipe_id: recipe id
        :return: Recipe object
        :rtype: dtlpy.entities.recipe.Recipe

        **Example**:

        .. code-block:: python

            dataset.recipes.get(recipe_id='recipe_id')
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/recipes/%s' % recipe_id)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               project=self._project,
                                               dataset=self._dataset)
        else:
            logger.error('Unable to get info from recipe. Recipe_id id: {}'.format(recipe_id))
            raise exceptions.PlatformException(response)

        return recipe

    def open_in_web(self,
                    recipe: entities.Recipe = None,
                    recipe_id: str = None):
        """
        Open the recipe in web platform.

        **Prerequisites**: All users.

        :param dtlpy.entities.recipe.Recipe recipe: recipe entity
        :param str recipe_id: recipe id

        **Example**:

        .. code-block:: python

            dataset.recipes.open_in_web(recipe_id='recipe_id')
        """
        if recipe is not None:
            recipe.open_in_web()
        elif recipe_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(recipe_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    @_api_reference.add(path='/recipes/{id}', method='delete')
    def delete(self, recipe_id: str, force: bool = False):
        """
        Delete recipe from platform.
        
        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str recipe_id: recipe id
        :param bool force: force delete recipe
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.recipes.delete(recipe_id='recipe_id')
        """
        path = '/recipes/{}'.format(recipe_id)
        if force:
            path += '?force=true'
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=path)
        if not success:
            raise exceptions.PlatformException(response)
        logger.info('Recipe id {} deleted successfully'.format(recipe_id))
        return True

    @_api_reference.add(path='/recipes/{id}', method='patch')
    def update(self, recipe: entities.Recipe, system_metadata=False) -> entities.Recipe:
        """
        Update recipe.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.recipe.Recipe recipe: Recipe object
        :param bool system_metadata: True, if you want to change metadata system
        :return: Recipe object
        :rtype: dtlpy.entities.recipe.Recipe

        **Example**:

        .. code-block:: python

            dataset.recipes.update(recipe='recipe_entity')
        """
        url_path = '/recipes/%s' % recipe.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=recipe.to_json())
        if success:
            return entities.Recipe.from_json(client_api=self._client_api, _json=response.json(), dataset=self._dataset)
        else:
            logger.error('Error while updating item:')
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/recipes/{id}/clone', method='post')
    def clone(self,
              recipe: entities.Recipe = None,
              recipe_id: str = None,
              shallow: bool = False):
        """
        Clone recipe.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

       :param dtlpy.entities.recipe.Recipe recipe: Recipe object
       :param str recipe_id: Recipe id
       :param bool shallow: If True, link to existing ontology, clones all ontologies that are linked to the recipe as well
       :return: Cloned ontology object
       :rtype: dtlpy.entities.recipe.Recipe

       **Example**:

        .. code-block:: python

            dataset.recipes.clone(recipe_id='recipe_id')
       """
        if recipe is None and recipe_id is None:
            raise exceptions.PlatformException('400', 'Must provide recipe or recipe_id')
        if recipe_id is None:
            if not isinstance(recipe, entities.Recipe):
                raise exceptions.PlatformException('400', 'Recipe must me entities.Recipe type')
            else:
                recipe_id = recipe.id

        payload = {'shallow': shallow}

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/recipes/{}/clone'.format(recipe_id),
                                                         json_req=payload)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json())
        else:
            logger.error('Failed to clone Recipe')
            raise exceptions.PlatformException(response)

        assert isinstance(recipe, entities.Recipe)
        logger.debug('Recipe has been cloned successfully. recipe id: {}'.format(recipe.id))

        return recipe
