from collections import namedtuple
import logging
import attr
import os

from .. import repositories, utilities, entities, services

logger = logging.getLogger(name=__name__)


@attr.s
class Dataset:
    """
    Dataset object
    """
    # dataset information
    id = attr.ib()
    url = attr.ib()
    name = attr.ib()
    annotated = attr.ib()
    creator = attr.ib()
    projects = attr.ib()
    itemsCount = attr.ib()
    metadata = attr.ib()
    items_url = attr.ib()  # name change when to_json
    directoryTree = attr.ib()
    export = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient)

    # entities
    _project = attr.ib(default=None)

    # repositories
    _repositories = attr.ib()

    # defaults
    _ontology_ids = attr.ib(default=None)
    _labels = attr.ib(default=None)

    @classmethod
    def from_json(cls, project, _json, client_api):
        """
        Build a Dataset entity object from a json

        :param _json: _json response form host
        :param project: dataset's project
        :param client_api: client_api
        :return: Dataset object
        """
        return cls(metadata=_json.get('metadata', None),
                   directoryTree=_json['directoryTree'],
                   itemsCount=_json['itemsCount'],
                   annotated=_json['annotated'],
                   projects=_json['projects'],
                   creator=_json['creator'],
                   items_url=_json['items'],
                   export=_json['export'],
                   name=_json['name'],
                   url=_json['url'],
                   id=_json['id'],

                   client_api=client_api,
                   project=project)

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Dataset)._client_api,
                                                              attr.fields(Dataset)._project,
                                                              attr.fields(Dataset)._repositories,
                                                              attr.fields(Dataset)._ontology_ids,
                                                              attr.fields(Dataset)._labels,
                                                              attr.fields(Dataset).items_url))
        _json.update({'items': self.items_url})
        return _json

    @property
    def labels(self):
        if self._labels is None:
            self._labels = self.recipes.list()[0].ontologies.list()[0].labels
        return self._labels

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

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['items', 'recipes', 'datasets'])
        if self._project is None:
            datasets = repositories.Datasets(client_api=self._client_api, project=self._project)
        else:
            datasets = self._project.datasets

        r = reps(items=repositories.Items(client_api=self._client_api, dataset=self),
                 recipes=repositories.Recipes(client_api=self._client_api, dataset=self),
                 datasets=datasets)
        return r

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

    @property
    def recipes(self):
        assert isinstance(self._repositories.recipes, repositories.Recipes)
        return self._repositories.recipes

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def project(self):
        if self._project is None:
            # get project from the dataset information
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.projects[0])
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        self._project = project

    def __copy__(self):
        return Dataset.from_json(_json=self.to_json(), project=self._project, client_api=self._client_api)

    def __get_local_path__(self):
        if self._project is not None:
            local_path = os.path.join(os.path.expanduser('~'),
                                      '.dataloop',
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
        return self.datasets.delete(dataset_id=self.id,
                                    sure=sure,
                                    really=really)

    def update(self, system_metadata=False):
        """
        Update dataset field

        :param system_metadata: bool - True, if you want to change metadata system
        :return:
        """
        return self.datasets.update(dataset=self,
                                    system_metadata=system_metadata)

    def download_annotations(self, local_path, overwrite=False):
        return self.datasets.download_annotations(dataset=self,
                                                  local_path=local_path,
                                                  overwrite=overwrite)

    def checkout(self):
        """
        Checkout the dataset

        :return:
        """
        self.datasets.checkout(identifier=self.name)

    def open_in_web(self):
        """
        Open the dataset in web platform

        :return:
        """
        self.datasets.open_in_web(dataset=self)

    def add_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                  recipe_id=None, ontology_id=None):
        """
        Add single label to dataset

        :param label_name:
        :param color:
        :param children:
        :param attributes:
        :param display_label:
        :param label:
        :param recipe_id: optional
        :param ontology_id: optional
        :return: label entity
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontologyIds[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)

        # add label
        added_label = ontology.add_label(label_name=label_name,
                                         color=color,
                                         children=children,
                                         attributes=attributes,
                                         display_label=display_label,
                                         label=label)

        # update and return
        ontology = ontology.update(system_metadata=True)
        self._labels = ontology.labels
        return added_label

    def add_labels(self, label_list, ontology_id=None, recipe_id=None):
        """
        Add labels to dataset

        :param label_list:
        :param recipe_id: optional
        :param ontology_id: optional
        :return: label entities
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontologyIds[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)

        # add labels to ontology
        added_labels = ontology.add_labels(label_list=label_list)

        # update and return
        ontology = ontology.update(system_metadata=True)
        self._labels = ontology.labels
        return added_labels
