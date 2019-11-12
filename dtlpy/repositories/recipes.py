import logging
import traceback

from .. import entities, miscellaneous, repositories, PlatformException

logger = logging.getLogger(name=__name__)


class Recipes:
    """
    Items repository
    """

    def __init__(self, client_api, dataset):
        self._client_api = client_api
        self._dataset = dataset

    @property
    def dataset(self):
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

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
            ontolgies = repositories.Ontologies(client_api=self._client_api,
                                                recipe=None)
            ontology = ontolgies.create(labels=labels,
                                        project_ids=[self.dataset.project.id],
                                        attributes=attributes)
            ontology_ids = [ontology.id]
        elif not isinstance(ontology_ids, list):
            ontology_ids = [ontology_ids]
        if recipe_name is None:
            recipe_name = self.dataset.name + " Default Recipe"
        payload = {'title': recipe_name,
                   'projectIds': project_ids,
                   'ontologyIds': ontology_ids}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/recipes',
                                                         json_req=payload)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               dataset=self.dataset)
        else:
            logger.exception('Failed to create Recipe')
            raise PlatformException(response)

        # add recipe id to dataset system metadata
        if 'system' not in self.dataset.metadata:
            self.dataset.metadata['system'] = dict()
        if 'recipes' not in self.dataset.metadata['system']:
            self.dataset.metadata['system']['recipes'] = list()
        # TODO - supposed to be append but it doesn't work in platform
        self.dataset.metadata['system']['recipes'] = [recipe.id]
        self.dataset.update(system_metadata=True)
        return recipe

    def list(self):
        """
        List recipes for dataset
        """
        recipes = list()
        if self.dataset.metadata is not None and 'system' in self.dataset.metadata and 'recipes' in \
                self.dataset.metadata['system']:
            recipes = [recipe_id for recipe_id in self.dataset.metadata['system']['recipes']]

        results = [None for _ in range(len(recipes))]
        for i_recipe, recipe_id in enumerate(recipes):
            results[i_recipe] = self._protected_get(recipe_id=recipe_id)

        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _protected_get(self, recipe_id):
        try:
            recipe = self.get(recipe_id=recipe_id)
            status = True
        except:
            recipe = traceback.format_exc()
            status = False
        return status, recipe

    def get(self, recipe_id):
        """
        Get Recipe object

        :param recipe_id: recipe id
        :return: Recipe object
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/recipes/%s' % recipe_id)
        if success:
            recipe = entities.Recipe.from_json(client_api=self._client_api, _json=response.json(), dataset=self.dataset)
        else:
            logger.exception(
                'Unable to get info from recipe. dataset id: {}, recipe_id id: {}'.format(self.dataset.id, recipe_id))
            raise PlatformException(response)

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
            raise PlatformException(response)
        logger.info('Recipe id {} deleted successfully'.format(recipe_id))
        return True

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
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=recipe.to_json())
        if success:
            return entities.Recipe.from_json(client_api=self._client_api, _json=response.json(), dataset=self.dataset)
        else:
            logger.exception('Error while updating item:')
            raise PlatformException(response)
