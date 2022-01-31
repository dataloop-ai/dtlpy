import itertools
import datetime
import logging
import shutil
import tqdm
import time
import tempfile
import os
from PIL import Image
import numpy as np
from collections import namedtuple

from .. import entities, exceptions, dtlpy_services

logger = logging.getLogger('dtlpy')


class BaseModelAdapter:
    configuration = {
        'label_map': None,  # {'label_name' : `int`, ...}
    }

    def __init__(self, model_entity):
        if not isinstance(model_entity, entities.Model):
            raise TypeError("model_entity must be of type dl.Model")

        self.model_name = model_entity.name
        # entities
        self._model_entity = model_entity  # TODO: change to dlp_model
        self._snapshot = None
        self.model = None
        self.bucket_path = None
        self.logger = logger

    ############
    # Entities #
    ############
    @property
    def snapshot(self):
        if self._snapshot is None:
            raise ValueError('Missing snapshot on adapter. please set: "adapter.snapshot=snapshot"')
        assert isinstance(self._snapshot, entities.Snapshot)
        return self._snapshot

    @snapshot.setter
    def snapshot(self, snapshot):
        assert isinstance(snapshot, entities.Snapshot)
        if self._snapshot is not None:
            if self._snapshot.id != snapshot.id:
                self.logger.warning('Replacing snapshot from {!r} to {!r}'.format(self._snapshot.name, snapshot.name))
        self._snapshot = snapshot

    @property
    def model_entity(self):
        if self._model_entity is None:
            raise ValueError('Missing Model entity on adapter. please set: "adapter.model_entity=dl.Model"')
        assert isinstance(self._model_entity, entities.Model)
        return self._model_entity

    @model_entity.setter
    def model_entity(self, val):
        assert isinstance(val, entities.Snapshot)
        self._model_entity = val

    ###################################
    # NEED TO IMPLEMENT THESE METHODS #
    ###################################

    def load(self, local_path, **kwargs):
        """ Loads model and populates self.model with a `runnable` model

            Virtual method - need to implement

            This function is called by load_from_snapshot (download to local and then loads)

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'load' method in {}".format(self.__class__.__name__))

    def save(self, local_path, **kwargs):
        """ saves configuration and weights locally

            Virtual method - need to implement

            the function is called in save_to_snapshot which first save locally and then uploads to snapshot entity

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

    def prepare_training(self,
                         # paths
                         root_path=None,
                         data_path=None,
                         output_path=None,
                         #
                         partitions=None,
                         filters=None,
                         **kwargs):
        """
        Prepares dataset locally before training.
        download the specific partition selected to data_path and preforms `self.convert` to the data_path dir

        :param root_path: `str` root directory for training. default is "tmp"
        :param data_path: `str` dataset directory. default <root_path>/"data"
        :param output_path: `str` save everything to this folder. default <root_path>/"output"

        :param partitions: `dl.SnapshotPartitionType` or list of partitions, defaults for all partitions
        :param dtlpy.entities.filters.Filters filters: `dl.Filter` in order to select only part of the data
        """
        if partitions is None:
            partitions = list(entities.SnapshotPartitionType)
        if isinstance(partitions, str):
            partitions = [partitions]

        # define paths
        dataloop_path = os.path.join(os.path.expanduser('~'), '.dataloop')
        if root_path is None:
            now = datetime.datetime.now()
            root_path = os.path.join(dataloop_path,
                                     'training',
                                     "{s_id}_{s_n}".format(s_id=self.snapshot.id, s_n=self.snapshot.name),
                                     now.strftime('%Y-%m-%d-%H%M%S'),
                                     )
        if data_path is None:
            data_path = os.path.join(dataloop_path, 'datasets', self.snapshot.dataset.id)
            os.makedirs(data_path, exist_ok=True)
        if output_path is None:
            output_path = os.path.join(root_path, 'output')
            os.makedirs(output_path, exist_ok=True)

        # Make sure snapshot.dataset has partitions
        has_partitions = self.snapshot.get_partitions(list(entities.SnapshotPartitionType)).items_count > 0
        if not has_partitions:  # set the partitions
            raise ValueError('must create train and test partitions for snapshot {!r} / dataset {!r}'.
                             format(self.snapshot.id, self.snapshot.dataset.id))

        if len(os.listdir(data_path)) > 0:
            self.logger.warning("Data path directory ({}) is not empty..".format(data_path))

        annotation_options = entities.ViewAnnotationOptions.JSON
        if self.model_entity.output_type in [entities.AnnotationType.SEGMENTATION]:
            annotation_options = entities.ViewAnnotationOptions.INSTANCE

        # Download the partitions items
        for partition in partitions:
            self.logger.debug("Downloading {!r} SnapshotPartition (DataPartition) of {}".format(partition.value,
                                                                                                self.snapshot.dataset.name))
            data_partiion_base_path = os.path.join(data_path, partition)
            ret_list = self.snapshot.download_partition(partition=partition,
                                                        local_path=data_partiion_base_path,
                                                        annotation_options=annotation_options,
                                                        filters=filters)
            self.logger.info("Downloaded {!r} SnapshotPartition complete. {} total items".format(partition.value,
                                                                                                 len(list(ret_list))))

        self.convert_from_dtlpy(data_path=data_path, **kwargs)
        return root_path, data_path, output_path

    def load_from_snapshot(self, snapshot, local_path=None, **kwargs):
        """ Loads a model from given `snapshot`.
            Reads configurations and instantiate self.snapshot
            Downloads the snapshot bucket (if available)

        :param snapshot:  `str` dl.Snapshot entity
        :param local_path:  `str` directory path in local FileSystem to download the snapshot to
        :param overwrite: `bool` (default False) if False does not downloads files with same name else (True) download all
        """
        overwrite = kwargs.get('overwrite', False)
        self.snapshot = snapshot
        if local_path is None:
            local_path = os.path.join(dtlpy_services.service_defaults.DATALOOP_PATH, "snapshots", self.snapshot.name)
        # update adapter instance
        self.configuration.update(snapshot.configuration)
        # Download
        if self.snapshot.bucket.is_remote:
            self.logger.debug("Found a remote bucket - downloading to: {!r}".format(local_path))
            self.snapshot.download_from_bucket(local_path=local_path,
                                               overwrite=overwrite)
            self.configuration.update({'bucket_path': local_path})
        else:
            self.logger.debug("Local bucket - making sure bucket.local path and argument local path - match")
            self.configuration.update({'bucket_path': self.snapshot.bucket.local_path})
            os.makedirs(self.snapshot.bucket.local_path, exist_ok=True)
            if os.path.realpath(local_path) != os.path.realpath(self.snapshot.bucket.local_path):
                raise OSError('given local_path {!r} is different from the localBucket path: {!r}'.
                              format(local_path, self.snapshot.bucket.local_path))
            # local_path = bucket.local_path
        self.load(local_path, **kwargs)

    def save_to_snapshot(self, local_path=None, cleanup=False, replace=True, **kwargs):
        """
            saves the model state to a new bucket and configuration

            Saves configuration and weights to new snapshot bucket
            Mark the snapshot as `trained`
            loads only applies for remote buckets

        :param local_path: `str` directory path in local FileSystem to save the current model bucket (weights) (default will create a temp dir)
        :param replace: `bool` will clean the bucket's content before uploading new files
        :param cleanup: `bool` if True (default) remove the data from local FileSystem after upload
        :return:
        """
        if local_path is None:
            local_path = tempfile.mkdtemp(prefix="snapshot_" + self.snapshot.name)
            self.logger.debug("Using temporary dir at {}".format(local_path))

        self.save(local_path=local_path, **kwargs)

        if self.snapshot is None:
            raise ValueError('missing snapshot entity on the adapter. '
                             'please set one before saving: "adapter.snapshot=snapshot"')

        if replace:
            self.snapshot.bucket.empty_bucket(sure=replace)
        self.snapshot.bucket.upload(local_path=local_path,
                                    overwrite=True,
                                    file_types=kwargs.get('file_types'))
        if cleanup:
            shutil.rmtree(path=local_path, ignore_errors=True)
            self.logger.info("Clean-up. deleting {}".format(local_path))
        self.snapshot.status = 'trained'
        self.snapshot.configuration = self.configuration
        self.snapshot = self.snapshot.update()

    def predict_items(self, items: list, with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image

        :return: `List[dl.AnnotationCollection]` where all annotation in the collection are of type model.output_type
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
                # Make sure user created right prediction types
                if not all(
                        [pred.type == self.model_entity.output_type for pred in itertools.chain(*all_predictions)]):
                    raise RuntimeError("Predictions annotation are not of model output type")
                for idx, item in enumerate(items):
                    all_predictions[idx] = self._upload_predictions_collection(item,
                                                                               all_predictions[idx],
                                                                               cleanup=cleanup)

            except exceptions.InternalServerError as err:
                self.logger.error("Failed to upload annotations items. Error: {}".format(err))

            self.logger.debug('Uploading  items annotation for snapshot {!r}. cleanup {}'.format(self.snapshot.name,
                                                                                                 cleanup))
        else:
            # fix the collection to have to correct item in the annotations
            for item, ann_coll in zip(items, all_predictions):
                for ann in ann_coll:
                    ann._item = item
                ann_coll.item = item
        return all_predictions

    def create_metrics(self, snapshot, partition='validation', predict=False, **kwargs):
        """ create predictions and calculates performance metrics

        :param snapshot: `dl.Snapshot` entity
        :param partition:  `str` snapshot_partition to preform metrics on
        :param predict: `bool` if given the function also preforms the predictions
        """

        self.snapshot = snapshot
        dataset = snapshot.dataset
        prd_filters = entities.Filters(field='annotationType',
                                       values='prediction',
                                       resource=entities.FiltersResource.ANNOTATION)
        prd_filters.add(field='type', values=self.model_entity.output_type)
        act_filters = entities.Filters(field='annotationType',
                                       values='actual',
                                       resource=entities.FiltersResource.ANNOTATION)
        act_filters.add(field='type', values=self.model_entity.output_type)

        items = list(itertools.chain(*snapshot.get_partitions(partitions=partition, filters=None)))
        if predict:
            predictions = self.predict_items(items=items, with_upload=True, **kwargs)
        results = []
        for item in items:
            prediction_annotations = item.annotations.list(filters=prd_filters)
            actual_annotations = item.annotations.list(filters=act_filters)

            for gt in actual_annotations:
                if self.model_entity.output_type == 'box':
                    # Consider uploading IoU per each annotation
                    best_match = self._box_compare(act=gt, predictions=prediction_annotations)
                elif self.model_entity.output_type == 'class':
                    self._class_compare(item, act=gt, pred=prediction_annotations)
                else:
                    # other methods are not supported
                    raise NotImplementedError(
                        "metrics for output type {} is not yet implemented".format(self.model_entity.output_type))
            results.append(best_match.score)  # change to items metric
        snapshot.add_metrics(results)

    # =============
    # INNER METHODS
    # =============

    def _upload_predictions_collection(self, item: entities.Item, predictions, cleanup=False):
        """
        Utility function that upload prediction to dlp platform based on the model.output_type
        :param predictions: `dl.AnnotationCollection`
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name
        """
        if not isinstance(predictions, entities.AnnotationCollection):
            raise TypeError('predictions was expected to be of type {}, but instead it is {}'.
                            format(entities.AnnotationCollection, type(predictions)))
        model_info_name = "{}-{}".format(self.model_name, self.snapshot.name)
        if cleanup:
            clean_filter = entities.Filters(field='type',
                                            values=self.model_entity.output_type,
                                            resource=entities.FiltersResource.ANNOTATION)
            clean_filter.add(field='metadata.user.model.name', values=model_info_name)
            item.annotations.delete(filters=clean_filter)

        return item.annotations.upload(annotations=predictions)

    def _box_compare(self, act: entities.Annotation, predictions):
        """ Calculates best matched  prediction to a single gt. Returns namedTuple (score, prd_id)"""
        # move our metrics method from fonda to dtlpy
        bestMatch = namedtuple('best_match', field_names=['score', 'iou'])
        best = bestMatch(0, None)
        for prd in predictions:
            score = act.x[0] - prd.x[1]
            if score > best.score:
                best = bestMatch(score, prd.id)
        return bestMatch

    def _class_compare(self, item, act, pred):
        _sample = self._sample_metric_base
        _sample.update({
            'frozen_itemId': item.id,
            'prediction_label': pred.label,
            'acutal_label': act.label,
            'prediction_id': pred.id,
            'acutal_id': act.id,
        })
        self.snapshot.project.times_series.add_samples(_sample)

    @property
    def _sample_metric_base(self):
        _sample = {
            'snapshotId': self.snapshot.id,
            'output_type': self.model.output_type,
            'frozen_datasetId': self.snapshot.dataset_id,
        }
        return _sample

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
