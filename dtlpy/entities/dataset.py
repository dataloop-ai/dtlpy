from collections import namedtuple
import traceback
import logging
import attr
import os

from .. import repositories, entities, services, exceptions
from .annotation import ViewAnnotationOptions, AnnotationType

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
    directoryTree = attr.ib(repr=False)
    export = attr.ib(repr=False)

    # name change when to_json
    created_at = attr.ib()
    items_url = attr.ib(repr=False)
    readable_type = attr.ib(repr=False)
    access_level = attr.ib(repr=False)
    driver = attr.ib(repr=False)
    _readonly = attr.ib(repr=False)

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
    def _protected_from_json(project: entities.Project,
                             _json: dict,
                             client_api: services.ApiClient,
                             datasets=None,
                             is_fetched=True):
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
    def from_json(cls,
                  project: entities.Project,
                  _json: dict,
                  client_api: services.ApiClient,
                  datasets=None,
                  is_fetched=True):
        """
        Build a Dataset entity object from a json

        :param is_fetched: is Entity fetched from Platform
        :param _json: _json response from host
        :param project: dataset's project
        :param datasets: Datasets repository
        :param client_api: client_api
        :return: Dataset object
        """
        projects = _json.get('projects', None)
        if project is not None and projects is not None:
            if project.id not in projects:
                logger.warning('Dataset has been fetched from a project that is not in it projects list')
                project = None

        inst = cls(metadata=_json.get('metadata', None),
                   directoryTree=_json.get('directoryTree', None),
                   readable_type=_json.get('readableType', None),
                   access_level=_json.get('accessLevel', None),
                   created_at=_json.get('createdAt', None),
                   itemsCount=_json.get('itemsCount', None),
                   annotated=_json.get('annotated', None),
                   readonly=_json.get('readonly', None),
                   projects=projects,
                   creator=_json.get('creator', None),
                   items_url=_json.get('items', None),
                   export=_json.get('export', None),
                   driver=_json.get('driver', None),
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
                                                              attr.fields(Dataset)._readonly,
                                                              attr.fields(Dataset)._datasets,
                                                              attr.fields(Dataset)._repositories,
                                                              attr.fields(Dataset)._ontology_ids,
                                                              attr.fields(Dataset)._labels,
                                                              attr.fields(Dataset)._directory_tree,
                                                              attr.fields(Dataset)._instance_map,
                                                              attr.fields(Dataset).access_level,
                                                              attr.fields(Dataset).readable_type,
                                                              attr.fields(Dataset).created_at,
                                                              attr.fields(Dataset).items_url))
        _json.update({'items': self.items_url})
        _json['readableType'] = self.readable_type
        _json['createdAt'] = self.created_at
        _json['accessLevel'] = self.access_level
        _json['readonly'] = self._readonly
        return _json

    @property
    def labels(self):
        if self._labels is None:
            self._labels = self.recipes.list()[0].ontologies.list()[0].labels
        return self._labels

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, state):
        raise exceptions.PlatformException(
            error='400',
            message='Cannot set attribute readonly. Please use "set_readonly({})" method'.format(state))

    @property
    def labels_flat_dict(self):
        flatten_dict = dict()

        def add_to_dict(tag: str, father: entities.Label):
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
    def instance_map(self, value: dict):
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
                          field_names=['items', 'recipes', 'datasets', 'assignments', 'tasks', 'annotations',
                                       'ontologies'])
        if self._project is None:
            datasets = repositories.Datasets(client_api=self._client_api, project=self._project)
        else:
            datasets = self._project.datasets

        r = reps(items=repositories.Items(client_api=self._client_api, dataset=self, datasets=datasets),
                 recipes=repositories.Recipes(client_api=self._client_api, dataset=self),
                 assignments=repositories.Assignments(project=self._project, client_api=self._client_api, dataset=self),
                 tasks=repositories.Tasks(client_api=self._client_api, project=self._project, dataset=self),
                 annotations=repositories.Annotations(client_api=self._client_api, dataset=self),
                 datasets=datasets,
                 ontologies=repositories.Ontologies(client_api=self._client_api, dataset=self))
        return r

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

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
            local_path = os.path.join(services.service_defaults.DATALOOP_PATH,
                                      'projects',
                                      self.project.name,
                                      'datasets',
                                      self.name)
        else:
            local_path = os.path.join(services.service_defaults.DATALOOP_PATH,
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

    def switch_recipe(self, recipe_id=None, recipe=None):
        """
        Switch the recipe that linked to the dataset with the given one

        :param: recipe_id
        :param: recipe
        :return:
        """
        if recipe is None and recipe_id is None:
            raise exceptions.PlatformException('400', 'Must provide recipe or recipe_id')
        if recipe_id is None:
            if not isinstance(recipe, entities.Recipe):
                raise exceptions.PlatformException('400', 'Recipe must me entities.Recipe type')
            else:
                recipe_id = recipe.id

        # add recipe id to dataset metadata
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        if 'recipes' not in self.metadata['system']:
            self.metadata['system']['recipes'] = list()
        self.metadata['system']['recipes'] = [recipe_id]
        self.update(system_metadata=True)

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

    def set_readonly(self, state: bool):
        """
        Set dataset readonly mode
        :param state:
        :return:
        """
        if not isinstance(state, bool):
            raise exceptions.PlatformException(
                error='400',
                message='Argument "state" must be bool. input type: {}'.format(type(state)))
        return self.datasets.set_readonly(dataset=self, state=state)

    def clone(self, clone_name, filters=None, with_items_annotations=True, with_metadata=True,
              with_task_annotations_status=True):
        """
        Clone dataset

        :param clone_name: new dataset name
        :param filters: Filters entity or a query dict
        :param with_items_annotations: clone all item's annotations
        :param with_metadata: clone metadata
        :param with_task_annotations_status: clone task annotations status
        :return:
        """
        return self.datasets.clone(dataset_id=self.id,
                                   filters=filters,
                                   clone_name=clone_name,
                                   with_metadata=with_metadata,
                                   with_items_annotations=with_items_annotations,
                                   with_task_annotations_status=with_task_annotations_status)

    def sync(self):
        """
        Sync dataset with external storage

        :return:
        """
        return self.datasets.sync(dataset_id=self.id)

    def download_annotations(self,
                             local_path=None,
                             filters=None,
                             annotation_options: ViewAnnotationOptions = None,
                             annotation_filters=None,
                             annotation_filter_type: AnnotationType = None,
                             annotation_filter_label=None,
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             remote_path=None):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param local_path: local folder or filename to save to.
        :param filters: Filters entity or a dictionary containing filters parameters
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param annotation_filters: Filters entity to filter annotations for download
        :param annotation_filter_type: DEPRECATED - list (dl.AnnotationType) of annotation types when downloading annotation, not relevant for JSON option
        :param annotation_filter_label: DEPRECATED - list of labels types when downloading annotation, not relevant for JSON option
        :param overwrite: optional - default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param remote_path: DEPRECATED and ignored. use filters
        :num_workers:
        :return: `List` of local_path per each downloaded item
        """

        return self.datasets.download_annotations(
            dataset=self,
            local_path=local_path,
            overwrite=overwrite,
            filters=filters,
            annotation_options=annotation_options,
            annotation_filters=annotation_filters,
            annotation_filter_type=annotation_filter_type,  # to deprecate - use "annotation_filters"
            annotation_filter_label=annotation_filter_label,  # to deprecate - use "annotation_filters"
            thickness=thickness,
            with_text=with_text,
            remote_path=remote_path)

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
                                         label=label,
                                         update_ontology=True)

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
        added_labels = ontology.add_labels(label_list=label_list, update_ontology=True)

        return added_labels

    def update_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                     recipe_id=None, ontology_id=None, upsert=False):
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
        :param upsert if True will add in case it does not existing
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
        added_label = ontology.update_label(label_name=label_name,
                                            color=color,
                                            children=children,
                                            attributes=attributes,
                                            display_label=display_label,
                                            label=label,
                                            update_ontology=True,
                                            upsert=upsert)

        return added_label

    def update_labels(self, label_list, ontology_id=None, recipe_id=None, upsert=False):
        """
        Add labels to dataset

        :param label_list:
        :param recipe_id: optional
        :param ontology_id: optional
        :param upsert if True will add in case it does not existing
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
        added_labels = ontology.update_labels(label_list=label_list, update_ontology=True, upsert=upsert)

        return added_labels

    def download(
            self,
            filters=None,
            local_path=None,
            file_types=None,
            annotation_options: ViewAnnotationOptions = None,
            annotation_filter_type: AnnotationType = None,
            annotation_filter_label=None,
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

        :param filters: Filters entity or a dictionary containing filters parameters
        :param local_path: local folder or filename to save to.
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param annotation_filter_type: list (dl.AnnotationType) of annotation types when downloading annotation,
                                                                                        not relevant for JSON option
        :param annotation_filter_label: list of labels types when downloading annotation, not relevant for JSON option
        :param overwrite: optional - default = False
        :param to_items_folder: Create 'items' folder and download items to it
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param without_relative_path: string - remote path - download items without the relative path from platform
        :return: `List` of local_path per each downloaded item
        """
        return self.items.download(filters=filters,
                                   local_path=local_path,
                                   file_types=file_types,
                                   annotation_options=annotation_options,
                                   annotation_filter_type=annotation_filter_type,
                                   annotation_filter_label=annotation_filter_label,
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

    def download_partition(self, partition, local_path=None, filters=None):
        """
        Download a specific partition of the dataset to local_path

        This function is commonly used with dl.ModelAdapter which implements thc convert to specific model structure

        :param partition: `dl.SnapshotPartitionType` name of the partition
        :param local_path: local path directory to download the data
        :param filters:  dl.entities.Filters to add the specific partitions constraint to
        :return List `str` of the new downloaded path of each item
        """
        if local_path is None:
            local_path = os.getcwd()
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.ITEM)

        if partition == 'all':  # TODO: should it be all or None (all != list(SnapshotPartitions) )
            logger.info("downloading all items - even without partitions")
        else:
            filters.add(field='metadata.system.snapshotPartition', values=partition)

        return self.items.download(filters=filters,
                                   local_path=local_path,
                                   annotation_options=entities.ViewAnnotationOptions.JSON)

    def set_partition(self, partition, filters=None):
        """
        Updates all items returned by filters in the dataset to specific partition

        :param partition:  `dl.entities.SnapshotPartitionType` to set to
        :param filters:  dl.entities.Filters to add the specific partitions constraint to
        :return:  dl.PagedEntities
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.ITEM)
        # TODO: How to preform update using the Filter - where do i set the field - docstring should state dict key-val while arg name is only values....
        return self.items.update(filters=filters, system_update_values={'snapshotPartition': partition},
                                 system_metadata=True)

    def get_partitions(self, partitions, filters=None):
        """
        Returns PagedEntity of items from one or more partitions

        :param partitions: `dl.entities.SnapshotPartitionType` or a list. Name of the partitions
        :param filters:  dl.Filters to add the specific partitions constraint to
        :return: `dl.PagedEntities` of `dl.Item`  preforms items.list()
        """
        # Question: do we have to give a partition? how do we get in case no partiton is defined?
        if isinstance(partitions, str):
            partitions = [partitions]
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.ITEM)

        if partitions == 'all':
            logger.info("downloading all items - even without partitions")
        else:
            filters.add(field='metadata.system.snapshotPartition',
                        values=partitions,
                        operator=entities.FiltersOperations.IN)
        return self.items.list(filters=filters)
