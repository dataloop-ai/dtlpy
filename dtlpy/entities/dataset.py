from collections import namedtuple
import traceback
import logging
import attr
import os

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


@attr.s
class Dataset(entities.BaseEntity):
    """
    Dataset object
    """
    # dataset information
    id = attr.ib()
    url = attr.ib()
    name = attr.ib()
    annotated = attr.ib(repr=False)
    creator = attr.ib()
    projects = attr.ib(repr=False)
    itemsCount = attr.ib()
    metadata = attr.ib(repr=False)
    items_url = attr.ib(repr=False)  # name change when to_json
    directoryTree = attr.ib(repr=False)
    export = attr.ib(repr=False)

    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _instance_map = attr.ib(default=None, repr=False)

    # entities
    _project = attr.ib(default=None, repr=False)

    # repositories
    _datasets = attr.ib(repr=False, default=None)
    _repositories = attr.ib(repr=False)

    # defaults
    _ontology_ids = attr.ib(default=None, repr=False)
    _labels = attr.ib(default=None, repr=False)
    _directory_tree = attr.ib(default=None, repr=False)

    @staticmethod
    def _protected_from_json(project, _json, client_api, datasets=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
         :param is_fetched: is Entity fetched from Platform
        :param _json: _json response from host
        :param project: dataset's project
        :param datasets: Datasets repository
        :param client_api: client_api
        :return: Dataset object
        """
        try:
            dataset = Dataset.from_json(project=project,
                                        _json=_json,
                                        client_api=client_api,
                                        datasets=datasets,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            dataset = traceback.format_exc()
            status = False
        return status, dataset

    @classmethod
    def from_json(cls, project, _json, client_api, datasets=None, is_fetched=True):
        """
        Build a Dataset entity object from a json

        :param is_fetched: is Entity fetched from Platform
        :param _json: _json response from host
        :param project: dataset's project
        :param datasets: Datasets repository
        :param client_api: client_api
        :return: Dataset object
        """
        inst = cls(metadata=_json.get('metadata', None),
                   directoryTree=_json.get('directoryTree', None),
                   itemsCount=_json.get('itemsCount', None),
                   annotated=_json.get('annotated', None),
                   projects=_json.get('projects', None),
                   creator=_json.get('creator', None),
                   items_url=_json.get('items', None),
                   export=_json.get('export', None),
                   name=_json.get('name', None),
                   url=_json.get('url', None),
                   id=_json.get('id', None),
                   datasets=datasets,
                   client_api=client_api,
                   project=project)
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Dataset)._client_api,
                                                              attr.fields(Dataset)._project,
                                                              attr.fields(Dataset)._datasets,
                                                              attr.fields(Dataset)._repositories,
                                                              attr.fields(Dataset)._ontology_ids,
                                                              attr.fields(Dataset)._labels,
                                                              attr.fields(Dataset)._directory_tree,
                                                              attr.fields(Dataset)._instance_map,
                                                              attr.fields(Dataset).items_url))
        _json.update({'items': self.items_url})
        return _json

    @property
    def labels(self):
        if self._labels is None:
            self._labels = self.recipes.list()[0].ontologies.list()[0].labels
        return self._labels

    @property
    def labels_flat_dict(self):
        flatten_dict = dict()

        def add_to_dict(tag, father):
            flatten_dict[tag] = father
            for child in father.children:
                add_to_dict('{}.{}'.format(tag, child.tag), child)

        for label in self.labels:
            add_to_dict(label.tag, label)
        return flatten_dict

    @property
    def instance_map(self):
        if self._instance_map is None:
            labels = [label for label in self.labels_flat_dict]
            labels.sort()
            # each label gets index as instance id
            self._instance_map = {label: (i_label + 1) for i_label, label in enumerate(labels)}
        return self._instance_map

    @instance_map.setter
    def instance_map(self, value):
        """
        instance mapping for creating instance mask
        :param value: dictionary {label: map_id}
        """
        if not isinstance(value, dict):
            raise ValueError('input must be a dictionary of {lable_name: instance_id}')
        self._instance_map = value

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
                          field_names=['items', 'recipes', 'datasets', 'assignments', 'tasks', 'annotations'])
        if self._project is None:
            datasets = repositories.Datasets(client_api=self._client_api, project=self._project)
        else:
            datasets = self._project.datasets

        r = reps(items=repositories.Items(client_api=self._client_api, dataset=self, datasets=datasets),
                 recipes=repositories.Recipes(client_api=self._client_api, dataset=self),
                 assignments=repositories.Assignments(project=self._project, client_api=self._client_api, dataset=self),
                 tasks=repositories.Tasks(client_api=self._client_api, project=self._project, dataset=self),
                 annotations=repositories.Annotations(client_api=self._client_api, dataset=self),
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
    def assignments(self):
        assert isinstance(self._repositories.assignments, repositories.Assignments)
        return self._repositories.assignments

    @property
    def tasks(self):
        assert isinstance(self._repositories.tasks, repositories.Tasks)
        return self._repositories.tasks

    @property
    def annotations(self):
        assert isinstance(self._repositories.annotations, repositories.Annotations)
        return self._repositories.annotations

    @property
    def project(self):
        if self._project is None:
            # get from cache
            project = self._client_api.state_io.get('project')
            if project is not None:
                # build entity from json
                p = entities.Project.from_json(_json=project, client_api=self._client_api)
                # check if dataset belongs to project
                if p.id in self.projects:
                    self._project = p
        if self._project is None:
            self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.projects[0],
                                                                                   fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def directory_tree(self):
        if self._directory_tree is None:
            self._directory_tree = self.project.datasets.directory_tree(dataset_id=self.id)
        assert isinstance(self._directory_tree, entities.DirectoryTree)
        return self._directory_tree

    def __copy__(self):
        return Dataset.from_json(_json=self.to_json(),
                                 project=self._project,
                                 client_api=self._client_api,
                                 is_fetched=self.is_fetched,
                                 datasets=self.datasets)

    def __get_local_path__(self):
        if self._project is not None:
            local_path = os.path.join(os.path.expanduser('~'),
                                      '.dataloop',
                                      'projects',
                                      self.project.name,
                                      'datasets',
                                      self.name)
        else:
            local_path = os.path.join(os.path.expanduser('~'),
                                      '.dataloop',
                                      'datasets',
                                      '%s_%s' % (self.name, self.id))
        return local_path

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

    def clone(self, clone_name, filters=None, with_items_annotations=True, with_metadata=True,
              with_task_annotations_status=True):
        """
        Clone dataset

        :param clone_name: new dataset name
        :param filters: Filters entity or a query dict
        :param with_items_annotations:
        :param with_metadata:
        :param with_task_annotations_status:
        :return:
        """
        return self.datasets.clone(dataset_id=self.id,
                                   filters=filters,
                                   clone_name=clone_name,
                                   with_metadata=with_metadata,
                                   with_items_annotations=with_items_annotations,
                                   with_task_annotations_status=with_task_annotations_status)

    def download_annotations(self,
                             local_path=None,
                             filters=None,
                             annotation_options=None,
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             remote_path=None,
                             num_workers=32):

        return self.datasets.download_annotations(dataset=self,
                                                  local_path=local_path,
                                                  overwrite=overwrite,
                                                  filters=filters,
                                                  annotation_options=annotation_options,
                                                  thickness=thickness,
                                                  with_text=with_text,
                                                  remote_path=remote_path,
                                                  num_workers=num_workers)

    def checkout(self):
        """
        Checkout the dataset

        :return:
        """
        self.datasets.checkout(dataset=self)

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

    def download(
            self,
            filters=None,
            local_path=None,
            file_types=None,
            annotation_options=None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            without_relative_path=None
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param local_path: local folder or filename to save to.
        :param filters: Filters entity or a dictionary containing filters parameters
        :param to_items_folder: Create 'items' folder and download items to it
        :param overwrite: optional - default = False
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param with_text: optional - add text to annotations, default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param without_relative_path: string - remote path - download items without the relative path from platform
        :return: Output (list)
        """
        return self.items.download(filters=filters,
                                   local_path=local_path,
                                   file_types=file_types,
                                   annotation_options=annotation_options,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   thickness=thickness,
                                   with_text=with_text,
                                   without_relative_path=without_relative_path)

    def delete_labels(self, label_names):
        """
        Delete labels from dataset's ontologies

        :param label_names: label object/ label name / list of label objects / list of label names
        :return:
        """
        for recipe in self.recipes.list():
            for ontology in recipe.ontologies.list():
                ontology.delete_labels(label_names=label_names)
        self._labels = None
