import tempfile
import datetime
import logging
import typing
import shutil
import tqdm
import json
import os
from PIL import Image
import numpy as np

from .. import entities, exceptions, dtlpy_services, utilities

logger = logging.getLogger('ModelAdapter')


class BaseModelAdapter(utilities.BaseServiceRunner):
    def __init__(self, model_entity: entities.Model):
        self.logger = logger
        # entities
        self._model_entity = None
        self._package = None
        self.package_name = None
        if model_entity is not None:
            self.model_entity = model_entity
        self.model = None
        self.bucket_path = None

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
            raise ValueError('Missing Model on adapter. please set: "adapter.model_entity=model"')
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
        if self.package.metadata['system']['ml']['outputType'] in [entities.AnnotationType.SEGMENTATION]:
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
            local_path = os.path.join(dtlpy_services.service_defaults.DATALOOP_PATH, "models", self.model_entity.name)
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
                                          inputs={'items': 'Item[]'})
    def predict_items(self, items: list, with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same package-model name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image

        :return: `List[dl.AnnotationCollection]` where all annotation in the collection are of type package.output_type
                                                 and has prediction fields (model_info)
        """
        # TODO: do we want to add score filtering here?
        self.logger.debug(
            "Predicting {} items, using batch size {}. Reshaping to: {}".format(len(items), batch_size, output_shape))
        all_predictions = list()
        for b in tqdm.tqdm(range(0, len(items), batch_size), desc='predicting', unit='bt', leave=None):
            batch = list()
            # TODO: add parallelism with multi threading
            # TODO: add resize when adding to batch
            for item in items[b: b + batch_size]:
                buffer = item.download(save_locally=False)
                img_pil = Image.open(buffer)
                if output_shape is not None:
                    img_pil = img_pil.resize(size=output_shape)
                img_np = np.asarray(img_pil).astype(np.float)
                batch.append(img_np)
            batch = np.asarray(batch)
            batch_predictions = self.predict(batch, **kwargs)
            all_predictions += batch_predictions

        if with_upload:
            try:
                for idx, item in enumerate(items):
                    all_predictions[idx] = self._upload_model_annotations(item,
                                                                          all_predictions[idx],
                                                                          cleanup=cleanup)

            except exceptions.InternalServerError as err:
                self.logger.error("Failed to upload annotations items. Error: {}".format(err))

            self.logger.debug("Uploading items' annotation for model {!r}. cleanup {}".format(self.model_entity.name,
                                                                                              cleanup))
        else:
            # fix the collection to have to correct item in the annotations
            for item, ann_coll in zip(items, all_predictions):
                for ann in ann_coll:
                    ann._item = item
                ann_coll.item = item
        return all_predictions

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
        return self.model.id

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
            logger.info("Received model: {} for training".format(model.id))

            ##############
            # Set status #
            ##############
            model.status = 'evaluating'
            if 'system' not in model.metadata:
                model.metadata['system'] = dict()
            if 'evaluateExecutionId' not in model.metadata['system']:
                model.metadata['system']['evaluations'] = list()
            model.metadata['system']['evaluations'].append(
                {"executionId": context.execution_id,
                 "datasetId": dataset.id,
                 "createdAt": datetime.datetime.now().isoformat(timespec='seconds')})
            model.update()

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

    def _upload_model_annotations(self, item: entities.Item, predictions, cleanup=False):
        """
        Utility function that upload prediction to dlp platform based on the package.output_type
        :param predictions: `dl.AnnotationCollection`
        :param cleanup: `bool` if set removes existing predictions with the same package-model name
        """
        if not isinstance(predictions, entities.AnnotationCollection):
            raise TypeError('predictions was expected to be of type {}, but instead it is {}'.
                            format(entities.AnnotationCollection, type(predictions)))
        model_info_name = "{}-{}".format(self.package_name, self.model_entity.name)
        if cleanup:
            clean_filter = entities.Filters(field='type',
                                            values=self.model_entity.output_type,
                                            resource=entities.FiltersResource.ANNOTATION)
            clean_filter.add(field='metadata.user.model.name', values=model_info_name)
            item.annotations.delete(filters=clean_filter)
        annotations = item.annotations.upload(annotations=predictions)
        return annotations

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
