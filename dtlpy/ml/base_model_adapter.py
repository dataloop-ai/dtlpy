import os
import shutil
import datetime
import logging
import tqdm
from collections import namedtuple
from contextlib import contextmanager
import warnings

from .. import entities, exceptions

logger = logging.getLogger(__name__)


class BaseModelAdapter:
    BoxPrediction = namedtuple('box_prediction', field_names=['top', 'left', 'bottom', 'right', 'label', 'score'])
    ClassPrediction = namedtuple('classification_prediction', field_names=['label', 'score'])

    _defaults = {'label_map': None,  # {'label_name' : `int`, ...}
                 }

    def __init__(self, model_entity, log_Level='INFO'):
        if not isinstance(model_entity, entities.Model):
            raise TypeError("model_entity must be of type dl.Model")

        self.model_name = model_entity.name
        self.model_entity = model_entity  # TODO: change to dlp_model
        self.model = None
        self.snapshot = None
        self.bucket_path = None
        self.logger = logger
        self.__dict__.update(self._defaults)  # set up default values

        self.__add_adapter_handler(level=log_Level)

    # ===============================
    # NEED TO IMPLEMENT THESE METHODS
    # ===============================

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

    def train(self, data_path, dump_path, **kwargs):
        """ Train the model according to data in local_path and save the snapshot to dump_path

            Virtual method - need to implement
        :param data_path: `str` local File System path to where the data was downloaded and converted at
        :param dump_path: `str` local File System path where to dump training mid-results (checkpoints, logs...)
        """
        raise NotImplementedError("Please implement 'train' method in {}".format(self.__class__.__name__))

    def predict(self, batch, **kwargs):
        """ Model inference (predictions) on batch of images

            Virtual method - need to implement

        :param batch: `np.ndarray`
        :return: `list[dl.AnnotationCollection]` each collection is per each image / item in the batch
        """
        raise NotImplementedError("Please implement 'predict' method in {}".format(self.__class__.__name__))

    def convert(self, data_path, **kwargs):
        """ Convert Dataloop structure data to model structured

            Virtual method - need to implement

            e.g. take dlp dir structure and construct annotation file

        :param data_path: `str` local File System directory path where we already downloaded the data from dataloop platform
        :return:
        """
        raise NotImplementedError("Please implement 'convert' method in {}".format(self.__class__.__name__))

    def convert_dlp(self, items: entities.PagedEntities):
        """ This should implement similar to convert only to work on dlp items.
                -> meaning create the converted version from items entities
        """
        # TODO
        pass

    # =============
    # DTLPY METHODS
    # =============

    def load_from_snapshot(self, local_path, snapshot_id, **kwargs):
        """ Loads a model from given `snapshot`.
            Reads configurations and instantiate self.snapshot
            Downloads the snapshot bucket (if available)

        :param local_path:  `str` directory path in local FileSystem to download the snapshot to
        :param snapshot_id:  `str` snapshot id
        """
        snapshot = self._snapshot_getter_setter(snapshot_id=snapshot_id)
        config = snapshot.configuration
        # Download
        if snapshot.bucket.is_remote:
            self.logger.debug("Found a remote bucket - downloading to: {!r}".format(local_path))
            snapshot.download_from_bucket(local_path=local_path)  # Partially supported (for itemBucket and GcsBucket)
            config.update({'bucket_path': local_path})
        else:
            self.logger.debug("Local bucket - making sure bucket.local path and argument local path - match")
            config.update({'bucket_path': snapshot.bucket.local_path})
            os.makedirs(snapshot.bucket.local_path, exist_ok=True)
            if os.path.realpath(local_path) != os.path.realpath(snapshot.bucket.local_path):
                raise OSError('given local_path {!r} is different from the localBucket path: {!r}'.
                              format(local_path, snapshot.bucket.local_path))
            # local_path = bucket.local_path

        # update adapter instance
        self.__dict__.update(config)  # update attributes with user overrides
        self.load(local_path, **kwargs)

    def save_to_snapshot(self, local_path, snapshot_name=None, description=None, cleanup=False, **kwargs):
        """
            saves the model state to a new bucket and configuration

            Saves configuration and weights to new snapshot bucket
            loads only applies for remote buckets

        :param local_path: `str` directory path in local FileSystem to save the current model bucket (weights)
        :param snapshot_name: `str` name for the new snapshot
        :param description:  `str` description for the new snapshot
        :param cleanup: `bool` if True (default) remove the data from local FileSystem after upload
        :return:
        """
        self.save(local_path=local_path, **kwargs)
        replaced = False  # did we replaced self.snapshot

        if self.snapshot is None:
            logger.warning("No active snapshot creating a new snapshot {!r} with a local bucket".format(snapshot_name))
            new_local_bucket = self.model_entity.buckets.create(bucket_type=entities.BucketType.ITEM,
                                                                local_path=local_path)
            self.snapshot = self.model_entity.snapshots.create(snapshot_name=snapshot_name,
                                                               bucket=new_local_bucket,
                                                               description=description)
            replaced = True
        else:
            new_bucket = self.snapshot.buckets.create(bucket_type=self.snapshot.bucket.type,
                                                      # TODO: for GCS bucket there are more configurations
                                                      local_path=local_path,
                                                      # TODO: use item_bucket options if they are given
                                                      # item_bucket_snapshot_name=snapshot_name
                                                      )
            if snapshot_name is None or snapshot_name == self.snapshot.name:
                # ==> use existing snapshot (replace the bucket)
                self.snapshot.bucket = new_bucket
                replaced = False
            else:  # snapshot_name != self.snapshot.name
                #   ==> Create a new snapshot
                logger.warning("Replacing snapshot {!r} by new created snapshot {!r}".
                               format(self.snapshot.name, snapshot_name))

                new_snapshot = self.snapshot.clone(snapshot_name=snapshot_name, new_bucket=new_bucket)
                self.snapshot = new_snapshot
                replaced = True
            if description is not None:
                self.snapshot.description = description

        # update existing configuration
        new_config = {key: getattr(self, key) for key in self._defaults.keys()}
        self.snapshot.configuration.update(new_config)
        self.snapshot.configuration.update({'trainedAt': datetime.datetime.utcnow().isoformat(timespec='minutes')})
        self.snapshot.status = 'trained'
        self.snapshot = self.snapshot.update()

        if replaced:
            logger.warning("Adapter snapshot was replaced by another snapshot. ({!r})".format(self.snapshot.id))

        if cleanup:
            shutil.rmtree(path=local_path, ignore_errors=True)
            logger.info("Clean-up. deleting {}".format(local_path))

    def prepare_trainset(self, data_path, partitions=None, filters=None, **kwargs):
        """
        Prepares train set for train.
        download the specific partition selected to data_path and preforms `self.convert` to the data_path dir

        :param data_path: `str` directory path to use as the root to the data from Dataloop platform
        :param partitions: `dl.SnapshotPartitionType` or list of partitions, defaults for all partitions
        :param filters: `dl.Filter` in order to select only part of the data
        """
        if partitions is None:
            partitions = list(entities.SnapshotPartitionType)
        if isinstance(partitions, str):
            partitions = [partitions]

        # Make sure snapshot.dataset has partitions
        has_partitions = self.snapshot.get_partitions(list(entities.SnapshotPartitionType)).items_count > 0
        if not has_partitions:  # set the partitions
            train_split = kwargs.get('train_split', None)
            val_split = kwargs.get('val_split', None)
            test_split = kwargs.get('test_split', 0.0)

            # split smartly if not all splits are valid
            if train_split is None and val_split is None:
                train_split, val_split = 0.7 * (1 - test_split), 0.3 * (1 - test_split)
            elif train_split is None:
                train_split = 1 - test_split - val_split
            else:
                val_split = 1 - test_split - train_split

            self._create_partitions(train_split=train_split, val_split=val_split, test_split=test_split)

        os.makedirs(data_path, exist_ok=True)
        if len(os.listdir(data_path)) > 0:
            self.logger.warning("Data path directory ({}) is not empty..".format(data_path))

        # Download the partitions items
        for partition in partitions:
            self.logger.debug("Downloading {!r} SnapshotPartition (DataPartition) of {}".format(partition,
                                                                                                self.snapshot.dataset.name))
            ret_list = self.snapshot.download_partition(partition=partition, local_path=data_path, filters=filters)
            self.logger.info(
                "Downloaded {!r} SnapshotPartition complete. {} total items".format(partition, len(ret_list)))

            if partition == entities.SnapshotPartitionType.TEST:
                self.num_test = len(ret_list)
            elif partition == entities.SnapshotPartitionType.VALIDATION:
                self.num_val = len(ret_list)
            elif partition == entities.SnapshotPartitionType.TRAIN:
                self.num_train = len(ret_list)

        # Convert items; json to one annotation file
        self.convert(data_path=data_path, **kwargs)

    # TODO: do we need predict by single partitions?
    #   currently we can't preform on PagedEntity which we get from get_partition
    # TODO: what to do with readonly dataset? unlock it?
    def predict_from_snapshot(self, filters=None, snapshot_id=None, with_upload=True, **kwargs):
        """
        Predicts all items in snapshot using filers

        :param filters: `dl.Filters` to narrow the search
        :param snapshot_id: `str` optional, if not given, uses self.snapshot
        :param with_upload: `bool` uploads the predictions back to the given items
        :return: `List[Prediction]' `Prediction is set by model.output_type
        """
        snapshot = self._snapshot_getter_setter(snapshot_id=snapshot_id, replace=kwargs.get('replace', False))
        # items_list = [item for item in snapshot.get_partitions(partitions=partitions, filters=filters).all()] # TODO: test if pre-allocation is faster?

        # un-freeze the dataset when preforming on snapshot operations
        with self._frozen_dataset(self.snapshot) as ds:
            items_list = ds.items.get_all_items(filters=filters)
            predictions = self.predict_items(items=items_list, with_upload=with_upload, cleanup=True, **kwargs)

        return predictions

    def predict_items(self, items: list, with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image
        :return: `List[dl.AnnotationCollection]' where all annotation in the collection are of type model.output_type
                                                 and has prediction fields (model_info)
        """
        # TODO: do we want to add score filtering here?
        import itertools
        from PIL import Image
        import numpy as np

        logger.debug(
            "Predicting {} items, using batch size {}. Reshaping to: {}".format(len(items), batch_size, output_shape))
        all_predictions = []
        for b in tqdm.tqdm(range(0, len(items), batch_size), desc='predicting', unit='bt', leave=None):
            batch = []
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
                # test if we use the newer AnnotaionCollection by the first item predictions
                if isinstance(all_predictions[0], entities.AnnotationCollection):
                    # Make sure user created right prediction types
                    if not all(
                            [pred.type == self.model_entity.output_type for pred in itertools.chain(*all_predictions)]):
                        raise RuntimeError("Predictions annotation are not of model output type")
                    for idx, item in enumerate(items):
                        self._upload_predictions_collection(item, all_predictions[idx], cleanup=cleanup)
                else:
                    warnings.warn("Deprecated function. You should create predictions as a dl.AnnotationsCollection")
                    # Make sure user created right prediction types
                    if self.model_entity.output_type == 'box' and \
                            not all(
                                [isinstance(pred, self.BoxPrediction) for pred in itertools.chain(*all_predictions)]):
                        raise RuntimeError("Expected all prediction to be of type BaseModelAdapter.BoxPrediction")
                    if self.model_entity.output_type == 'class' and \
                            not all(
                                [isinstance(pred, self.ClassPrediction) for pred in itertools.chain(*all_predictions)]):
                        raise RuntimeError("Expected all prediction to be of type BaseModelAdapter.ClassPrediction")
                    for idx, item in enumerate(items):
                        self._upload_predictions(item, all_predictions[idx], cleanup=cleanup)

            except exceptions.InternalServerError as err:
                self.logger.error("Failed to upload annotations items. Error: {}".format(err))

            self.logger.info('Uploading  items annotation for snapshot {!r}. cleanup {}'.
                             format(self.snapshot.name, cleanup))
        return all_predictions

    def create_metrics(self, snapshot_id, partition='validation', predict=False, **kwargs):
        """ create predictions and calculates performance metrics

        :param snapshot_id: `str` snapshot id to use
        :param partition:  `str` snapshot_partition to preform metrics on
        :param predict: `bool` if given the function also preforms the predictions
        """

        import itertools
        snapshot = self._snapshot_getter_setter(snapshot_id=snapshot_id)
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
                    self._class_compare(self, item, act=gt, pred=prediction_annotations)
                else:
                    # other methods are not supported
                    raise NotImplementedError(
                        "metrics for output type {} is not yet implemented".format(self.model_entity.output_type))
            results.append(best_match.score)  # change to items metric
        snapshot.add_metrics(results)

    # =============
    # INNER METHODS
    # =============
    def _upload_predictions(self, item, predictions, cleanup=False):
        """
        Utility function that upload prediction to dlp platform based on the model.output_type
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name
        """
        model_info_name = "{}-{}".format(self.model_name, self.snapshot.name)
        if cleanup:
            clean_filter = entities.Filters(field='type',
                                            values=self.model_entity.output_type,
                                            resource=entities.FiltersResource.ANNOTATION)
            clean_filter.add(field='metadata.user.model.name', values=model_info_name)
            item.annotations.delete(filters=clean_filter)

        if self.model_entity.output_type == 'box':
            builder = item.annotations.builder()
            for pred in predictions:
                builder.add(annotation_definition=entities.Box(
                    top=float(pred.top), left=float(pred.left), bottom=float(pred.bottom),
                    right=float(pred.right), label=str(pred.label)),
                    model_info={'name': model_info_name,
                                'confidence': float(pred.score)})

            item.annotations.upload(annotations=builder)
        elif self.model_entity.output_type == 'class':
            builder = item.annotations.builder()
            for pred in predictions:
                builder.add(annotation_definition=entities.Classification(label=pred.label),
                            model_info={'name': model_info_name,
                                        'confidence': float(pred.score)})
            item.annotations.upload(annotations=builder)
        else:
            raise NotImplementedError('model output type: {} is not supported to upload to platform'.
                                      format(self.model_entity.output_type))

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

        item.annotations.upload(annotations=predictions)

    def _box_compare(self, act: entities.Annotation, predictions):
        """ Calculates best matched  prediction to a single gt. Returns namedTuple (score, prd_id)"""
        # move our metircs method from fonda to dtlpy
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
            'snapshotId': self.id,
            'output_type': self.model.output_type,
            'frozen_datasetId': self.dataset.id,
        }
        return _sample

    def _create_partitions(self, train_split=0.7, val_split=0.3, test_split=0.0):
        """ Updates partitions on the current items by the splits ratios"""
        import time
        import numpy as np

        self.logger.info("Creating data partition for {!r} snapshot: splits: [Train-Val-Test {:1.2f}-{:1.2f}-{:1.2f}]".
                         format(self.snapshot.name, train_split, val_split, test_split))
        if round(train_split + val_split + test_split) != 1:
            raise RuntimeError(
                'Splits should sum up to 1 (train {}; val {}; test{})'.format(train_split, val_split, test_split))

        all_item_ids = [item.id for item in self.snapshot.dataset.items.get_all_items()]
        num_items = len(all_item_ids)

        np.random.seed(round(time.time()))
        np.random.shuffle(all_item_ids)
        self.num_test = round(num_items * test_split)
        self.num_val = round(num_items * val_split)
        self.num_train = num_items - self.num_val - self.num_test  # To avoid roundups

        # split the list by number per partition
        test_item_ids = all_item_ids[:self.num_test]
        val_item_ids = all_item_ids[self.num_test:self.num_test + self.num_val]
        train_item_ids = all_item_ids[self.num_test + self.num_val:]

        # update items to their partition
        with self._frozen_dataset(self.snapshot) as ds:
            op = entities.FiltersOperations.IN
            ds.set_partition(partition=entities.SnapshotPartitionType.TEST,
                             filters=entities.Filters(field='id', values=test_item_ids, operator=op))
            ds.set_partition(partition=entities.SnapshotPartitionType.VALIDATION,
                             filters=entities.Filters(field='id', values=val_item_ids, operator=op))
            ds.set_partition(partition=entities.SnapshotPartitionType.TRAIN,
                             filters=entities.Filters(field='id', values=train_item_ids, operator=op))

        self.logger.info("Data Partition Ended. Dataset {!r} has: {} training, {} validation and {} test items".
                         format(self.snapshot.dataset.name, self.num_train, self.num_val, self.num_test))

    # =======
    # Utility
    # =======

    @contextmanager
    def _frozen_dataset(self, obj):
        try:
            if isinstance(obj, entities.Snapshot):
                dataset = obj.dataset
            elif isinstance(obj, entities.Dataset):
                dataset = obj
            else:
                raise NotImplementedError("could not get a dataset")
            _readonly_state = dataset.readonly
            dataset.set_readonly(False)
            self.logger.debug("dataset {!r} - opned for edit".format(dataset.name))
            yield dataset
        finally:
            dataset.set_readonly(_readonly_state)
            self.logger.debug(
                "free frozen context ended. dataset {!r}, readonly was set back to: {}".format(dataset.name,
                                                                                               dataset.readonly))

    def _snapshot_getter_setter(self, snapshot_id=None, snapshot_name=None, replace=False):
        """
        Utility function that retuns the active snapshot
        if self.snapshot is None or if `replace` is set - the function alson assigns a new snapshot

        :param snapshot_id: `str` optional snapshot_id to use
        :param snapshot_name: `str` optional snapshot_name to use
        NOTE: only one of id / name may be given
        :param replace: `bool` what to do in case the id_name is different from the current self.snapshot
                default (False) ignores the id/name and retuns the current snapshot
        :return:
        """

        if snapshot_name is not None and snapshot_id is not None:
            raise NotImplementedError('cannot work with both id and name args')

        if snapshot_id is not None:
            snapshot = self.model_entity.snapshots.get(snapshot_id=snapshot_id)
            if self.snapshot is None:
                self.snapshot = snapshot
                return snapshot
            else:
                if snapshot.id == self.snapshot.id:
                    return snapshot
                elif replace:
                    logger.warning("Replacing snapshot")
                    self.snapshot = snapshot
                    return snapshot
                else:
                    return self.snapshot

        elif snapshot_name is not None:
            snapshot = self.model_entity.snapshots.get(snapshot_name=snapshot_name)
            if self.snapshot is None:
                self.snapshot = snapshot
                return snapshot
            else:
                if snapshot.id == self.snapshot.id:
                    return snapshot
                elif replace:
                    logger.warning("Replacing snapshot")
                    self.snapshot = snapshot
                    return snapshot
                else:
                    return self.snapshot
        else:
            # No new arg. use current snapshot
            return self.snapshot

        # if id_or_name:
        #     try:
        #         snapshot = self.model_entity.snapshots.get(snapshot_id=id_or_name)
        #     except exceptions.NotFound as e:
        #         snapshot = self.model_entity.snapshots.get(snapshot_name=id_or_name)

    def __set_adapter_handler__(self, level):
        for hdl in self.logger.handlers:
            if hdl.name.startswith('adapter'):
                hdl.setLevel(level=level)

    def __add_adapter_handler(self, level):
        fmt = '%(levelname).1s: %(name)-20s %(asctime)-s [%(filename)-s:%(lineno)-d](%(funcName)-s):: %(msg)s'
        hdl = logging.StreamHandler()
        hdl.setFormatter(logging.Formatter(fmt=fmt, datefmt='%X'))
        hdl.setLevel(level=level.upper())
        hdl.name = 'adapter_handler'  # use the name to get the specific logger
        if hdl.name in [h.name for h in self.logger.handlers]:
            pass  # Handler already on logger
        else:
            self.logger.addHandler(hdlr=hdl)

    @staticmethod
    def _np_resize_util(images, output_shape):
        try:
            import numpy as np
            from skimage.transform import resize
        except (ImportError, ModuleNotFoundError) as err:
            raise RuntimeError('dtlpy depends on external package. Please install ') from err
        if isinstance(images, np.ndarray) and len(images.shape) < 4:
            # Single image
            return resize(images, output_shape=output_shape)
        batch_reshape = []
        for img in images:
            batch_reshape.append(resize(img, output_shape=output_shape))
        # construct as batch and return
        return np.array(batch_reshape)

    # ==========================
    # Callback Factory functions
    # ==========================
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
