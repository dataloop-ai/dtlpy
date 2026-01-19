from collections import namedtuple
import traceback
import logging
from enum import Enum

import attr
import os

from .. import repositories, entities, services, exceptions
from ..services.api_client import ApiClient
from .annotation import ViewAnnotationOptions, AnnotationType, ExportVersion

logger = logging.getLogger(name='dtlpy')


class IndexDriver(str, Enum):
    V1 = "v1"
    V2 = "v2"


class ExportType(str, Enum):
    JSON = "json"
    ZIP = "zip"

class OutputExportType(str, Enum):
    JSON = "json"
    ZIP = "zip"
    FOLDERS = "folders"

class ExpirationOptions:
    """
    ExpirationOptions object
    """

    def __init__(self, item_max_days: int = None):
        """
        :param item_max_days: int. items in dataset will be auto delete after this number id days
        """
        self.item_max_days = item_max_days

    def to_json(self):
        _json = dict()
        if self.item_max_days is not None:
            _json["itemMaxDays"] = self.item_max_days
        return _json

    @classmethod
    def from_json(cls, _json: dict):
        item_max_days = _json.get('itemMaxDays', None)
        if item_max_days:
            return cls(item_max_days=item_max_days)
        return None


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
    items_count = attr.ib()
    metadata = attr.ib(repr=False)
    directoryTree = attr.ib(repr=False)
    expiration_options = attr.ib()
    index_driver = attr.ib()
    enable_sync_with_cloned = attr.ib(repr=False)

    # name change when to_json
    created_at = attr.ib()
    updated_at = attr.ib()
    updated_by = attr.ib()
    items_url = attr.ib(repr=False)
    readable_type = attr.ib(repr=False)
    access_level = attr.ib(repr=False)
    driver = attr.ib(repr=False)
    src_dataset = attr.ib(repr=False)
    _readonly = attr.ib(repr=False)
    annotations_count = attr.ib()

    # api
    _client_api = attr.ib(type=ApiClient, repr=False)

    # syncing status
    is_syncing = attr.ib(default=False, repr=False)

    # entities
    _project = attr.ib(default=None, repr=False)

    # repositories
    _datasets = attr.ib(repr=False, default=None)
    _repositories = attr.ib(repr=False)

    # defaults
    _ontology_ids = attr.ib(default=None, repr=False)
    _labels = attr.ib(default=None, repr=False)
    _directory_tree = attr.ib(default=None, repr=False)
    _recipe = attr.ib(default=None, repr=False)
    _ontology = attr.ib(default=None, repr=False)

    @property
    def itemsCount(self):
        return self.items_count

    @staticmethod
    def _protected_from_json(project: entities.Project,
                             _json: dict,
                             client_api: ApiClient,
                             datasets=None,
                             is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param project: dataset's project
        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param datasets: Datasets repository
        :param is_fetched: is Entity fetched from Platform
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
                  client_api: ApiClient,
                  datasets=None,
                  is_fetched=True):
        """
        Build a Dataset entity object from a json

        :param project: dataset's project
        :param dict _json: _json response from host
        :param client_api: ApiClient entity
        :param datasets: Datasets repository
        :param bool is_fetched: is Entity fetched from Platform
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset
        """
        projects = _json.get('projects', None)
        if project is not None and projects is not None:
            if project.id not in projects:
                logger.warning('Dataset has been fetched from a project that is not in it projects list')
                project = None

        expiration_options = _json.get('expirationOptions', None)
        if expiration_options:
            expiration_options = ExpirationOptions.from_json(expiration_options)
        inst = cls(metadata=_json.get('metadata', None),
                   directoryTree=_json.get('directoryTree', None),
                   readable_type=_json.get('readableType', None),
                   access_level=_json.get('accessLevel', None),
                   created_at=_json.get('createdAt', None),
                   updated_at=_json.get('updatedAt', None),
                   updated_by=_json.get('updatedBy', None),
                   annotations_count=_json.get("annotationsCount", None),
                   items_count=_json.get('itemsCount', None),
                   annotated=_json.get('annotated', None),
                   readonly=_json.get('readonly', None),
                   projects=projects,
                   creator=_json.get('creator', None),
                   items_url=_json.get('items', None),
                   driver=_json.get('driver', None),
                   name=_json.get('name', None),
                   url=_json.get('url', None),
                   id=_json.get('id', None),
                   datasets=datasets,
                   client_api=client_api,
                   project=project,
                   expiration_options=expiration_options,
                   index_driver=_json.get('indexDriver', None),
                   enable_sync_with_cloned=_json.get('enableSyncWithCloned', None),
                   is_syncing=_json.get('isSyncing', False),
                   src_dataset=_json.get('srcDataset', None))
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Dataset)._client_api,
                                                              attr.fields(Dataset)._project,
                                                              attr.fields(Dataset)._readonly,
                                                              attr.fields(Dataset)._datasets,
                                                              attr.fields(Dataset)._repositories,
                                                              attr.fields(Dataset)._ontology_ids,
                                                              attr.fields(Dataset)._labels,
                                                              attr.fields(Dataset)._recipe,
                                                              attr.fields(Dataset)._ontology,
                                                              attr.fields(Dataset)._directory_tree,
                                                              attr.fields(Dataset).access_level,
                                                              attr.fields(Dataset).readable_type,
                                                              attr.fields(Dataset).created_at,
                                                              attr.fields(Dataset).updated_at,
                                                              attr.fields(Dataset).updated_by,
                                                              attr.fields(Dataset).annotations_count,
                                                              attr.fields(Dataset).items_url,
                                                              attr.fields(Dataset).expiration_options,
                                                              attr.fields(Dataset).items_count,
                                                              attr.fields(Dataset).index_driver,
                                                              attr.fields(Dataset).enable_sync_with_cloned,
                                                              attr.fields(Dataset).is_syncing,
                                                              attr.fields(Dataset).src_dataset,
                                                              ))
        _json.update({'items': self.items_url})
        _json['readableType'] = self.readable_type
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['updatedBy'] = self.updated_by
        _json['annotationsCount'] = self.annotations_count
        _json['accessLevel'] = self.access_level
        _json['readonly'] = self._readonly
        _json['itemsCount'] = self.items_count
        _json['indexDriver'] = self.index_driver
        if self.expiration_options and self.expiration_options.to_json():
            _json['expirationOptions'] = self.expiration_options.to_json()
        if self.enable_sync_with_cloned is not None:
            _json['enableSyncWithCloned'] = self.enable_sync_with_cloned
        _json['isSyncing'] = self.is_syncing
        if self.src_dataset is not None:
            _json['srcDataset'] = self.src_dataset
        return _json

    @property
    def labels(self):
        if self._labels is None:
            self._labels = self._get_ontology().labels
        return self._labels

    @property
    def readonly(self):
        return self._readonly

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/datasets/{}/items".format(self.project.id, self.id))

    @readonly.setter
    def readonly(self, state):
        import warnings
        warnings.warn("`readonly` flag on dataset is deprecated, doing nothing.", DeprecationWarning)

    @property
    def labels_flat_dict(self):
        return self._get_ontology().labels_flat_dict

    @property
    def instance_map(self) -> dict:
        return self._get_ontology().instance_map

    @instance_map.setter
    def instance_map(self, value: dict):
        """
        instance mapping for creating instance mask

        :param value: dictionary {label: map_id}
        """
        if not isinstance(value, dict):
            raise ValueError('input must be a dictionary of {label_name: instance_id}')
        self._get_ontology().instance_map = value

    @property
    def ontology_ids(self):
        if self._ontology_ids is None:
            self._ontology_ids = list()
            if self.metadata is not None and 'system' in self.metadata and 'recipes' in self.metadata['system']:
                recipe_ids = self.get_recipe_ids()
                for rec_id in recipe_ids:
                    recipe = self.recipes.get(recipe_id=rec_id)
                    self._ontology_ids += recipe.ontology_ids
        return self._ontology_ids


    @property
    def project_id(self):
        _project_id = None
        if self.projects is not None and len(self.projects) > 0:
            _project_id = self.projects[0]
        return _project_id

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['items', 'recipes', 'datasets', 'assignments', 'tasks', 'annotations',
                                       'ontologies', 'features', 'feature_sets', 'settings', 'schema', 'collections'])
        _project_id = None
        if self._project is None:
            datasets = repositories.Datasets(client_api=self._client_api, project=self._project)
            if self.projects is not None and len(self.projects) > 0:
                _project_id = self.projects[0]
        else:
            datasets = self._project.datasets
            _project_id = self._project.id
        return reps(
            items=repositories.Items(client_api=self._client_api, dataset=self, datasets=datasets),
            recipes=repositories.Recipes(client_api=self._client_api, dataset=self),
            assignments=repositories.Assignments(project=self._project, client_api=self._client_api, dataset=self),
            tasks=repositories.Tasks(client_api=self._client_api, project=self._project, dataset=self),
            annotations=repositories.Annotations(client_api=self._client_api, dataset=self),
            datasets=datasets,
            ontologies=repositories.Ontologies(client_api=self._client_api, dataset=self),
            features=repositories.Features(client_api=self._client_api, project=self._project, dataset=self),
            feature_sets=repositories.FeatureSets(client_api=self._client_api, project=self._project, project_id=_project_id, dataset=self),
            settings=repositories.Settings(client_api=self._client_api, dataset=self),
            schema=repositories.Schema(client_api=self._client_api, dataset=self),
            collections=repositories.Collections(client_api=self._client_api, dataset=self)
        )

    @property
    def settings(self):
        assert isinstance(self._repositories.settings, repositories.Settings)
        return self._repositories.settings

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
    def features(self):
        assert isinstance(self._repositories.features, repositories.Features)
        return self._repositories.features

    @property
    def feature_sets(self):
        assert isinstance(self._repositories.feature_sets, repositories.FeatureSets)
        return self._repositories.feature_sets

    @property
    def collections(self):
        assert isinstance(self._repositories.collections, repositories.Collections)
        return self._repositories.collections

    @property
    def schema(self):
        assert isinstance(self._repositories.schema, repositories.Schema)
        return self._repositories.schema

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

    def _get_recipe(self):
        recipes = self.recipes.list()
        if len(recipes) > 0:
            return recipes[0]
        else:
            raise exceptions.PlatformException('404', 'Dataset {} has no recipe'.format(self.name))

    def _get_ontology(self):
        if self._ontology is None:
            ontologies = self._get_recipe().ontologies.list()
            if len(ontologies) > 0:
                self._ontology = ontologies[0]
            else:
                raise exceptions.PlatformException('404', 'Dataset {} has no ontology'.format(self.name))
        return self._ontology

    @staticmethod
    def serialize_labels(labels_dict):
        """
        Convert hex color format to rgb

        :param dict labels_dict: dict of labels
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
        :rtype: list
        """
        return self.metadata['system']['recipes']

    def switch_recipe(self, recipe_id=None, recipe=None):
        """
        Switch the recipe that linked to the dataset with the given one

        :param str recipe_id: recipe id
        :param dtlpy.entities.recipe.Recipe recipe: recipe entity

        **Example**:

        .. code-block:: python

            dataset.switch_recipe(recipe_id='recipe_id')
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

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param bool sure: are you sure you want to delete?
        :param bool really: really really?
        :return: True is success
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = dataset.delete(sure=True, really=True)
        """
        return self.datasets.delete(dataset_id=self.id,
                                    sure=sure,
                                    really=really)

    def update(self, system_metadata=False):
        """
        Update dataset field

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param bool system_metadata: bool - True, if you want to change metadata system
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = dataset.update()
        """
        return self.datasets.update(dataset=self,
                                    system_metadata=system_metadata)

    def unlock(self):
        """
        Unlock dataset

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = dataset.unlock()
        """
        return self.datasets.unlock(dataset=self)

    def set_readonly(self, state: bool):
        """
        Set dataset readonly mode

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param bool state: state

        **Example**:

        .. code-block:: python

            dataset.set_readonly(state=True)
        """
        import warnings
        warnings.warn("`readonly` flag on dataset is deprecated, doing nothing.", DeprecationWarning)

    def clone(self,
              clone_name=None,
              filters=None,
              with_items_annotations=True,
              with_metadata=True,
              with_task_annotations_status=True,
              dst_dataset_id=None,
              target_directory=None,
              ):
        """
        Clone dataset

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str clone_name: new dataset name
        :param dtlpy.entities.filters.Filters filters: Filters entity or a query dict
        :param bool with_items_annotations: clone all item's annotations
        :param bool with_metadata: clone metadata
        :param bool with_task_annotations_status: clone task annotations status
        :param str dst_dataset_id: destination dataset id
        :param str target_directory: target directory
        :return: dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = dataset.clone(dataset_id='dataset_id',
                          clone_name='dataset_clone_name',
                          with_metadata=True,
                          with_items_annotations=False,
                          with_task_annotations_status=False)
        """
        return self.datasets.clone(dataset_id=self.id,
                                   filters=filters,
                                   clone_name=clone_name,
                                   with_metadata=with_metadata,
                                   with_items_annotations=with_items_annotations,
                                   with_task_annotations_status=with_task_annotations_status,
                                   dst_dataset_id=dst_dataset_id,
                                   target_directory=target_directory)

    def sync(self, wait=True):
        """
        Sync dataset with external storage

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param bool wait: wait for the command to finish
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dataset.sync()
        """
        return self.datasets.sync(dataset_id=self.id, wait=wait)

    def download_annotations(self,
                             local_path=None,
                             filters=None,
                             annotation_options: ViewAnnotationOptions = None,
                             annotation_filters=None,
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             remote_path=None,
                             include_annotations_in_output=True,
                             export_png_files=False,
                             filter_output_annotations=False,
                             alpha=1,
                             export_version=ExportVersion.V1,
                             dataset_lock=False,
                             lock_timeout_sec=None,
                             export_summary=False,
                            ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str local_path: local folder or filename to save to.
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param list(dtlpy.entities.annotation.ViewAnnotationOptions) annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False
        :param bool dataset_lock: optional - default = False
        :param bool export_summary: optional - default = False
        :param int lock_timeout_sec: optional
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param str remote_path: DEPRECATED and ignored
        :param bool include_annotations_in_output: default - False , if export should contain annotations
        :param bool export_png_files: default - if True, semantic annotations should be exported as png files
        :param bool filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return: local_path of the directory where all the downloaded item
        :rtype: str

        **Example**:

        .. code-block:: python

            local_path = dataset.download_annotations(dataset='dataset_entity',
                                         local_path='local_path',
                                         annotation_options=[dl.ViewAnnotationOptions.JSON, dl.ViewAnnotationOptions.MASK],
                                         overwrite=False,
                                         thickness=1,
                                         with_text=False,
                                         alpha=1,
                                         dataset_lock=False,
                                         lock_timeout_sec=300,
                                         export_summary=False
                                        )
        """

        return self.datasets.download_annotations(
            dataset=self,
            local_path=local_path,
            overwrite=overwrite,
            filters=filters,
            annotation_options=annotation_options,
            annotation_filters=annotation_filters,
            thickness=thickness,
            with_text=with_text,
            remote_path=remote_path,
            include_annotations_in_output=include_annotations_in_output,
            export_png_files=export_png_files,
            filter_output_annotations=filter_output_annotations,
            alpha=alpha,
            export_version=export_version,
            dataset_lock=dataset_lock,
            lock_timeout_sec=lock_timeout_sec,
            export_summary=export_summary        
        )

    def export(self,
               local_path=None,
               filters=None,
               annotation_filters=None,
               feature_vector_filters=None,
               include_feature_vectors: bool = False,
               include_annotations: bool = False,
               export_type: ExportType = ExportType.JSON,
               timeout: int = 0,
               dataset_lock: bool = False,
               lock_timeout_sec: int = None,
               export_summary: bool = False,
               output_export_type: OutputExportType = None):
        """
        Export dataset items and annotations.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset, dataset_name, dataset_id.

        :param str local_path: The local path to save the exported dataset
        :param Union[dict, dtlpy.entities.filters.Filters] filters: Filters entity or a query dictionary
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity
        :param dtlpy.entities.filters.Filters feature_vector_filters: Filters entity
        :param bool include_feature_vectors: Include item feature vectors in the export
        :param bool include_annotations: Include item annotations in the export
        :param bool dataset_lock: Make dataset readonly during the export
        :param bool export_summary: Download dataset export summary
        :param int lock_timeout_sec: Timeout for locking the dataset during export in seconds
        :param entities.ExportType export_type: Type of export ('json' or 'zip')
        :param entities.OutputExportType output_export_type: Output format ('json', 'zip', or 'folders'). If None, defaults to 'json'
        :param int timeout: Maximum time in seconds to wait for the export to complete
        :return: Exported item
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            export_item = dataset.export(filters=filters,
                                         include_feature_vectors=True,
                                         include_annotations=True,
                                         export_type=dl.ExportType.JSON,
                                         output_export_type=dl.OutputExportType.JSON)
        """

        return self.datasets.export(dataset=self,
                                    local_path=local_path,
                                    filters=filters,
                                    annotation_filters=annotation_filters,
                                    feature_vector_filters=feature_vector_filters,
                                    include_feature_vectors=include_feature_vectors,
                                    include_annotations=include_annotations,
                                    export_type=export_type,
                                    timeout=timeout,
                                    dataset_lock=dataset_lock,
                                    lock_timeout_sec=lock_timeout_sec,
                                    export_summary=export_summary,
                                    output_export_type=output_export_type)

    def upload_annotations(self,
                           local_path,
                           filters=None,
                           clean=False,
                           remote_root_path='/',
                           export_version=ExportVersion.V1
                           ):
        """
        Upload annotations to dataset.

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param str local_path: str - local folder where the annotations files is.
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param bool clean: bool - if True it remove the old annotations
        :param str remote_root_path: str - the remote root path to match remote and local items
        :param str export_version:  `V2` - exported items will have original extension in filename, `V1` - no original extension in filenames

        For example, if the item filepath is a/b/item and remote_root_path is /a the start folder will be b instead of a

        **Example**:

        .. code-block:: python

            dataset.upload_annotations(dataset='dataset_entity',
                                     local_path='local_path',
                                     clean=False,
                                     export_version=dl.ExportVersion.V1
                                     )
        """

        return self.datasets.upload_annotations(
            dataset=self,
            local_path=local_path,
            filters=filters,
            clean=clean,
            remote_root_path=remote_root_path,
            export_version=export_version
        )

    def checkout(self):
        """
        Checkout the dataset

        """
        self.datasets.checkout(dataset=self)

    def open_in_web(self):
        """
        Open the dataset in web platform

        """
        self._client_api._open_in_web(url=self.platform_url)

    def add_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                  recipe_id=None, ontology_id=None, icon_path=None):
        """
        Add single label to dataset

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param str label_name: str - label name
        :param tuple color: RGB color of the annotation, e.g (255,0,0) or '#ff0000' for red
        :param children: children (sub labels). list of sub labels of this current label, each value is either dict or dl.Label
        :param list attributes: add attributes to the labels
        :param str display_label: name that display label
        :param dtlpy.entities.label.Label label: label object
        :param str recipe_id: optional recipe id
        :param str ontology_id: optional ontology id
        :param str icon_path: path to image to be display on label
        :return: label entity
        :rtype: dtlpy.entities.label.Label

        **Example**:

        .. code-block:: python

            dataset.add_label(label_name='person', color=(34, 6, 231), attributes=['big', 'small'])
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)
        # ontology._dataset = self

        # add label
        added_label = ontology.add_label(label_name=label_name,
                                         color=color,
                                         children=children,
                                         attributes=attributes,
                                         display_label=display_label,
                                         label=label,
                                         update_ontology=True,
                                         icon_path=icon_path)

        return added_label

    def add_labels(self, label_list, ontology_id=None, recipe_id=None):
        """
        Add labels to dataset

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param list label_list: a list of labels to add to the dataset's ontology. each value should be a dict, dl.Label or a string
        :param str ontology_id: optional ontology id
        :param str recipe_id: optional recipe id
        :return: label entities

        **Example**:

        .. code-block:: python

            dataset.add_labels(label_list=label_list)
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)

        # add labels to ontology
        added_labels = ontology.add_labels(label_list=label_list, update_ontology=True)

        return added_labels

    def update_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                     recipe_id=None, ontology_id=None, upsert=False, icon_path=None):
        """
        Add single label to dataset

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param str label_name: str - label name
        :param tuple color: color
        :param children: children (sub labels)
        :param list attributes: add attributes to the labels
        :param str display_label: name that display label
        :param dtlpy.entities.label.Label label: label
        :param str recipe_id: optional recipe id
        :param str ontology_id: optional ontology id
        :param str icon_path: path to image to be display on label

        :return: label entity
        :rtype: dtlpy.entities.label.Label

        **Example**:

        .. code-block:: python

            dataset.update_label(label_name='person', color=(34, 6, 231), attributes=['big', 'small'])
        """
        # get recipe

        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)

        # add label
        added_label = ontology.update_label(label_name=label_name,
                                            color=color,
                                            children=children,
                                            attributes=attributes,
                                            display_label=display_label,
                                            label=label,
                                            update_ontology=True,
                                            upsert=upsert,
                                            icon_path=icon_path)

        return added_label

    def update_labels(self, label_list, ontology_id=None, recipe_id=None, upsert=False):
        """
        Add labels to dataset

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param list label_list: label list
        :param str ontology_id: optional ontology id
        :param str recipe_id: optional recipe id
        :param bool upsert: if True will add in case it does not existing

        :return: label entities
        :rtype: dtlpy.entities.label.Label

        **Example**:

        .. code-block:: python

            dataset.update_labels(label_list=label_list)
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
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
            annotation_filters=None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            without_relative_path=None,
            alpha=1,
            export_version=ExportVersion.V1,
            dataset_lock=False,
            lock_timeout_sec=None,
            export_summary=False,
            raise_on_error=False
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param str local_path: local folder or filename to save to.
        :param list file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param list annotation_options: type of download annotations: list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False to overwrite the existing files
        :param bool dataset_lock: optional - default = False to make dataset readonly during the download
        :param bool export_summary: optional - default = False to get the symmary of the export
        :param int lock_timeout_sec: optional - Set lock timeout for the export
        :param bool to_items_folder: Create 'items' folder and download items to it
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param bool without_relative_path: bool - download items without the relative path from platform
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  `V2` - exported items will have original extension in filename, `V1` - no original extension in filenames
        :param bool raise_on_error: raise an exception if an error occurs
        :return: `List` of local_path per each downloaded item

        **Example**:

        .. code-block:: python

            dataset.download(local_path='local_path',
                             annotation_options=[dl.ViewAnnotationOptions.JSON, dl.ViewAnnotationOptions.MASK],
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             alpha=1,
                             dataset_lock=False,      
                             lock_timeout_sec=300,
                             export_summary=False                      
                             )
        """
        return self.items.download(filters=filters,
                                   local_path=local_path,
                                   file_types=file_types,
                                   annotation_options=annotation_options,
                                   annotation_filters=annotation_filters,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   thickness=thickness,
                                   with_text=with_text,
                                   without_relative_path=without_relative_path,
                                   alpha=alpha,
                                   export_version=export_version,
                                   dataset_lock=dataset_lock,
                                   lock_timeout_sec=lock_timeout_sec,
                                   export_summary=export_summary,
                                   raise_on_error=raise_on_error
                                   )

    def download_folder(
            self,
            folder_path,
            filters=None,
            local_path=None,
            file_types=None,
            annotation_options: ViewAnnotationOptions = None,
            annotation_filters=None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            without_relative_path=None,
            alpha=1,
            export_version=ExportVersion.V1,
            dataset_lock=False,
            lock_timeout_sec=None,
            export_summary=False,
            raise_on_error=False
    ):
        """
        Download dataset folder.
        Optional - also download annotation, mask, instance and image mask of the item

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str folder_path: the path of the folder that want to download
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param str local_path: local folder or filename to save to.
        :param list file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param list annotation_options: type of download annotations: list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False to overwrite the existing files
        :param bool dataset_lock: optional - default = False to make the dataset readonly during the download
        :param bool export_summary: optional - default = False to get the symmary of the export
        :param bool lock_timeout_sec: optional - Set lock timeout for the export
        :param bool to_items_folder: Create 'items' folder and download items to it
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param bool without_relative_path: bool - download items without the relative path from platform
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  `V2` - exported items will have original extension in filename, `V1` - no original extension in filenames
        :param bool raise_on_error: raise an exception if an error occurs
        :return: `List` of local_path per each downloaded item

        **Example**:

        .. code-block:: python

            dataset.download_folder(folder_path='folder_path'
                             local_path='local_path',
                             annotation_options=[dl.ViewAnnotationOptions.JSON, dl.ViewAnnotationOptions.MASK],
                             overwrite=False,
                             thickness=1,
                             with_text=False,
                             alpha=1,
                             save_locally=True,
                             dataset_lock=False
                             lock_timeout_sec=300,
                             export_summary=False
                             )
        """
        filters = self.datasets._bulid_folder_filter(folder_path=folder_path, filters=filters)
        return self.items.download(filters=filters,
                                   local_path=local_path,
                                   file_types=file_types,
                                   annotation_options=annotation_options,
                                   annotation_filters=annotation_filters,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   thickness=thickness,
                                   with_text=with_text,
                                   without_relative_path=without_relative_path,
                                   alpha=alpha,
                                   export_version=export_version,
                                   dataset_lock=dataset_lock,
                                   lock_timeout_sec=lock_timeout_sec,
                                    export_summary=export_summary,
                                    raise_on_error=raise_on_error
                                   )

    def delete_labels(self, label_names):
        """
        Delete labels from dataset's ontologies

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param label_names: label object/ label name / list of label objects / list of label names

        **Example**:

        .. code-block:: python

            dataset.delete_labels(label_names=['myLabel1', 'Mylabel2'])
        """
        for recipe in self.recipes.list():
            for ontology in recipe.ontologies.list():
                ontology.delete_labels(label_names=label_names)
        self._labels = None

    def update_attributes(self,
                          title: str,
                          key: str,
                          attribute_type,
                          recipe_id: str = None,
                          ontology_id: str = None,
                          scope: list = None,
                          optional: bool = None,
                          values: list = None,
                          attribute_range=None):
        """
        ADD a new attribute or update if exist

        :param str ontology_id: ontology_id
        :param str title: attribute title
        :param str key: the key of the attribute must br unique
        :param AttributesTypes attribute_type: dl.AttributesTypes your attribute type
        :param list scope: list of the labels or * for all labels
        :param bool optional: optional attribute
        :param list values: list of the attribute values ( for checkbox and radio button)
        :param dict or AttributesRange attribute_range: dl.AttributesRange object
        :return: true in success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.update_attributes(ontology_id='ontology_id',
                                      key='1',
                                      title='checkbox',
                                      attribute_type=dl.AttributesTypes.CHECKBOX,
                                      values=[1,2,3])
        """
        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)

        # add attribute to ontology
        attribute = ontology.update_attributes(
            title=title,
            key=key,
            attribute_type=attribute_type,
            scope=scope,
            optional=optional,
            values=values,
            attribute_range=attribute_range)

        return attribute

    def delete_attributes(self, keys: list,
                          recipe_id: str = None,
                          ontology_id: str = None):
        """
        Delete a bulk of attributes

        :param str recipe_id: recipe id
        :param str ontology_id: ontology id
        :param list keys: Keys of attributes to delete
        :return: True if success
        :rtype: bool
        """

        # get recipe
        if recipe_id is None:
            recipe_id = self.get_recipe_ids()[0]
        recipe = self.recipes.get(recipe_id=recipe_id)

        # get ontology
        if ontology_id is None:
            ontology_id = recipe.ontology_ids[0]
        ontology = recipe.ontologies.get(ontology_id=ontology_id)
        return ontology.delete_attributes(ontology_id=ontology.id, keys=keys)

    def split_ml_subsets(self,
                         items_query = None,
                         percentages: dict = None ):
        """
        Split dataset items into ML subsets.

        :param dl.Filters items_query: Filters object to select items.
        :param dict percentages: {'train': x, 'validation': y, 'test': z}.
        :return: True if the split operation was successful.
        :rtype: bool
        """
        return self.datasets.split_ml_subsets(dataset_id=self.id,
                                              items_query=items_query,
                                              ml_split_list=percentages)

    def assign_subset_to_items(self, subset: str, items_query=None) -> bool:
        """
        Assign a specific ML subset (train/validation/test) to items defined by the given filters.
        This will set the chosen subset to True and the others to None.

        :param dl.Filters items_query: Filters to select items
        :param str subset: 'train', 'validation', or 'test'
        :return: True if successful
        :rtype: bool
        """
   
        return self.datasets.bulk_update_ml_subset(dataset_id=self.id,
                                                   items_query=items_query,
                                                   subset=subset)

    def remove_subset_from_items(self, items_query= None,) -> bool:
        """
        Remove any ML subset assignment from items defined by the given filters.
        This sets train, validation, and test tags to None.

        :param dl.Filters items_query: Filters to select items
        :return: True if successful
        :rtype: bool
        """
        return self.datasets.bulk_update_ml_subset(dataset_id=self.id,
                                                   items_query=items_query,
                                                   subset=None,
                                                   deleteTag=True)

    def get_items_missing_ml_subset(self, filters = None) -> list:
        """
        Get the list of item IDs that are missing ML subset assignment.
        An item is considered missing ML subset if train, validation, and test tags are not True (all None).

        :param dl.Filters filters: optional filters to narrow down items. If None, will use a default filter for files.
        :return: list of item IDs
        :rtype: list
        """
        if filters is None:
            filters = entities.Filters()
        filters.add(field='metadata.system.tags.train', values=None)
        filters.add(field='metadata.system.tags.validation', values=None)
        filters.add(field='metadata.system.tags.test', values=None)
        missing_ids = []
        pages = self.items.list(filters=filters)
        for page in pages:
            for item in page:
                # item that pass filters means no subsets assigned
                missing_ids.append(item.id)
        return missing_ids
