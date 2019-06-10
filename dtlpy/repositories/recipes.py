import logging
from multiprocessing.pool import ThreadPool

from .. import entities, utilities, repositories, PlatformException


class Recipes:
    """
    Items repository
    """

    def __init__(self, client_api, dataset):
        self.logger = logging.getLogger('dataloop.repositories.recipes')
        self.client_api = client_api
        self.dataset = dataset

    def create(self, project_ids=None, ontology_ids=None, labels=None, recipe_name=None, attributes=None):
        """
        Create New Recipe

        if ontology_ids is None an ontology will be created first
        """
        if labels is None:
            labels = list()
        if attributes is None:
            attributes = list()
        if project_ids is None:
            project_ids = [self.dataset.project.id]
        if ontology_ids is None:
            ontolgies = repositories.Ontologies(client_api=self.client_api, recipe=None)
            ontology = ontolgies.create(labels=labels, project_ids=[self.dataset.project.id], attributes=attributes)
            ontology_ids = [ontology.id]
        elif not isinstance(ontology_ids, list):
            ontology_ids = [ontology_ids]
        if recipe_name is None:
            title = self.dataset.name + " Default Recipe"
        else:
            title = recipe_name
        payload = {'title': title, 'projectIds': project_ids, 'ontologyIds': ontology_ids}
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/recipes',
                                                        json_req=payload)
        if success:
            recipe = entities.Recipe.from_json(client_api=self.client_api, _json=response.json(), dataset=self.dataset)
        else:
            self.logger.exception('Failed to create Recipe')
            raise PlatformException(response)
        return recipe

    def list(self):
        """
        List recipes for dataset
        """
        recipes = list()
        recipes = list()
        if self.dataset.metadata is not None and 'system' in self.dataset.metadata and 'recipes' in \
                self.dataset.metadata['system']:
            recipes = [recipe_id for recipe_id in self.dataset.metadata['system']['recipes']]

        def get_single_recipe(w_i_recipe):
            recipes[w_i_recipe] = self.get(recipe_id=recipes[w_i_recipe])

        pool = ThreadPool(processes=32)
        for i_recipe in range(len(recipes)):
            pool.apply_async(get_single_recipe, kwds={'w_i_recipe': i_recipe})
        pool.close()
        pool.join()
        pool.terminate()

        return utilities.List(recipes)

    def get(self, recipe_id):
        """
        Get Recipe object

        :param recipe_id: recipe id
        :return: Recipe object
        """
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/recipes/%s' % recipe_id)
        if success:
            recipe = entities.Recipe.from_json(client_api=self.client_api, _json=response.json(), dataset=self.dataset)
        else:
            self.logger.exception(
                'Unable to get info from recipe. dataset id: %s, recipe_id id: %s' % (self.dataset.id, recipe_id))
            raise PlatformException(response)

        return recipe

    def delete(self, recipe_id):
        """
        Delete recipe from platform

        :param recipe_id: recipe id
        :return: True
        """
        success, response = self.client_api.gen_request(req_type='delete',
                                                        path='/recipes/%s' % recipe_id)

        return success

    def update(self, recipe, system_metadata=False):
        """
        Update items metadata

        :param recipe: Recipe object
        :param system_metadata: bool
        :return: Recipe object
        """
        url_path = '/recipes/%s' % recipe.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=recipe.to_json())
        if success:
            return entities.Recipe.from_json(client_api=self.client_api, _json=response.json(), dataset=self.dataset)
        else:
            self.logger.exception('Error while updating item')
            raise PlatformException(response)
