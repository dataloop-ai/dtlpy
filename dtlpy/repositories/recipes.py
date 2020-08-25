import logging
import traceback

from .. import entities, miscellaneous, repositories, exceptions, services

logger = logging.getLogger(name=__name__)


class Recipes:
    """
    Items repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
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
    def create(self, project_ids=None, ontology_ids=None, labels=None, recipe_name=None,
               attributes=None) -> entities.Recipe:
        """
        Create New Recipe

        if ontology_ids is None an ontology will be created first
        """
        if labels is None:
            labels = list()
        if attributes is None:
            attributes = list()
        if project_ids is None:
            if self._dataset is not None:
                project_ids = [self._dataset.project.id]
            else:
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
                   'ontologyIds': ontology_ids}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/recipes',
                                                         json_req=payload)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               dataset=self._dataset)
        else:
            logger.error('Failed to create Recipe')
            raise exceptions.PlatformException(response)

        if self._dataset is not None:
            # add recipe id to dataset system metadata
            if 'system' not in self._dataset.metadata:
                self._dataset.metadata['system'] = dict()
            if 'recipes' not in self._dataset.metadata['system']:
                self._dataset.metadata['system']['recipes'] = list()
            # TODO - supposed to be append but it doesn't work in platform
            self._dataset.metadata['system']['recipes'] = [recipe.id]
            self._dataset.update(system_metadata=True)
        return recipe

    def list(self, filters: entities.Filters = None) -> miscellaneous.List[entities.Recipe]:
        """
        List recipes for dataset
        """
        if self._dataset is not None:
            try:
                recipes = [recipe_id for recipe_id in self._dataset.metadata['system']['recipes']]
            except KeyError:
                recipes = list()

            pool = self._client_api.thread_pools(pool_name='entity.create')
            jobs = [None for _ in range(len(recipes))]
            for i_recipe, recipe_id in enumerate(recipes):
                jobs[i_recipe] = pool.apply_async(self._protected_get, kwds={'recipe_id': recipe_id})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all results
            results = [j.get() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            recipes = miscellaneous.List([r[1] for r in results if r[0] is True])
        elif self._project_id is not None:
            if filters is None:
                filters = entities.Filters(resource=entities.FiltersResource.RECIPE)

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

        # request
        success, response = self._client_api.gen_request(req_type='get', path=url)
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Recipe]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_rec, rec in enumerate(response_items):
            jobs[i_rec] = pool.apply_async(entities.Recipe._protected_from_json,
                                           kwds={'client_api': self._client_api,
                                                 '_json': rec,
                                                 'project': self._project,
                                                 'dataset': self._dataset})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
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

    def get(self, recipe_id) -> entities.Recipe:
        """
        Get Recipe object

        :param recipe_id: recipe id
        :return: Recipe object
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/recipes/%s' % recipe_id)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               dataset=self._dataset)
        else:
            logger.error('Unable to get info from recipe. Recipe_id id: {}'.format(recipe_id))
            raise exceptions.PlatformException(response)

        return recipe

    def delete(self, recipe_id):
        """
        Delete recipe from platform

        :param recipe_id: recipe id
        :return: True
        """
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path='/recipes/%s' % recipe_id)
        if not success:
            raise exceptions.PlatformException(response)
        logger.info('Recipe id {} deleted successfully'.format(recipe_id))
        return True

    def update(self, recipe: entities.Recipe, system_metadata=False) -> entities.Recipe:
        """
        Update items metadata

        :param recipe: Recipe object
        :param system_metadata: bool
        :return: Recipe object
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
