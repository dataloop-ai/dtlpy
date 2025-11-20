import dataclasses
import threading
import tempfile
import datetime
import logging
import string
import shutil
import random
import base64
import copy
import time
import tqdm
import traceback
import sys
import io
import os
from itertools import chain
from PIL import Image
from functools import partial
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import attr
from collections.abc import MutableMapping
from typing import Optional
from .. import entities, utilities, repositories, exceptions
from ..services import service_defaults
from ..services.api_client import ApiClient

logger = logging.getLogger('ModelAdapter')

# Constants
PREDICT_EMBED_DEFAULT_SUBSET_LIMIT = 1000
PREDICT_EMBED_DEFAULT_TIMEOUT = 3600 * 24


class ModelConfigurations(MutableMapping):
    """
    Manages model configuration using composition with a backing dict.

    Uses MutableMapping to implement dict-like behavior without inheritance.
    This avoids duplication: if we inherited from dict, we'd have two dicts
    (one from inheritance, one from model_entity.configuration), leading to
    data inconsistency and maintenance issues.
    """

    def __init__(self, base_model_adapter):
        # Store reference to base_model_adapter dictionary
        self._backing_dict = {}

        if base_model_adapter is not None and base_model_adapter.model_entity is not None and base_model_adapter.model_entity.configuration is not None:
            self._backing_dict = base_model_adapter.model_entity.configuration
        if 'include_background' not in self._backing_dict:
            self._backing_dict['include_background'] = False
        self._base_model_adapter = base_model_adapter
        # Don't call _update_model_entity during initialization to avoid premature updates

    def _update_model_entity(self):
        if self._base_model_adapter is not None and self._base_model_adapter.model_entity is not None:
            self._base_model_adapter.model_entity.update(reload_services=False)

    def __ior__(self, other):
        self.update(other)
        return self

    # Required MutableMapping abstract methods
    def __getitem__(self, key):
        return self._backing_dict[key]

    def __setitem__(self, key, value):
        # Note: This method only updates the backing dict, not object attributes.
        # If you need to also update object attributes, be careful to avoid
        # infinite recursion by not calling __setattr__ from here.
        update = False
        if key not in self._backing_dict or self._backing_dict.get(key) != value:
            update = True
        self._backing_dict[key] = value
        if update:
            self._update_model_entity()

    def __delitem__(self, key):
        del self._backing_dict[key]

    def __iter__(self):
        return iter(self._backing_dict)

    def __len__(self):
        return len(self._backing_dict)

    def get(self, key, default=None):
        if key not in self._backing_dict:
            self.__setitem__(key, default)
        return self._backing_dict.get(key)

    def update(self, *args, **kwargs):
        # Check if there will be any modifications
        update_dict = dict(*args, **kwargs)
        has_changes = False
        for key, value in update_dict.items():
            if key not in self._backing_dict or self._backing_dict[key] != value:
                has_changes = True
                break
        self._backing_dict.update(*args, **kwargs)

        if has_changes:
            self._update_model_entity()

    def setdefault(self, key, default=None):
        if key not in self._backing_dict:
            self._backing_dict[key] = default
        return self._backing_dict[key]


@dataclasses.dataclass
class AdapterDefaults(ModelConfigurations):
    # for predict items, dataset, evaluate
    upload_annotations: bool = dataclasses.field(default=True)
    clean_annotations: bool = dataclasses.field(default=True)
    overwrite_annotations: bool = dataclasses.field(default=True)
    # for embeddings
    upload_features: bool = dataclasses.field(default=None)
    # for training
    root_path: str = dataclasses.field(default=None)
    data_path: str = dataclasses.field(default=None)
    output_path: str = dataclasses.field(default=None)

    def __init__(self, base_model_adapter=None):
        super().__init__(base_model_adapter)
        for f in dataclasses.fields(AdapterDefaults):
            # if the field exists in model_entity.configuration, use it
            # else set it from the attribute default value
            if super().get(f.name) is not None:
                super().__setattr__(f.name, super().get(f.name))
            else:
                super().__setitem__(f.name, f.default)

    def __setattr__(self, key, value):
        # Dataclass-like fields behave as attributes, so map to dict
        super().__setattr__(key, value)
        if not key.startswith("_"):
            super().__setitem__(key, value)

    def update(self, *args, **kwargs):
        for f in dataclasses.fields(AdapterDefaults):
            if f.name in kwargs:
                setattr(self, f.name, kwargs[f.name])
        super().update(*args, **kwargs)

    def resolve(self, key, *args):
        for arg in args:
            if arg is not None:
                super().__setitem__(key, arg)
                return arg
        return self.get(key, None)


class BaseModelAdapter(utilities.BaseServiceRunner):
    _client_api = attr.ib(type=ApiClient, repr=False)
    _feature_set_lock = threading.Lock()

    def __init__(self, model_entity: entities.Model = None):
        self.logger = logger
        # entities
        self._model_entity = None
        self._configuration = None
        self.adapter_defaults = None
        self.model = None
        self.bucket_path = None
        self._project = None
        self._feature_set = None
        # funcs
        self.item_to_batch_mapping = {'text': self._item_to_text, 'image': self._item_to_image}
        if model_entity is not None:
            self.load_from_model(model_entity=model_entity)
        logger.warning(
            "in case of a mismatch between 'model.name' and 'model_info.name' in the model adapter, model_info.name will be updated to align with 'model.name'."
        )

    ##################
    # Configurations #
    ##################

    @property
    def configuration(self) -> dict:
        # load from model
        if self._model_entity is not None:
            configuration = self._configuration
        else:
            configuration = dict()
        return configuration

    @configuration.setter
    def configuration(self, configuration: dict):
        assert isinstance(configuration, dict)
        if self._model_entity is not None:
            # Update configuration with received dict
            self._model_entity.configuration = configuration
            self.adapter_defaults = AdapterDefaults(self)
            self._configuration = self.adapter_defaults

    ############
    # Entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self._project = self.model_entity.project
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def feature_set(self):
        if self._feature_set is None:
            self._feature_set = self._get_feature_set()
        assert isinstance(self._feature_set, entities.FeatureSet)
        return self._feature_set

    @property
    def model_entity(self):
        if self._model_entity is None:
            raise ValueError("No model entity loaded. Please load a model (adapter.load_from_model(<dl.Model>)) or set: 'adapter.model_entity=<dl.Model>'")
        assert isinstance(self._model_entity, entities.Model)
        return self._model_entity

    @model_entity.setter
    def model_entity(self, model_entity):
        assert isinstance(model_entity, entities.Model)
        if self._model_entity is not None and isinstance(self._model_entity, entities.Model):
            if self._model_entity.id != model_entity.id:
                self.logger.warning('Replacing Model from {!r} to {!r}'.format(self._model_entity.name, model_entity.name))
        self._model_entity = model_entity
        self.adapter_defaults = AdapterDefaults(self)
        self._configuration = self.adapter_defaults

    ###################################
    # NEED TO IMPLEMENT THESE METHODS #
    ###################################

    def load(self, local_path, **kwargs):
        """
        Loads model and populates self.model with a `runnable` model

        Virtual method - need to implement

        This function is called by load_from_model (download to local and then loads)

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement `load` method in {}".format(self.__class__.__name__))

    def save(self, local_path, **kwargs):
        """
        Saves configuration and weights locally

        Virtual method - need to implement

        the function is called in save_to_model which first save locally and then uploads to model entity

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement `save` method in {}".format(self.__class__.__name__))

    def train(self, data_path, output_path, **kwargs):
        """
        Virtual method - need to implement

        Train the model according to data in data_paths and save the train outputs to output_path,
        this include the weights and any other artifacts created during train

        :param data_path: `str` local File System path to where the data was downloaded and converted at
        :param output_path: `str` local File System path where to dump training mid-results (checkpoints, logs...)
        """
        raise NotImplementedError("Please implement `train` method in {}".format(self.__class__.__name__))

    def predict(self, batch, **kwargs):
        """
        Model inference (predictions) on batch of items

        Virtual method - need to implement

        :param batch: output of the `prepare_item_func` func
        :return: `list[dl.AnnotationCollection]` each collection is per each image / item in the batch
        """
        raise NotImplementedError("Please implement `predict` method in {}".format(self.__class__.__name__))

    def embed(self, batch, **kwargs):
        """
        Extract model embeddings on batch of items

        Virtual method - need to implement

        :param batch: output of the `prepare_item_func` func
        :return: `list[list]` a feature vector per each item in the batch
        """
        raise NotImplementedError("Please implement `embed` method in {}".format(self.__class__.__name__))

    def evaluate(self, model: entities.Model, dataset: entities.Dataset, filters: entities.Filters) -> entities.Model:
        """
        This function evaluates the model prediction on a dataset (with GT annotations).
        The evaluation process will upload the scores and metrics to the platform.

        :param model: The model to evaluate (annotation.metadata.system.model.name
        :param dataset: Dataset where the model predicted and uploaded its annotations
        :param filters: Filters to query items on the dataset
        :return:
        """
        import dtlpymetrics

        compare_types = model.output_type
        if not filters:
            filters = entities.Filters()
        if filters is not None and isinstance(filters, dict):
            filters = entities.Filters(custom_filter=filters)
        model = dtlpymetrics.scoring.create_model_score(
            model=model,
            dataset=dataset,
            filters=filters,
            compare_types=compare_types,
        )
        return model

    def convert_from_dtlpy(self, data_path, **kwargs):
        """Convert Dataloop structure data to model structured

            Virtual method - need to implement

            e.g. take dlp dir structure and construct annotation file

        :param data_path: `str` local File System directory path where we already downloaded the data from dataloop platform
        :return:
        """
        raise NotImplementedError("Please implement `convert_from_dtlpy` method in {}".format(self.__class__.__name__))

    #################
    # DTLPY METHODS #
    ################
    def prepare_item_func(self, item: entities.Item):
        """
        Prepare the Dataloop item before calling the `predict` function with a batch.
        A user can override this function to load item differently
        Default will load the item according the input_type (mapping type to function is in self.item_to_batch_mapping)

        :param item:
        :return: preprocessed: the var with the loaded item information (e.g. ndarray for image, dict for json files etc)
        """
        # Item to batch func
        if isinstance(self.model_entity.input_type, list):
            if 'text' in self.model_entity.input_type and 'text' in item.mimetype:
                processed = self._item_to_text(item)
            elif 'image' in self.model_entity.input_type and 'image' in item.mimetype:
                processed = self._item_to_image(item)
            else:
                processed = self._item_to_item(item)

        elif self.model_entity.input_type in self.item_to_batch_mapping:
            processed = self.item_to_batch_mapping[self.model_entity.input_type](item)

        else:
            processed = self._item_to_item(item)

        return processed

    def __include_model_annotations(self, annotation_filters):
        include_model_annotations = self.model_entity.configuration.get("include_model_annotations", False)
        if include_model_annotations is False:
            if annotation_filters.custom_filter is None:
                annotation_filters.add(field="metadata.system.model.name", values=False, operator=entities.FiltersOperations.EXISTS)
            else:
                annotation_filters.custom_filter['filter']['$and'].append({'metadata.system.model.name': {'$exists': False}})
        return annotation_filters

    def __download_items(self, dataset, filters, local_path, annotation_options, annotation_filters=None):
        """
        Download items from dataset with optional annotation filters.

        :param dataset: Dataset to download from
        :param filters: Filters to apply
        :param local_path: Local path to save files
        :param annotation_options: Annotation download options
        :param annotation_filters: Optional filters for annotations
        :return: List of downloaded items
        """
        if annotation_options == entities.ViewAnnotationOptions.JSON:
            downloader = repositories.Downloader(dataset.items)
            return downloader._download_recursive(
                local_path=local_path,
                filters=filters,
                annotation_filters=annotation_filters
            )
        else:
            return dataset.items.download(
                filters=filters,
                local_path=local_path,
                annotation_options=annotation_options,
                annotation_filters=annotation_filters
            )

    def __download_background_images(self, filters, data_subset_base_path, annotation_options):
        background_list = list()
        if self.configuration.get('include_background', False) is True:
            filters.custom_filter["filter"]["$and"].append({"annotated": False})
            background_list = self.__download_items(
                dataset=self.model_entity.dataset,
                filters=filters,
                local_path=data_subset_base_path,
                annotation_options=annotation_options
            )
        return background_list

    def prepare_data(
        self,
        dataset: entities.Dataset,
        # paths
        root_path=None,
        data_path=None,
        output_path=None,
        #
        overwrite=False,
        **kwargs,
    ):
        """
        Prepares dataset locally before training or evaluation.
        download the specific subset selected to data_path and preforms `self.convert` to the data_path dir

        :param dataset: dl.Dataset
        :param root_path: `str` root directory for training. default is "tmp". Can be set using self.adapter_defaults.root_path
        :param data_path: `str` dataset directory. default <root_path>/"data". Can be set using self.adapter_defaults.data_path
        :param output_path: `str` save everything to this folder. default <root_path>/"output". Can be set using self.adapter_defaults.output_path

        :param bool overwrite: overwrite the data path (download again). default is False
        """
        # define paths
        dataloop_path = service_defaults.DATALOOP_PATH
        root_path = self.adapter_defaults.resolve("root_path", root_path)
        data_path = self.adapter_defaults.resolve("data_path", data_path)
        output_path = self.adapter_defaults.resolve("output_path", output_path)
        if root_path is None:
            now = datetime.datetime.now()
            root_path = os.path.join(
                dataloop_path,
                'model_data',
                "{s_id}_{s_n}".format(s_id=self.model_entity.id, s_n=self.model_entity.name),
                now.strftime('%Y-%m-%d-%H%M%S'),
            )
        if data_path is None:
            data_path = os.path.join(root_path, 'datasets', self.model_entity.dataset.id)
            os.makedirs(data_path, exist_ok=True)
        if output_path is None:
            output_path = os.path.join(root_path, 'output')
            os.makedirs(output_path, exist_ok=True)

        if len(os.listdir(data_path)) > 0:
            self.logger.warning("Data path directory ({}) is not empty..".format(data_path))

        annotation_options = entities.ViewAnnotationOptions.JSON
        if self.model_entity.output_type in [entities.AnnotationType.SEGMENTATION]:
            annotation_options = entities.ViewAnnotationOptions.INSTANCE

        # Download the subset items
        subsets = self.model_entity.metadata.get("system", {}).get("subsets", None)
        annotations_subsets = self.model_entity.metadata.get("system", {}).get("annotationsSubsets", {})
        if subsets is None:
            raise ValueError("Model (id: {}) must have subsets in metadata.system.subsets".format(self.model_entity.id))
        for subset, filters_dict in subsets.items():
            _filters_dict = filters_dict.copy()
            data_subset_base_path = os.path.join(data_path, subset)
            if os.path.isdir(data_subset_base_path) and not overwrite:
                # existing and dont overwrite
                self.logger.debug("Subset {!r} already exists (and overwrite=False). Skipping.".format(subset))
                continue

            filters = entities.Filters(custom_filter=_filters_dict)
            self.logger.debug("Downloading subset {!r} of {}".format(subset, self.model_entity.dataset.name))

            annotation_filters = None
            if subset in annotations_subsets:
                annotation_filters = entities.Filters(
                    use_defaults=False,
                    resource=entities.FiltersResource.ANNOTATION,
                    custom_filter=annotations_subsets[subset],
                )
            # if user provided annotation_filters, skip the default filters
            elif self.model_entity.output_type is not None and self.model_entity.output_type != "embedding":
                annotation_filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION, use_defaults=False)
                if self.model_entity.output_type in [
                    entities.AnnotationType.SEGMENTATION,
                    entities.AnnotationType.POLYGON,
                ]:
                    model_output_types = [entities.AnnotationType.SEGMENTATION, entities.AnnotationType.POLYGON]
                else:
                    model_output_types = [self.model_entity.output_type]

                annotation_filters.add(
                    field=entities.FiltersKnownFields.TYPE,
                    values=model_output_types,
                    operator=entities.FiltersOperations.IN,
                )

            annotation_filters = self.__include_model_annotations(annotation_filters)
            annotations_subsets[subset] = annotation_filters.prepare()

            ret_list = self.__download_items(
                dataset=dataset,
                filters=filters,
                local_path=data_subset_base_path,
                annotation_options=annotation_options,
                annotation_filters=annotation_filters
            )
            _filters_dict = subsets[subset].copy()
            filters = entities.Filters(custom_filter=_filters_dict)
            background_ret_list = self.__download_background_images(
                filters=filters,
                data_subset_base_path=data_subset_base_path,
                annotation_options=annotation_options,
            )
            ret_list = list(ret_list)
            background_ret_list = list(background_ret_list)
            self.logger.debug(f"Subset '{subset}': ret_list length: {len(ret_list)}, background_ret_list length: {len(background_ret_list)}")
            # Combine ret_list and background_ret_list generators into a single generator
            ret_list = ret_list + background_ret_list
            if isinstance(ret_list, list) and len(ret_list) == 0:
                if annotation_filters is not None:
                    annotation_filters_str = annotation_filters.prepare()
                else:
                    annotation_filters_str = None
                raise ValueError(
                    f"No items downloaded for subset {subset}! Cannot train model with empty subset.\n"
                    f"Subset {subset} filters: {filters.prepare()}\n"
                    f"Annotation filters: {annotation_filters_str}"
                )

        self.convert_from_dtlpy(data_path=data_path, **kwargs)
        return root_path, data_path, output_path

    def load_from_model(self, model_entity=None, local_path=None, overwrite=True, **kwargs):
        """Loads a model from given `dl.Model`.
            Reads configurations and instantiate self.model_entity
            Downloads the model_entity bucket (if available)

        :param model_entity:  `str` dl.Model entity
        :param local_path:  `str` directory path in local FileSystem to download the model_entity to
        :param overwrite: `bool` (default False) if False does not download files with same name else (True) download all
        """
        if model_entity is not None:
            self.model_entity = model_entity
        if local_path is None:
            local_path = os.path.join(service_defaults.DATALOOP_PATH, "models", self.model_entity.name)
        # Load configuration and adapter defaults
        self.adapter_defaults = AdapterDefaults(self)
        # Point _configuration to the same object since AdapterDefaults inherits from ModelConfigurations
        self._configuration = self.adapter_defaults
        # Download
        self.model_entity.artifacts.download(local_path=local_path, overwrite=overwrite)
        self.load(local_path, **kwargs)

    def save_to_model(self, local_path=None, cleanup=False, replace=True, **kwargs):
        """
        Saves the model state to a new bucket and configuration

        Saves configuration and weights to artifacts
        Mark the model as `trained`
        loads only applies for remote buckets

        :param local_path: `str` directory path in local FileSystem to save the current model bucket (weights) (default will create a temp dir)
        :param replace: `bool` will clean the bucket's content before uploading new files
        :param cleanup: `bool` if True (default) remove the data from local FileSystem after upload
        :return:
        """

        if local_path is None:
            local_path = tempfile.mkdtemp(prefix="model_{}".format(self.model_entity.name))
            self.logger.debug("Using temporary dir at {}".format(local_path))

        self.save(local_path=local_path, **kwargs)

        if self.model_entity is None:
            raise ValueError('Missing model entity on the adapter. ' 'Please set before saving: "adapter.model_entity=model"')

        self.model_entity.artifacts.upload(filepath=os.path.join(local_path, '*'), overwrite=True)
        if cleanup:
            shutil.rmtree(path=local_path, ignore_errors=True)
            self.logger.info("Clean-up. deleting {}".format(local_path))

    # ===============
    # SERVICE METHODS
    # ===============

    @entities.Package.decorators.function(
        display_name='Predict Items',
        inputs={'items': 'Item[]'},
        outputs={'items': 'Item[]', 'annotations': 'Annotation[]'},
    )
    def predict_items(self, items: list, batch_size=None, **kwargs):
        """
        Run the predict function on the input list of items (or single) and return the items and the predictions.
        Each prediction is by the model output type (package.output_type) and model_info in the metadata

        :param items: `List[dl.Item]` list of items to predict
        :param batch_size: `int` size of batch to run a single inference

        :return: `List[dl.Item]`, `List[List[dl.Annotation]]`
        """
        if batch_size is None:
            batch_size = self.configuration.get('batch_size', 4)
        input_type = self.model_entity.input_type
        self.logger.debug("Predicting {} items, using batch size {}. input type: {}".format(len(items), batch_size, input_type))
        pool = ThreadPoolExecutor(max_workers=16)
        error_counter = 0
        fail_ids = list()
        annotations = list()
        for i_batch in tqdm.tqdm(range(0, len(items), batch_size), desc='predicting', unit='bt', leave=None, file=sys.stdout):
            batch_items = items[i_batch : i_batch + batch_size]
            batch = list(pool.map(self.prepare_item_func, batch_items))
            try:
                batch_collections = self.predict(batch, **kwargs)
            except Exception as e:
                item_ids = [item.id for item in batch_items]
                self.logger.error(f"Failed to predict batch {i_batch} for items {item_ids}. Error: {e}\n{traceback.format_exc()}")
                error_counter += 1
                fail_ids.extend(item_ids)
                continue
            _futures = list(pool.map(partial(self._update_predictions_metadata), batch_items, batch_collections))
            # Loop over the futures to make sure they are all done to avoid race conditions
            _ = [_f for _f in _futures]
            self.logger.debug("Uploading items' annotation for model {!r}.".format(self.model_entity.name))
            try:
                batch_collections = list(
                    pool.map(partial(self._upload_model_annotations), batch_items, batch_collections)
                )
            except Exception as err:
                item_ids = [item.id for item in batch_items]
                self.logger.error(
                    f"Failed to upload annotations for items {item_ids}. Error: {err}\n{traceback.format_exc()}"
                )
                error_counter += 1
                fail_ids.extend(item_ids)

            for collection in batch_collections:
                # function needs to return `List[List[dl.Annotation]]`
                # convert annotation collection to a list of dl.Annotation for each batch
                if isinstance(collection, entities.AnnotationCollection):
                    annotations.extend([annotation for annotation in collection.annotations])
                else:
                    logger.warning(f'RETURN TYPE MAY BE INVALID: {type(collection)}')
                    annotations.extend(collection)
            # TODO call the callback

        pool.shutdown()
        if error_counter > 0:
            raise Exception(f"Failed to predict all items. Failed IDs: {fail_ids}, See logs for more details")
        return items, annotations

    @entities.Package.decorators.function(
        display_name='Embed Items',
        inputs={'items': 'Item[]'},
        outputs={'items': 'Item[]', 'features': 'Json[]'},
    )
    def embed_items(self, items: list, upload_features=None, batch_size=None, progress: utilities.Progress = None, **kwargs):
        """
        Extract feature from an input list of items (or single) and return the items and the feature vector.

        :param items: `List[dl.Item]` list of items to embed
        :param upload_features: `bool` uploads the features on the given items
        :param batch_size: `int` size of batch to run a single embed

        :return: `List[dl.Item]`, `List[List[vector]]`
        """
        if batch_size is None:
            batch_size = self.configuration.get('batch_size', 4)
        upload_features = self.adapter_defaults.resolve("upload_features", upload_features)
        skip_default_items = upload_features is None
        if upload_features is None:
            upload_features = True
        input_type = self.model_entity.input_type
        self.logger.debug("Embedding {} items, using batch size {}. input type: {}".format(len(items), batch_size, input_type))
        error_counter = 0
        fail_ids = list()

        feature_set = self.feature_set

        # upload the feature vectors
        pool = ThreadPoolExecutor(max_workers=16)
        vectors = list()
        _items = list()
        for i_batch in tqdm.tqdm(
            range(0, len(items), batch_size),
            desc='embedding',
            unit='bt',
            leave=None,
            file=sys.stdout,
        ):
            batch_items = items[i_batch : i_batch + batch_size]
            batch = list(pool.map(self.prepare_item_func, batch_items))
            try:
                batch_vectors = self.embed(batch, **kwargs)
            except Exception as err:
                item_ids = [item.id for item in batch_items]
                self.logger.error(f"Failed to embed batch {i_batch} for items {item_ids}. Error: {err}\n{traceback.format_exc()}")
                error_counter += 1
                fail_ids.extend(item_ids)
                continue
            vectors.extend(batch_vectors)
            # Save the items in the order of the vectors
            _items.extend(batch_items)
        pool.shutdown()

        if upload_features is True:
            embeddings_size = self.configuration.get('embeddings_size', 256)
            valid_items = []
            valid_vectors = []
            items_to_upload = []
            vectors_to_upload = []
            
            for item, vector in zip(_items, vectors):
                # Check if vector is valid
                if vector is None or len(vector) != embeddings_size:
                    self.logger.warning(f"Vector generated for item {item.id} is None or has wrong size. Skipping...")
                    continue

                # Item and vector are valid
                valid_items.append(item)
                valid_vectors.append(vector)
                
                # Check if item should be skipped (prompt items)
                _system_metadata = getattr(item, 'system', dict())
                is_prompt = _system_metadata.get('shebang', dict()).get('dltype', '') == 'prompt'
                if skip_default_items and is_prompt:
                    self.logger.debug(f"Skipping feature upload for prompt item {item.id}")
                    continue
                
                # Items were not skipped - should be uploaded
                items_to_upload.append(item)
                vectors_to_upload.append(vector)
            
            # Update the original lists with valid items only
            _items[:] = valid_items
            vectors[:] = valid_vectors
            
            if len(_items) != len(vectors):
                raise ValueError(f"The number of items ({len(_items)}) is not equal to the number of vectors ({len(vectors)}).")
            
            self.logger.debug(f"Uploading {len(items_to_upload)} items' feature vectors for model {self.model_entity.name}.")
            try:
                start_time = time.time()
                feature_set.features.create(entity=items_to_upload, value=vectors_to_upload, feature_set_id=feature_set.id, project_id=self.model_entity.project_id)
                self.logger.debug(f"Uploaded {len(items_to_upload)} items' feature vectors for model {self.model_entity.name} in {time.time() - start_time} seconds.")
            except Exception as err:
                self.logger.error(f"Failed to upload feature vectors. Error: {err}\n{traceback.format_exc()}")
                error_counter += 1
        if error_counter > 0:
            raise Exception(f"Failed to embed all items. Failed IDs: {fail_ids}, See logs for more details")
        return _items, vectors

    @entities.Package.decorators.function(
        display_name='Embed Dataset with DQL',
        inputs={'dataset': 'Dataset', 'filters': 'Json'},
    )
    def embed_dataset(
        self,
        dataset: entities.Dataset,
        filters: Optional[entities.Filters] = None,
        upload_features: Optional[bool] = None,
        batch_size: Optional[int] = None,
        progress: Optional[utilities.Progress] = None,
        **kwargs,
    ):
        """
        Run model embedding on all items in a dataset

        :param dataset: Dataset entity to embed
        :param filters: Filters entity for filtering before embedding
        :param upload_features: bool whether to upload features back to platform
        :param batch_size: int size of batch to run a single embedding
        :param progress: dl.Progress object to track progress
        :return: bool indicating if embedding completed successfully
        """

        self._execute_dataset_operation(
            dataset=dataset,
            operation_type='embed',
            filters=filters,
            progress=progress,
            batch_size=batch_size,
        )

    @entities.Package.decorators.function(
        display_name='Predict Dataset with DQL',
        inputs={'dataset': 'Dataset', 'filters': 'Json'},
    )
    def predict_dataset(
        self,
        dataset: entities.Dataset,
        filters: Optional[entities.Filters] = None,
        batch_size: Optional[int] = None,
        progress: Optional[utilities.Progress] = None,
        **kwargs,
    ):
        """
        Run model prediction on all items in a dataset

        :param dataset: Dataset entity to predict
        :param filters: Filters entity for filtering before prediction
        :param batch_size: int size of batch to run a single prediction
        :param progress: dl.Progress object to track progress
        :return: bool indicating if prediction completed successfully
        """
        self._execute_dataset_operation(
            dataset=dataset,
            operation_type='predict',
            filters=filters,
            progress=progress,
            batch_size=batch_size,
        )

    @entities.Package.decorators.function(
        display_name='Train a Model',
        inputs={'model': entities.Model},
        outputs={'model': entities.Model},
    )
    def train_model(self, model: entities.Model, cleanup=False, progress: utilities.Progress = None, context: utilities.Context = None):
        """
        Train on existing model.
        data will be taken from dl.Model.datasetId
        configuration is as defined in dl.Model.configuration
        upload the output the model's bucket (model.bucket)
        """
        if isinstance(model, dict):
            model = repositories.Models(client_api=self._client_api).get(model_id=model['id'])
        output_path = None
        try:
            logger.info("Received {s} for training".format(s=model.id))
            model = model.wait_for_model_ready()
            if model.status == 'failed':
                raise ValueError("Model is in failed state, cannot train.")

            ##############
            # Set status #
            ##############
            model.status = 'training'
            if context is not None:
                if 'system' not in model.metadata:
                    model.metadata['system'] = dict()
            model.update(reload_services=False)

            ##########################
            # load model and weights #
            ##########################
            logger.info("Loading Adapter with: {n} ({i!r})".format(n=model.name, i=model.id))
            self.load_from_model(model_entity=model)

            ################
            # prepare data #
            ################
            root_path, data_path, output_path = self.prepare_data(dataset=self.model_entity.dataset, root_path=os.path.join('tmp', model.id))
            # Start the Train
            logger.info(f"Training model {model.name!r} ({model.id!r}) on data {data_path!r}")
            if progress is not None:
                progress.update(message='starting training')

            def on_epoch_end_callback(i_epoch, n_epoch):
                if progress is not None:
                    progress.update(progress=int(100 * (i_epoch + 1) / n_epoch), message='finished epoch: {}/{}'.format(i_epoch, n_epoch))

            self.train(data_path=data_path, output_path=output_path, on_epoch_end_callback=on_epoch_end_callback)
            if progress is not None:
                progress.update(message='saving model', progress=99)

            self.save_to_model(local_path=output_path, replace=True)
            model.status = 'trained'
            model.update(reload_services=False)
            ###########
            # cleanup #
            ###########
            if cleanup:
                shutil.rmtree(output_path, ignore_errors=True)
        except Exception:
            # save also on fail
            if output_path is not None:
                self.save_to_model(local_path=output_path, replace=True)
            logger.info('Execution failed. Setting model.status to failed')
            raise
        return model

    @entities.Package.decorators.function(
        display_name='Evaluate a Model',
        inputs={'model': entities.Model, 'dataset': entities.Dataset, 'filters': 'Json'},
        outputs={'model': entities.Model, 'dataset': entities.Dataset},
    )
    def evaluate_model(
        self,
        model: entities.Model,
        dataset: entities.Dataset,
        filters: entities.Filters = None,
        #
        progress: utilities.Progress = None,
        context: utilities.Context = None,
    ):
        """
        Evaluate a model.
        data will be downloaded from the dataset and query
        configuration is as defined in dl.Model.configuration
        upload annotations and calculate metrics vs GT

        :param model: Model entity to run prediction
        :param dataset: Dataset to evaluate
        :param filters: Filter for specific items from dataset
        :param progress: dl.Progress for report FaaS progress
        :param context:
        :return:
        """
        logger.info(f"Received model: {model.id} for evaluation on dataset (name: {dataset.name}, id: {dataset.id}")
        ##########################
        # load model and weights #
        ##########################
        logger.info(f"Loading Adapter with: {model.name} ({model.id!r})")
        self.load_from_model(dataset=dataset, model_entity=model)

        ##############
        # Predicting #
        ##############
        logger.info(f"Calling prediction, dataset: {dataset.name!r} ({model.id!r}), filters: {filters}")
        if not filters:
            filters = entities.Filters()
        if self.adapter_defaults.get("overwrite_annotations", True) is True:
            self._execute_dataset_operation(
                dataset=dataset,
                operation_type='predict',
                filters=filters,
                multiple_executions=False,
            )

        ##############
        # Evaluating #
        ##############
        logger.info(f"Starting adapter.evaluate()")
        if progress is not None:
            progress.update(message='calculating metrics', progress=98)
        model = self.evaluate(model=model, dataset=dataset, filters=filters)
        #########
        # Done! #
        #########
        if progress is not None:
            progress.update(message='finishing evaluation', progress=99)
        return model, dataset

    # =============
    # INNER METHODS
    # =============
    def _get_feature_set(self):
        # Ensure feature set creation/retrieval is thread-safe across the class
        with self.__class__._feature_set_lock:
            # Search for existing feature set for this model id
            feature_set = self.model_entity.feature_set
            if feature_set is None:
                logger.info('Feature Set not found. creating... ')
                try:
                    self.project.feature_sets.get(feature_set_name=self.model_entity.name)
                    feature_set_name = f"{self.model_entity.name}-{''.join(random.choices(string.ascii_letters + string.digits, k=5))}"
                    logger.warning(
                        f"Feature set with the model name already exists. Creating new feature set with name {feature_set_name}"
                    )

                except exceptions.NotFound:
                    feature_set_name = self.model_entity.name
                feature_set = self.project.feature_sets.create(
                    name=feature_set_name,
                    entity_type=entities.FeatureEntityType.ITEM,
                    model_id=self.model_entity.id,
                    project_id=self.project.id,
                    set_type=self.model_entity.name,
                    size=self.configuration.get('embeddings_size', 256),
                )
                logger.info(f'Feature Set created! name: {feature_set.name}, id: {feature_set.id}')
            else:
                logger.info(f'Feature Set found! name: {feature_set.name}, id: {feature_set.id}')
            return feature_set

    def _execute_dataset_operation(
        self,
        dataset: entities.Dataset,
        operation_type: str,
        filters: Optional[entities.Filters] = None,
        progress: Optional[utilities.Progress] = None,
        batch_size: Optional[int] = None,
        multiple_executions: bool = True,
    ) -> bool:
        """
        Execute dataset operation (predict/embed) with batching and filtering support.

        :param dataset: Dataset entity to run operation on
        :param operation_type: Type of operation to execute ('predict' or 'embed')
        :param filters: Filters entity to filter items, default None
        :param progress: Progress object for tracking progress, default None
        :param batch_size: Size of batches to process items, default None (uses model config)
        :param multiple_executions: Whether to use multiple executions when filters exceed subset limit, default True
        :return: True if operation completes successfully
        :raises ValueError: If operation_type is not 'predict' or 'embed'
        """
        self.logger.debug(f"Running {operation_type} for dataset (name:{dataset.name}, id:{dataset.id})")

        if not filters:
            self.logger.debug("No filters provided, using default filters")
            filters = entities.Filters()
        if filters is not None and isinstance(filters, dict):
            self.logger.debug(f"Received custom filters {filters}")
            filters = entities.Filters(custom_filter=filters)

        if operation_type == 'embed':
            feature_set = self.feature_set
            logger.info(f"Feature set found! name: {feature_set.name}, id: {feature_set.id}")

        predict_embed_subset_limit = self.configuration.get('predict_embed_subset_limit', PREDICT_EMBED_DEFAULT_SUBSET_LIMIT)
        predict_embed_timeout = self.configuration.get('predict_embed_timeout', PREDICT_EMBED_DEFAULT_TIMEOUT)
        self.logger.debug(f"Inputs: predict_embed_subset_limit: {predict_embed_subset_limit}, predict_embed_timeout: {predict_embed_timeout}")
        tmp_filters = copy.deepcopy(filters.prepare())
        tmp_filters['pageSize'] = 0
        num_items = dataset.items.list(filters=entities.Filters(custom_filter=tmp_filters)).items_count
        self.logger.debug(f"Number of items for current filters: {num_items}")

        # One-item lookahead on generator: if only one subset, run locally; else create executions for all
        gen = entities.Filters._get_split_filters(dataset, filters, predict_embed_subset_limit)
        try:
            first_filter = next(gen)
        except StopIteration:
            self.logger.info("Filters is empty, nothing to run")
            return True

        try:
            second_filter = next(gen)
            multiple = True
        except StopIteration:
            multiple = False

        # Create consistent iterable of all filters for reuse
        # Both paths use chain to ensure consistent type and iteration behavior
        if multiple:
            # Chain together the pre-consumed filters with the remaining generator
            all_filters = chain([first_filter, second_filter], gen)
        else:
            # Single filter - use chain with empty generator for consistency
            all_filters = chain([first_filter], [])

        if not multiple or not multiple_executions:
            self.logger.info("Running locally")
            if batch_size is None:
                batch_size = self.configuration.get('batch_size', 4)

            # Process each filter locally
            for filter_dict in all_filters:
                filter_dict["pageSize"] = 1000
                single_filters = entities.Filters(custom_filter=filter_dict)
                pages = dataset.items.list(filters=single_filters)
                self.logger.info(f"Processing filter on: {pages.items_count} items")
                items = [item for page in pages for item in page if item.type == 'file']
                self.logger.debug(f"Items length: {len(items)}")

                if operation_type == 'embed':
                    self.embed_items(items=items, batch_size=batch_size, progress=progress)
                elif operation_type == 'predict':
                    self.predict_items(items=items, batch_size=batch_size, progress=progress)
                else:
                    raise ValueError(f"Unsupported operation type: {operation_type}")
            return True

        executions = []
        for filter_dict in all_filters:
            self.logger.debug(f"Creating execution for models {operation_type} with dataset id {dataset.id} and filter_dict {filter_dict}")
            if operation_type == 'embed':
                execution = self.model_entity.models.embed(
                    model=self.model_entity,
                    dataset_id=dataset.id,
                    filters=entities.Filters(custom_filter=filter_dict),
                )
            elif operation_type == 'predict':
                execution = self.model_entity.models.predict(
                    model=self.model_entity, dataset_id=dataset.id, filters=entities.Filters(custom_filter=filter_dict)
                )
            else:
                raise ValueError(f"Unsupported operation type: {operation_type}")
            executions.append(execution)

        if executions:
            self.logger.info(f'Created {len(executions)} executions for {operation_type}, ' f'execution ids: {[ex.id for ex in executions]}')

            wait_time = 5
            start_time = time.time()
            last_perc = 0
            self.logger.debug(f"Waiting for executions with timeout {predict_embed_timeout}")
            while time.time() - start_time < predict_embed_timeout:
                continue_loop = False
                total_perc = 0

                for ex in executions:
                    execution = self.project.executions.get(execution_id=ex.id)
                    perc = execution.latest_status.get('percentComplete', 0)
                    total_perc += perc
                    if execution.in_progress():
                        continue_loop = True

                avg_perc = round(total_perc / len(executions), 0)
                if progress is not None and last_perc != avg_perc:
                    last_perc = avg_perc
                    progress.update(progress=last_perc, message=f'running {operation_type}')

                if not continue_loop:
                    break

                time.sleep(wait_time)
            self.logger.debug("End waiting for executions")
            # Check if any execution failed
            executions_filter = entities.Filters(resource=entities.FiltersResource.EXECUTION)
            executions_filter.add(field="id", values=[ex.id for ex in executions], operator=entities.FiltersOperations.IN)
            executions_filter.add(field='latestStatus.status', values='failed')
            executions_filter.page_size = 0
            failed_executions_count = self.project.executions.list(filters=executions_filter).items_count
            if failed_executions_count > 0:
                self.logger.error(f"Failed to {operation_type} for {failed_executions_count} executions")
                raise ValueError(f"Failed to {operation_type} entire dataset, please check the logs for more details")
        return True

    def _upload_model_annotations(self, item: entities.Item, predictions):
        """
        Utility function that upload prediction to dlp platform based on the package.output_type
        :param predictions: `dl.AnnotationCollection`
        :param cleanup: `bool` if set removes existing predictions with the same package-model name
        """
        if not (isinstance(predictions, entities.AnnotationCollection) or isinstance(predictions, list)):
            raise TypeError(f'predictions was expected to be of type {entities.AnnotationCollection}, but instead it is {type(predictions)}')
        clean_filter = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
        clean_filter.add(field='metadata.user.model.name', values=self.model_entity.name, method=entities.FiltersMethod.OR)
        clean_filter.add(field='metadata.system.model.name', values=self.model_entity.name, method=entities.FiltersMethod.OR)
        # clean_filter.add(field='type', values=self.model_entity.output_type,)
        item.annotations.delete(filters=clean_filter)
        annotations = item.annotations.upload(annotations=predictions)
        return annotations

    @staticmethod
    def _item_to_image(item):
        """
        Preprocess items before calling the `predict` functions.
        Convert item to numpy array

        :param item:
        :return:
        """
        try:
            buffer = item.download(save_locally=False)
            image = np.asarray(Image.open(buffer))
        except Exception as e:
            logger.error(f"Failed to convert image to np.array, Error: {e}\n{traceback.format_exc()}")
            image = None
        return image

    @staticmethod
    def _item_to_item(item):
        """
        Default item to batch function.
        This function should prepare a single item for the predict function, e.g. for images, it loads the image as numpy array
        :param item:
        :return:
        """
        return item

    @staticmethod
    def _item_to_text(item):
        filename = item.download(overwrite=True)
        text = None
        if item.mimetype == 'text/plain' or item.mimetype == 'text/markdown':
            with open(filename, 'r') as f:
                text = f.read()
                text = text.replace('\n', ' ')
        else:
            logger.warning('Item is not text file. mimetype: {}'.format(item.mimetype))
            text = item
        if os.path.exists(filename):
            os.remove(filename)
        return text

    @staticmethod
    def _uri_to_image(data_uri):
        # data_uri = "data:image/png;base64,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"
        image_b64 = data_uri.split(",")[1]
        binary = base64.b64decode(image_b64)
        image = np.asarray(Image.open(io.BytesIO(binary)))
        return image

    def _update_predictions_metadata(self, item: entities.Item, predictions: entities.AnnotationCollection):
        """
        add model_name and model_id to the metadata of the annotations.
        add model_info to the metadata of the system metadata of the annotation.
        Add item id to all the annotations in the AnnotationCollection

        :param item: Entity.Item
        :param predictions: item's AnnotationCollection
        :return:
        """
        for prediction in predictions:
            if prediction.type == entities.AnnotationType.SEGMENTATION:
                color = None
                try:
                    color = item.dataset._get_ontology().color_map.get(prediction.label, None)
                except (exceptions.BadRequest, exceptions.NotFound):
                    ...
                if color is None:
                    if self.model_entity._dataset is not None:
                        try:
                            color = self.model_entity.dataset._get_ontology().color_map.get(prediction.label, (255, 255, 255))
                        except (exceptions.BadRequest, exceptions.NotFound):
                            ...
                if color is None:
                    logger.warning("Can't get annotation color from model's dataset, using default.")
                    color = prediction.color
                prediction.color = color

            prediction.item_id = item.id
            if 'user' in prediction.metadata and 'model' in prediction.metadata['user']:
                prediction.metadata['user']['model']['model_id'] = self.model_entity.id
                prediction.metadata['user']['model']['name'] = self.model_entity.name
            if 'system' not in prediction.metadata:
                prediction.metadata['system'] = dict()
            if 'model' not in prediction.metadata['system']:
                prediction.metadata['system']['model'] = dict()
            confidence = prediction.metadata.get('user', dict()).get('model', dict()).get('confidence', None)
            prediction.metadata['system']['model'] = {
                'model_id': self.model_entity.id,
                'name': self.model_entity.name,
                'confidence': confidence,
            }

    ##############################
    # Callback Factory functions #
    ##############################
    @property
    def dataloop_keras_callback(self):
        """
        Returns the constructor for a keras api dump callback
        The callback is used for dlp platform to show train losses

        :return: DumpHistoryCallback constructor
        """
        try:
            import keras
        except (ImportError, ModuleNotFoundError) as err:
            raise RuntimeError(f'{self.__class__.__name__} depends on extenral package. Please install ') from err

        import os
        import time
        import json

        class DumpHistoryCallback(keras.callbacks.Callback):
            def __init__(self, dump_path):
                super().__init__()
                if os.path.isdir(dump_path):
                    dump_path = os.path.join(dump_path, f'__view__training-history__{time.strftime("%F-%X")}.json')
                self.dump_file = dump_path
                self.data = dict()

            def on_epoch_end(self, epoch, logs=None):
                logs = logs or {}
                for name, val in logs.items():
                    if name not in self.data:
                        self.data[name] = {'x': list(), 'y': list()}
                    self.data[name]['x'].append(float(epoch))
                    self.data[name]['y'].append(float(val))
                self.dump_history()

            def dump_history(self):
                _json = {
                    "query": {},
                    "datasetId": "",
                    "xlabel": "epoch",
                    "title": "training loss",
                    "ylabel": "val",
                    "type": "metric",
                    "data": [
                        {
                            "name": name,
                            "x": values['x'],
                            "y": values['y'],
                        }
                        for name, values in self.data.items()
                    ],
                }

                with open(self.dump_file, 'w') as f:
                    json.dump(_json, f, indent=2)

        return DumpHistoryCallback
