import os
import shutil
import logging
import tqdm
from collections import namedtuple
from contextlib import contextmanager

from .. import entities

logger = logging.getLogger(__name__)


class BaseModelAdapter():
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

    def train(self, local_path, dump_path, **kwargs):
        """ Train the model according to data in local_path and save the snapshot to dump_path

            Virtual method - need to implement
        """
        raise NotImplementedError("Please implement 'train' method in {}".format(self.__class__.__name__))

    def predict(self, batch, **kwargs):
        """ Model inference (predictions) on batch of images

            Virtual method - need to implement

        :param batch: `np.ndarray`
        :return: `list[self.BoxPrediction]`  prediction results by len(batch)
        """
        raise NotImplementedError("Please implement 'predict' method in {}".format(self.__class__.__name__))

    def convert(self, local_path, **kwargs):
        """ Convert Dataloop structure data to model structured

            Virtual method - need to implement

            e.g. take dlp dir structure and construct annotation file

        :param local_path: `str` local File System directory path where we already downloaded the data from dataloop platform
        :return:
        """
        raise NotImplementedError("Please implement 'convert' method in {}".format(self.__class__.__name__))

    def convert_dlp(self, items: entities.PagedEntities):
        """ This should implement similar to convert only to work on dlp items.  -> meaning create the converted version from items entities"""
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
            snapshot.download_from_bucket(local_path=local_path)  # Not supported yet - only for item codebase
            config.update({'bucket_path': local_path})
        else:
            config.update({'bucket_path': snapshot.bucket.local_path})
            # local_path = bucket.local_path

        # update adapter instance
        self.__dict__.update(config)  # update attributes with user overrides
        self.load(local_path, **kwargs)

    def save_to_snapshot(self, local_path, snapshot_name=None, description=None, cleanup=False, **kwargs):
        """ Saves configuration and weights to new snapshot bucket
            loads only applies for remote buckets

        :param local_path: `str` directory path in local FileSystem
        :param snapshot_name: `str` name for the new snapshot
        :param description:  `str` description for the new snapshot
        :param cleanup: `bool` if True (default) remove the data from local FileSystem after upload
        :return:
        """
        self.save(local_path=local_path, **kwargs)
        replaced = False

        if self.snapshot is None:
            logger.warning("No active snapshot creating new one {!r}".format(snapshot_name))
            self.snapshot = self.model_entity.snapshots.create(snapshot_name=snapshot_name,
                                                               description=description)
            if self.snapshot.bucket.type == entities.BucketType.LOCAL \
                    and local_path != self.snapshot.bucket.local_path:
                # ==> Create new bucket
                replaced = True
        else:
            if snapshot_name is not None and snapshot_name != self.snapshot.name:
                #   ==> Create a new snapshot
                logger.warning(
                    "Replacing snapshot {!r} by new created snapshot {!r}".format(self.snapshot.name, snapshot_name))
                self.snapshot = self.model_entity.snapshots.create(snapshot_name=snapshot_name,
                                                                   description=description)
                replaced = True

        # update existing configuration
        config = {key: getattr(self, key) for key in self._defaults.keys()}
        self.snapshot.configuration.update(config)

        # update the bucket
        if self.snapshot.bucket.type == entities.BucketType.ITEM:
            # TODO: test the upload_to_bucket also works for the first push...
            self.snapshot.upload_to_bucket(local_path=local_path, overwrite=True)
        else:  # Local bucket
            if replaced:
                self.snapshot.bucket = entities.LocalBucket(local_path=local_path)
                self.snapshot = self.snapshot.update()

        # TODO: what about the option we give different local path than th current local_bucket
        #       do we want to override current bucket or just create new local and replce?

        if cleanup:
            shutil.rmtree(path=local_path, ignore_errors=True)
            logger.info("Clean-up. deleting {}".format(local_path))

    def prepare_trainset(self, data_path, partitions=None, filters=None, **kwargs):
        """
        Prepares train set for train.
        download the specific partition selected to data_path and preforms `self.convert` to the data_paht dir

        :param data_path: `str` directory path to use as the root to the data from Dataloop platform
        :param partitions: `dl.SnapshotPratitionType` or list of partitions, defaults for all partitions
        :param filters: `dl.Filter` in order to select only part of the data
        :param has_partitions: `bool` specifing if the dataset allready has partition defined or we can set them during the run
        """
        if partitions is None:
            partitions = list(entities.SnapshotPartitionType)
        if isinstance(partitions, str):
            partitions = [partitions]

        # Make sure snapshot.dataset has partitions
        has_partitions = self.snapshot.get_partitions(list(entities.SnapshotPartitionType)).items_count > 0
        if not has_partitions:
            # TODO: dynamically choose the splits
            self._create_partitions(**kwargs) # train_split=0.7, val_split=0.3, test_split=0.0)  # set the partitions
            # set the partition

        os.makedirs(data_path, exist_ok=True)
        if len(os.listdir(data_path)) > 0:
            self.logger.warning("Data path directory ({}) is not empty..".format(data_path))

        # Download the partitions items
        for partition in partitions:
            self.logger.debug("Downloading {} of {}".format(partition, self.snapshot.dataset.name))
            ret_list = self.snapshot.download_partition(partition=partition, local_path=data_path, filters=filters)

            if partition == entities.SnapshotPartitionType.TEST:
                self.num_test = len(ret_list)
            elif partition == entities.SnapshotPartitionType.VALIDATION:
                self.num_val = len(ret_list)
            elif partition == entities.SnapshotPartitionType.TRAIN:
                self.num_train = len(ret_list)

        # Convert items; json to one annotation file
        self.convert(local_path=data_path, **kwargs)

    # TODO: do we need predict by single partitons?  currently we cann't preform on PagedEntity which we get from get_partition
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
        items_list = snapshot.dataset.items.get_all_items(filters=filters)
        return self.predict_items(items=items_list, with_upload=with_upload, **kwargs)

    def predict_items(self, items: list, with_upload=True, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :return: `List[Prediction]' `Prediction is set by model.output_type
        """
        import itertools
        from PIL import Image
        import numpy as np

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
            # Make sure user created right prediction boxes
            if self.model_entity.output_type == 'box' and\
                    not all([isinstance(pred, self.BoxPrediction) for pred in itertools.chain(*all_predictions)]):
                raise RuntimeError("Expected all prediction to be of type BaseModelAdapter.BoxPrediction")
            if self.model_entity.output_type == 'class' and\
                    not all([isinstance(pred, self.ClassPrediction) for pred in itertools.chain(*all_predictions)]):
                raise RuntimeError("Expected all prediction to be of type BaseModelAdapter.ClassPrediction")

            with self._frozen_dataset(self.snapshot) as ds:
                for idx, item in enumerate(items):
                    self._upload_predictions(item, all_predictions[idx])
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

        items = itertools.chain(*snapshot.get_partitions(partitions=partition, filters=None))
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

    def _upload_predictions(self, item, predictions):
        """Utility function that upload prediction to dlp platform based on the model.outout_type"""
        if self.model_entity.output_type == 'box':
            builder = item.annotations.builder()
            for pred in predictions:
                builder.add(annotation_definition=entities.Box(
                    top=float(pred.top), left=float(pred.left), bottom=float(pred.bottom),
                    right=float(pred.right), label=str(pred.label)),
                    model_info={'name': "{}-{}".format(self.model_name, self.snapshot.name),
                                'confidence': float(pred.score)})

            item.annotations.upload(annotations=builder)
        elif self.model_entity.output_type == 'class':
            builder = item.annotations.builder()
            for pred in predictions:
                builder.add(annotation_definition=entities.Classification(label=pred.label),
                    model_info={'name': "{}-{}".format(self.model_name, self.snapshot.name),
                                'confidence': float(pred.score)})
            item.annotations.upload(annotations=builder)
        else:
            raise NotImplementedError('model output type: {} is not supported to upload to platform'.
                                      format(self.model_entity.output_type))

    def _box_compare(self, act: entities.Annotation, predictions):
        """ Calculates best matched  prediciotn to a single gt. Returns namedTuple (score, prd_id)"""
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

    def _create_partitions(self, train_split=0.7, val_split=0.3, test_split=0.0, **kwargs):
        """ Updates partitions on the current items by the splits ratios"""
        import time
        import numpy as np

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
            self.logger.debug("free frozen context ended. dataset {!r}, readonly was set back to: {}".format(dataset.name, dataset.readonly))


    def __set_adapter_handler(self, level):
        for hdl in self.logger.handlers:
            if hdl.name.startswith('adapter'):
                hdl.setLevel(level=level)

    def __add_adapter_handler(self, level):
        fmt = '%(levelname).1s: %(name)-20s %(asctime)-s [%(filename)-s:%(lineno)-d]:: %(msg)s'
        hdl = logging.StreamHandler()
        hdl.setFormatter(logging.Formatter(fmt=fmt, datefmt='%X'))
        hdl.setLevel(level=level.upper())
        hdl.name = 'adapter_handler' # use the name to get the specific logger
        if hdl.name in [h.name for h in self.logger.handlers]:
            pass  # Handler already on logger
        else:
            self.logger.addHandler(hdlr=hdl)

    @ staticmethod
    def _np_resize_util(images, output_shape):
        from numpy import ndarray
        from skimage.transform import resize
        if isinstance(images, ndarray) and len(images.shape) < 4:
            # Single image
            return resize(img, output_shape=output_shape)
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
        import keras
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

