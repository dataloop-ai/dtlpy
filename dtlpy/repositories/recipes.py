import logging
import traceback

from .. import entities, miscellaneous, repositories, exceptions

logger = logging.getLogger(name=__name__)


class Recipes:
    """
    Items repository
    """

    def __init__(self, client_api, dataset):
        self._client_api = client_api
        self._dataset = dataset

    ############
    # entities #
    ############
    @property
    def dataset(self):
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.recipes repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    ###########
    # methods #
    ###########
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
            raise exceptions.PlatformException(response)

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

        try:
            recipes = [recipe_id for recipe_id in self.dataset.metadata['system']['recipes']]
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
        return miscellaneous.List([r[1] for r in results if r[0] is True])

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

    def get(self, recipe_id):
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
                                               dataset=self.dataset)
        else:
            logger.exception(
                'Unable to get info from recipe. dataset id: {}, recipe_id id: {}'.format(self.dataset.id, recipe_id))
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
            raise exceptions.PlatformException(response)
