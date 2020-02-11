from collections import namedtuple
import logging
import attr

from .. import repositories, miscellaneous, entities, services

logger = logging.getLogger(name=__name__)


@attr.s
class Recipe:
    """
    Recipe object
    """
    id = attr.ib()
    creator = attr.ib()
    url = attr.ib(repr=False)
    title = attr.ib()
    projectIds = attr.ib()
    description = attr.ib()
    ontologyIds = attr.ib(repr=False)
    instructions = attr.ib(repr=False)
    examples = attr.ib(repr=False)
    customActions = attr.ib(repr=False)
    metadata = attr.ib()

    # name change
    ui_settings = attr.ib()

    # platform
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    # entities
    _dataset = attr.ib(repr=False)
    # repositories
    _repositories = attr.ib(repr=False)

    @classmethod
    def from_json(cls, _json, dataset, client_api):
        """
        Build a Recipe entity object from a json

        :param _json: _json response from host
        :param dataset: recipe's dataset
        :param client_api: client_api
        :return: Recipe object
        """
        return cls(
            client_api=client_api,
            dataset=dataset,
            id=_json['id'],
            creator=_json['creator'],
            url=_json['url'],
            title=_json['title'],
            projectIds=_json['projectIds'],
            description=_json['description'],
            ontologyIds=_json['ontologyIds'],
            instructions=_json['instructions'],
            ui_settings=_json.get('uiSettings', None),
            metadata=_json['metadata'],
            examples=_json['examples'],
            customActions=_json['customActions'])

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['ontologies', 'recipes'])
        if self.dataset is None:
            recipes = repositories.Recipes(client_api=self._client_api, dataset=self.dataset)
        else:
            recipes = self.dataset.recipes
        r = reps(ontologies=repositories.Ontologies(recipe=self, client_api=self._client_api),
                 recipes=recipes)
        return r

    @property
    def dataset(self):
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def recipes(self):
        assert isinstance(self._repositories.recipes, repositories.Recipes)
        return self._repositories.recipes

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Recipe)._client_api,
                                                              attr.fields(Recipe)._dataset,
                                                              attr.fields(Recipe).ui_settings,
                                                              attr.fields(Recipe)._repositories))
        _json['uiSettings'] = self.ui_settings
        return _json

    def print(self):
        """
        Display

        :return:
        """
        miscellaneous.List([self]).print()

    def delete(self):
        """
        Delete recipe from platform

        :return: True
        """
        return self.recipes.delete(self.id)

    def update(self, system_metadata=False):
        """
        Update Recipe

        :param system_metadata: bool
        :return: Recipe object
        """
        return self.recipes.update(recipe=self, system_metadata=system_metadata)
