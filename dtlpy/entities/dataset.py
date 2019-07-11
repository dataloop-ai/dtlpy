import os
import logging
import attr

from .. import repositories, utilities

logger = logging.getLogger('dataloop.dataset')


@attr.s
class Dataset:
    """
    Dataset object
    """
    client_api = attr.ib()
    id = attr.ib()
    url = attr.ib()
    name = attr.ib()
    annotated = attr.ib()
    creator = attr.ib()
    projects = attr.ib()
    itemsCount = attr.ib()
    metadata = attr.ib()
    items_url = attr.ib()
    directoryTree = attr.ib()
    export = attr.ib()

    # entities
    project = attr.ib()

    # repositories
    _items = attr.ib()
    _recipes = attr.ib()

    # defaults
    _ontology_ids = attr.ib(default=None)
    _labels = attr.ib(default=None)

    @classmethod
    def from_json(cls, project, _json, client_api):
        """
        Build a Dataset entity object from a json

        :param _json: _json respons form host
        :param project: dataset's project
        :param client_api: client_api
        :return: Dataset object
        """
        if 'metadata' in _json:
            metadata = _json['metadata']
        else:
            metadata = None

        return cls(
            client_api=client_api,
            annotated=_json['annotated'],
            creator=_json['creator'],
            directoryTree=_json['directoryTree'],
            export=_json['export'],
            id=_json['id'],
            items_url=_json['items'],
            itemsCount=_json['itemsCount'],
            name=_json['name'],
            projects=_json['projects'],
            url=_json['url'],
            project=project,
            metadata=metadata)

    @property
    def labels(self):
        if self._labels is None:
            self._labels = self.recipes.list()[0].ontologies.list()[0].labels
        return self._labels

    @labels.setter
    def labels(self, labels):
        self._labels = labels

    @property
    def ontology_ids(self):
        if self._ontology_ids is None:
            self._ontology_ids = list()
            if self.metadata is not None and 'system' in self.metadata and 'recipes' in self.metadata['system']:
                recipe_ids = self.get_recipe_ids()
                for rec_id in recipe_ids:
                    recipe = self.recipes.get(recipe_id=rec_id)
                    self._ontology_ids += recipe.ontologyIds
        return self._ontology_ids

    @_items.default
    def set_items(self):
        return repositories.Items(dataset=self, client_api=self.client_api)

    @property
    def items(self):
        assert isinstance(self._items, repositories.Items)
        return self._items

    @_recipes.default
    def set_recipes(self):
        return repositories.Recipes(dataset=self, client_api=self.client_api)

    @property
    def recipes(self):
        assert isinstance(self._recipes, repositories.Recipes)
        return self._recipes

    def __copy__(self):
        return Dataset.from_json(_json=self.to_json(), project=self.project, client_api=self.client_api)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Dataset)._items,
                                                              attr.fields(Dataset).items_url,
                                                              attr.fields(Dataset).project,
                                                              attr.fields(Dataset)._recipes,
                                                              attr.fields(Dataset).client_api))
        _json.update({'items': self.items_url})
        return _json

    def __get_local_path__(self):
        if self.project is not None:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'projects', self.project.name,
                                      'datasets', self.name)
        else:
            local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                      'datasets', '%s_%s' % (self.name, self.id))
        return local_path

    def print(self):
        utilities.List([self]).print()

    @staticmethod
    def serialize_labels(labels_dict):
        """
        Convert hex color format to rgb

        :param labels_dict: dict of labels
        :return: dict of converted labels
        """
        dataset_labels_dict = dict()
        for label, color in labels_dict.items():
            dataset_labels_dict[label] = '#%02x%02x%02x' % color
        return dataset_labels_dict

    def get_recipe_ids(self):
        """
        Get dataset recipe Ids

        :return: list of recipe ids
        """
        return self.metadata['system']['recipes']

    def delete(self, sure=False, really=False):
        """
        Delete a dataset forever!
        :param sure: are you sure you want to delete?
        :param really: really really?
        :return:
        """
        return self.project.datasets.delete(dataset_id=self.id,
                                            sure=sure,
                                            really=really)

    def update(self, system_metadata=False):
        """
        Update dataset field
        :param system_metadata: bool - True, if you want to change metadata system
        :return:
        """
        return self.project.datasets.update(dataset=self, system_metadata=system_metadata)

    def download_annotations(self, local_path, overwrite=False):
        return self.project.datasets.download_annotations(dataset=self,
                                                          local_path=local_path,
                                                          overwrite=overwrite)
