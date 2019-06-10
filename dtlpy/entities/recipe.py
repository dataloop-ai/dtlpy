import logging
from .. import repositories, utilities
import attr

logger = logging.getLogger('dataloop.item')


@attr.s
class Recipe:
    """
    Recipe object
    """
    # platform
    client_api = attr.ib()
    id = attr.ib()
    creator = attr.ib()
    url = attr.ib()
    title = attr.ib()
    projectIds = attr.ib()
    description = attr.ib()
    ontologyIds = attr.ib()
    instructions = attr.ib()
    examples = attr.ib()
    customActions = attr.ib()

    # entities
    dataset = attr.ib()
    # repositories
    _ontologies = attr.ib()

    @classmethod
    def from_json(cls, _json, dataset, client_api):
        """
        Build a Recipe entity object from a json

        :param _json: _json respons from host
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
            examples=_json['examples'],
            customActions=_json['customActions'])

    @_ontologies.default
    def set_ontologies(self):
        return repositories.Ontologies(recipe=self, client_api=self.client_api)

    @property
    def ontologies(self):
        assert isinstance(self._ontologies, repositories.Ontologies)
        return self._ontologies

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Recipe).dataset,
                                                              attr.fields(Recipe)._ontologies,
                                                              attr.fields(Recipe).client_api))
        return _json

    def print(self):
        utilities.List([self]).print()

    def delete(self):
        """
        Delete recipe from platform
        :return: True
        """
        return self.dataset.recipes.delete(self.id)

    def update(self, system_metadata=False):
        """
        Update Recipe
        :param system_metadata: bool
        :return: Recipe object
        """
        return self.dataset.recipes.update(recipe=self, system_metadata=system_metadata)
