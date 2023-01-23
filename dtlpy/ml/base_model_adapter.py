import tempfile
import datetime
import logging
import typing
import shutil
import base64
import tqdm
import json
import io
import os
from PIL import Image
from functools import partial
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from .. import entities, utilities
from ..services import service_defaults

logger = logging.getLogger('ModelAdapter')


class BaseModelAdapter(utilities.BaseServiceRunner):
    def __init__(self, model_entity: entities.Model = None):
        self.logger = logger
        # entities
        self._model_entity = None
        self._package = None
        self.package_name = None
        self.model = None
        self.bucket_path = None
        if model_entity is not None:
            self.load_from_model(model_entity=model_entity)

    ##################
    # Configurations #
    ##################

    @property
    def configuration(self) -> dict:
        # load from model
        if self._model_entity is not None:
            configuration = self.model_entity.configuration
        # else - load the default from the package
        else:
            configuration = self.package.metadata.get('system', {}).get('ml', {}).get('defaultConfiguration', {})
        return configuration

    @configuration.setter
    def configuration(self, d):
        assert isinstance(d, dict)
        if self._model_entity is not None:
            self._model_entity.configuration = d

    ############
    # Entities #
    ############
    @property
    def model_entity(self):
        if self._model_entity is None:
            raise ValueError(
                "No model entity loaded. Please load a model (adapter.load_from_model(<dl.Model>)) or set: 'adapter.model_entity=<dl.Model>'")
        assert isinstance(self._model_entity, entities.Model)
        return self._model_entity

    @model_entity.setter
    def model_entity(self, model_entity):
        assert isinstance(model_entity, entities.Model)
        if self._model_entity is not None and isinstance(self._model_entity, entities.Model):
            if self._model_entity.id != model_entity.id:
                self.logger.warning(
                    'Replacing Model from {!r} to {!r}'.format(self._model_entity.name, model_entity.name))
        self._model_entity = model_entity
        self.package = model_entity.package

    @property
    def package(self):
        if self._model_entity is not None:
            self.package = self.model_entity.package
        if self._package is None:
            raise ValueError('Missing Package entity on adapter. please set: "adapter.package=package"')
        assert isinstance(self._package, entities.Package)
        return self._package

    @package.setter
    def package(self, package):
        assert isinstance(package, entities.Package)
        self.package_name = package.name
        self._package = package

    ###################################
    # NEED TO IMPLEMENT THESE METHODS #
    ###################################

    def load(self, local_path, **kwargs):
        """ Loads model and populates self.model with a `runnable` model

            Virtual method - need to implement

            This function is called by load_from_model (download to local and then loads)

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'load' method in {}".format(self.__class__.__name__))

    def save(self, local_path, **kwargs):
        """ saves configuration and weights locally

            Virtual method - need to implement

            the function is called in save_to_model which first save locally and then uploads to model entity

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'save' method in {}".format(self.__class__.__name__))

    def train(self, data_path, output_path, **kwargs):
        """
        Virtual method - need to implement

        Train the model according to data in data_paths and save the train outputs to output_path,
        this include the weights and any other artifacts created during train

        :param data_path: `str` local File System path to where the data was downloaded and converted at
        :param output_path: `str` local File System path where to dump training mid-results (checkpoints, logs...)
        """
        raise NotImplementedError("Please implement 'train' method in {}".format(self.__class__.__name__))

    def predict(self, batch, **kwargs):
        """ Model inference (predictions) on batch of images

            Virtual method - need to implement

        :param batch: `np.ndarray`
        :return: `list[dl.AnnotationCollection]` each collection is per each image / item in the batch
        """
        raise NotImplementedError("Please implement 'predict' method in {}".format(self.__class__.__name__))

    def evaluate(self, data_path, on_batch_end_callback: typing.Callable, **kwargs):
        """ Model evaluation

            Virtual method - need to implement

        :param data_path: local directory with set to predict
        :param on_batch_end_callback: Callable, run after batch end
        :return: `list[dl.AnnotationCollection]` each collection is per each image / item in the batch
        """
        raise NotImplementedError("Please implement 'evaluate' method in {}".format(self.__class__.__name__))

    def convert_from_dtlpy(self, data_path, **kwargs):
        """ Convert Dataloop structure data to model structured

            Virtual method - need to implement

            e.g. take dlp dir structure and construct annotation file

        :param data_path: `str` local File System directory path where we already downloaded the data from dataloop platform
        :return:
        """
        raise NotImplementedError("Please implement 'convert_from_dtlpy' method in {}".format(self.__class__.__name__))

    #################
    # DTLPY METHODS #
    #################

    def prepare_data(self,
                     dataset: entities.Dataset,
                     # paths
                     root_path=None,
                     data_path=None,
                     output_path=None,
                     #
                     overwrite=False,
                     **kwargs):
        """
        Prepares dataset locally before training or evaluation.
        download the specific subset selected to data_path and preforms `self.convert` to the data_path dir

        :param dataset: dl.Dataset
        :param root_path: `str` root directory for training. default is "tmp"
        :param data_path: `str` dataset directory. default <root_path>/"data"
        :param output_path: `str` save everything to this folder. default <root_path>/"output"

        :param bool overwrite: overwrite the data path (download again). default is False
        """
        # define paths
        dataloop_path = os.path.join(os.path.expanduser('~'), '.dataloop')
        if root_path is None:
            now = datetime.datetime.now()
            root_path = os.path.join(dataloop_path,
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
        subsets = dataset.metadata.get("system", dict()).get("subsets", None)
        if subsets is None:
            raise ValueError("Dataset (id: {}) must have subsets in metadata.system.subsets".format(dataset.id))
        for subset, filters_string in subsets.items():
            filters = entities.Filters(custom_filter=json.loads(filters_string))
            data_subset_base_path = os.path.join(data_path, subset)
            if os.path.isdir(data_subset_base_path) and not overwrite:
                # existing and dont overwrite
                self.logger.debug("Subset {!r} Existing (and overwrite=False). Skipping.".format(subset))
            else:
                self.logger.debug("Downloading subset {!r} of {}".format(subset,
                                                                         self.model_entity.dataset.name))
                ret_list = dataset.items.download(filters=filters,
                                                  local_path=data_subset_base_path,
                                                  annotation_options=annotation_options)

        self.convert_from_dtlpy(data_path=data_path, **kwargs)
        return root_path, data_path, output_path

    def load_from_model(self, model_entity=None, local_path=None, overwrite=False, **kwargs):
        """ Loads a model from given `dl.Model`.
            Reads configurations and instantiate self.model_entity
            Downloads the model_entity bucket (if available)

        :param model_entity:  `str` dl.Model entity
        :param local_path:  `str` directory path in local FileSystem to download the model_entity to
        :param overwrite: `bool` (default False) if False does not downloads files with same name else (True) download all
        """
        if model_entity is not None:
            self.model_entity = model_entity
        if local_path is None:
            local_path = os.path.join(service_defaults.DATALOOP_PATH, "models", self.model_entity.name)
        # update adapter instance
        _configuration = self.package.metadata.get('system', {}).get('ml', {}).get('defaultConfiguration', {})
        _configuration.update(self.model_entity.configuration)
        self.configuration = _configuration
        # Download
        self.model_entity.artifacts.download(
            local_path=local_path,
            overwrite=overwrite
        )
        self.configuration.update({'artifacts_path': local_path})
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
            raise ValueError('missing model entity on the adapter. '
                             'please set one before saving: "adapter.model_entity=model"')

        self.model_entity.artifacts.upload(filepath=os.path.join(local_path, '*'),
                                           overwrite=True)
        if cleanup:
            shutil.rmtree(path=local_path, ignore_errors=True)
            self.logger.info("Clean-up. deleting {}".format(local_path))
        self.model_entity.status = 'trained'
        self.model_entity = self.model_entity.update()

    # ===============
    # SERVICE METHODS
    # ===============

    @entities.Package.decorators.function(display_name='Predict Items',
                                          inputs={'items': 'Item[]'},
                                          outputs={'items': 'Item[]', 'annotations': 'Annotation[]'})
    def predict_items(self, items: list, upload_annotations=True, conf_threshold=0, batch_size=16, **kwargs):
        """
        Run the predict function on the input list of items (or single) and return the items and the predictions.
        Each prediction is by the model output type (package.output_type) and model_info in the metadata

        :param items: `List[dl.Item]` list of items to predict
        :param upload_annotations: `bool` uploads the predictions on the given items
        :param conf_threshold: `float` returns and uploads annotation only above this threshold
        :param batch_size: `int` size of batch to run a single inference

        :return: `List[dl.Item]`, `List[List[dl.Annotation]]`
        """

        input_type = self.model_entity.input_type
        self.logger.debug(
            "Predicting {} items, using batch size {}. input type: {}".format(len(items), batch_size, input_type))
        pool = ThreadPoolExecutor(max_workers=16)
        annotations = list()
        for i_batch in tqdm.tqdm(range(0, len(items), batch_size), desc='predicting', unit='bt', leave=None):
            batch_items = items[i_batch: i_batch + batch_size]
            if input_type == 'image':
                batch = list(pool.map(self._prepare_items_image_batch, batch_items))
            elif input_type == 'txt':
                batch = list(pool.map(self._prepare_items_txt_batch, batch_items))
            else:
                raise ValueError('Unknown inputType: {} (from model_entity.input_type'.format(input_type))
            batch_collections = self.predict(batch, **kwargs)
            for collection in batch_collections:
                # convert annotation collection to a list aof annotations jsons
                if isinstance(collection, entities.AnnotationCollection):
                    annotations.append(collection.to_json()['annotations'])
                else:
                    annotations.append(collection)
            if upload_annotations is True:
                self.logger.debug(
                    "Uploading items' annotation for model {!r}.".format(self.model_entity.name))
                try:
                    annotations = list(pool.map(partial(self._upload_model_annotations),
                                                batch_items, batch_collections))
                except Exception as err:
                    self.logger.exception("Failed to upload annotations items.")

        pool.shutdown()
        return items, annotations

    @entities.Package.decorators.function(display_name='Predict Dataset with DQL',
                                          inputs={'dataset': 'Dataset',
                                                  'filters': 'Json'})
    def predict_dataset(self,
                        dataset: entities.Dataset, filters: entities.Filters = None,
                        with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param dataset: Dataset entity to predict
        :param filters: Filters entity for a filtering before predicting
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same package-model name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image

        :return: `List[dl.AnnotationCollection]` where all annotation in the collection are of type package.output_type
                                                 and has prediction fields (model_info)
        """
        # TODO: do we want to add score filtering here?
        self.logger.debug(
            "Predicting dataset (name:{}, id:{}, using batch size {}. Reshaping to: {}".format(dataset.name,
                                                                                               dataset.id,
                                                                                               batch_size,
                                                                                               output_shape))
        if filters is not None:
            filters = entities.Filters(custom_filter=filters)
        pages = dataset.items.list(filters=filters, page_size=batch_size)
        for page in tqdm.tqdm(pages, total=pages.items_count, desc='predicting', unit='bt', leave=None):
            self.predict_items(items=page.items,
                               with_upload=with_upload,
                               cleanup=cleanup,
                               batch_size=batch_size,
                               output_shape=output_shape,
                               **kwargs)
        return True

    @entities.Package.decorators.function(display_name='Train a Model',
                                          inputs={'model': entities.Model},
                                          outputs={'model': entities.Model})
    def train_model(self,
                    model: entities.Model,
                    cleanup=False,
                    progress: utilities.Progress = None,
                    context: utilities.Context = None):
        # FROM PARENT
        """
            Train on existing model.
            data will be taken from dl.Model.datasetId
            configuration is as defined in dl.Model.configuration
            upload the output the model's bucket (model.bucket)
        """
        if isinstance(model, dict):
            model = context.package.models.get(model_id=model['model_id'])
        output_path = None
        try:
            logger.info("Received {s} for training".format(s=model.id))

            ##############
            # Set status #
            ##############
            model.status = 'training'
            if context is not None:
                if 'system' not in model.metadata:
                    model.metadata['system'] = dict()
                model.metadata['system']['trainExecutionId'] = context.execution_id
            model.update()

            ##########################
            # load model and weights #
            ##########################
            logger.info("Loading Adapter with: {n} ({i!r})".format(n=model.name, i=model.id))
            self.load_from_model(model_entity=model)

            ################
            # prepare data #
            ################
            root_path, data_path, output_path = self.prepare_data(
                dataset=self.model_entity.dataset,
                root_path=os.path.join('tmp', model.id)
            )
            # Start the Train
            logger.info("Training {p_name!r} with model {m_name!r} on data {d_path!r}".
                        format(p_name=self.package_name, m_name=model.id, d_path=data_path))
            if progress is not None:
                progress.update(message='starting training')

            def on_epoch_end_callback(i_epoch, n_epoch):
                if progress is not None:
                    progress.update(progress=int(100 * (i_epoch + 1) / n_epoch),
                                    message='finished epoch: {}/{}'.format(i_epoch, n_epoch))

            self.train(data_path=data_path,
                       output_path=output_path,
                       on_epoch_end_callback=on_epoch_end_callback)
            if progress is not None:
                progress.update(message='saving model',
                                progress=99)

            self.save_to_model(local_path=output_path, replace=True)

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
            model.status = 'failed'
            model.update()
            raise
        return model.id

    @entities.Package.decorators.function(display_name='Evaluate a Model',
                                          inputs={'model': entities.Model,
                                                  'dataset': entities.Dataset})
    def evaluate_model(self,
                       model: entities.Model,
                       dataset: entities.Dataset,
                       cleanup=False,
                       progress: utilities.Progress = None,
                       context: utilities.Context = None):
        """
        Evaluate a model.
        data will be downloaded from the dataset and query
        configuration is as defined in dl.Model.configuration
        upload annotations and calculate metrics vs GT
        """
        output_path = None
        try:
            logger.info(
                f"Received model: {model.id} for evaluation on dataset (name: {dataset.name}, id: {dataset.name}")
            ##########################
            # load model and weights #
            ##########################
            logger.info("Loading Adapter with: {n} ({i!r})".format(n=model.name, i=model.id))
            self.load_from_model(dataset=dataset,
                                 model_entity=model)

            ################
            # prepare data #
            ################
            root_path, data_path, output_path = self.prepare_data(
                dataset=dataset,
                root_path=os.path.join('tmp', model.id)
            )
            # Start the Train
            logger.info("Training {p_name!r} with model {m_name!r} on data {d_path!r}".
                        format(p_name=self.package_name, m_name=model.id, d_path=data_path))
            if progress is not None:
                progress.update(message='starting evaluation')

            def on_batch_end_callback(i_epoch, n_epoch):
                if progress is not None:
                    progress.update(progress=int(100 * (i_epoch + 1) / n_epoch),
                                    message='finished epoch: {}/{}'.format(i_epoch, n_epoch))

            self.evaluate(data_path=data_path,
                          on_batch_end_callback=on_batch_end_callback)
            if progress is not None:
                progress.update(message='finishing evaluation',
                                progress=99)

            ###########
            # cleanup #
            ###########
            if cleanup:
                shutil.rmtree(output_path, ignore_errors=True)
        except Exception:
            model.status = 'failed'
            model.update()
            raise
        return self.model

    # =============
    # INNER METHODS
    # =============

    def _upload_model_annotations(self, item: entities.Item, predictions):
        """
        Utility function that upload prediction to dlp platform based on the package.output_type
        :param predictions: `dl.AnnotationCollection`
        :param cleanup: `bool` if set removes existing predictions with the same package-model name
        """
        if not isinstance(predictions, entities.AnnotationCollection):
            raise TypeError('predictions was expected to be of type {}, but instead it is {}'.
                            format(entities.AnnotationCollection, type(predictions)))
        model_info_name = "{}-{}".format(self.package_name, self.model_entity.name)
        # if cleanup:
        #     clean_filter = entities.Filters(field='type',
        #                                     values=self.model_entity.output_type,
        #                                     resource=entities.FiltersResource.ANNOTATION)
        #     clean_filter.add(field='metadata.user.model.name', values=model_info_name)
        #     item.annotations.delete(filters=clean_filter)
        annotations = item.annotations.upload(annotations=predictions)
        return annotations

    @staticmethod
    def _prepare_items_image_batch(item):
        buffer = item.download(save_locally=False)
        image = np.asarray(Image.open(buffer))
        return image

    @staticmethod
    def _prepare_items_txt_batch(item):
        buffer = item.download(save_locally=False)
        txt = buffer.read().decode()
        return txt

    @staticmethod
    def _prepare_uris_image_batch(data_uri):
        # data_uri = "data:image/png;base64,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"
        image_b64 = data_uri.split(",")[1]
        binary = base64.b64decode(image_b64)
        image = np.asarray(Image.open(io.BytesIO(binary)))
        return image

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
            raise RuntimeError(
                '{} depends on extenral package. Please install '.format(self.__class__.__name__)) from err

        import os
        import time
        import json
        class DumpHistoryCallback(keras.callbacks.Callback):
            def __init__(self, dump_path):
                super().__init__()
                if os.path.isdir(dump_path):
                    dump_path = os.path.join(dump_path,
                                             '__view__training-history__{}.json'.format(time.strftime("%F-%X")))
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
                    "data": [{"name": name,
                              "x": values['x'],
                              "y": values['y']} for name, values in self.data.items()]
                }

                with open(self.dump_file, 'w') as f:
                    json.dump(_json, f, indent=2)

        return DumpHistoryCallback
