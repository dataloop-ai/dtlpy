import json
import os
import logging
import itertools
import tqdm
import time
import numpy as np
from PIL import Image

from .. import entities
from . import BaseModelAdapter

logger = logging.getLogger('dtlpy')


class SuperModelAdapter(BaseModelAdapter):

    def __init__(self, model_entity):
        super(SuperModelAdapter, self).__init__(model_entity)
        self.grids = None  # Note this class support static grids only that are set once for all the images

    # =============
    # DTLPY METHODS
    # =============
    # TODO Does prepare method need to change for super model?!
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
            self.logger.debug("Downloading {} of {}".format(partition, self.snapshot.dataset.name))
            img_list = self.snapshot.download_partition(partition=partition, local_path=data_path, filters=filters)
            self.logger.info("Downloaded {} complete. {} total items".format(partition, len(img_list)))
            if self.grids is None:
                self.logger.info("No Grids defined for {!r} setting global grids".format(self.model_name))
                first_img = Image.open(img_list[0])
                first_item_wh = first_img.size
                _ = self.set_grids_by_nof_boxes(size_wh=first_item_wh, nof_rows=2, nof_cols=2)

            crops_list = self._prepare_grids_trainset(images_filepaths=img_list)

            # TODO: how to ignore the original size images when converting
            self.logger.info("Modifying {} to crops. {} total crops".format(partition, len(crops_list)))

            if partition == entities.SnapshotPartitionType.TEST:
                self.num_test = len(crops_list)
            elif partition == entities.SnapshotPartitionType.VALIDATION:
                self.num_val = len(crops_list)
            elif partition == entities.SnapshotPartitionType.TRAIN:
                self.num_train = len(crops_list)

        # Convert items; json to one annotation file
        self.convert(data_path=data_path, **kwargs)

    def predict_items(self, items: list, with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image

        :return: `List[Prediction]` Prediction is set by model.output_type
        """
        logger.debug("Predicting {} items, using batch size {}. Reshaping to: {}".
                     format(len(items), batch_size, output_shape))

        size_wh = (items[0].width, items[0].height)
        self.set_grids_by_nof_boxes(size_wh=size_wh, nof_rows=3, nof_cols=3)
        # TODO: we need a mapping of item and it's prediction for the load later on..
        all_predictions = []
        for item in items:
            batch = []

            buffer = item.download(save_locally=False)
            img_pil = Image.open(buffer)
            for grid in self.grids:
                crop = img_pil.crop(grid)
                img_np = np.asarray(crop).astype(np.float)
                batch.append(img_np)
            batch = np.asarray(batch)
            batch_predictions = self.predict(batch, **kwargs)
            # scale and shift to the original item
            scaled_predictions = self.aggregate_single_image_predictions(batch_predictions)

            all_predictions.append(scaled_predictions)

        if with_upload:
            # Make sure user created right prediction boxes
            if self.model_entity.output_type == 'box' and \
                    not all([isinstance(pred, self.BoxPrediction) for pred in itertools.chain(*all_predictions)]):
                raise RuntimeError("Expected all prediction to be of type SuperModelAdapter.BoxPrediction")
            if self.model_entity.output_type == 'class' and \
                    not all([isinstance(pred, self.ClassPrediction) for pred in itertools.chain(*all_predictions)]):
                raise RuntimeError("Expected all prediction to be of type SuperModelAdapter.ClassPrediction")

            self.logger.info('Uploading  items annotation for snapshot {!r}. cleanup {}'.
                             format(self.snapshot.name, cleanup))
            with self._frozen_dataset(self.snapshot) as ds:
                for idx, item in enumerate(items):
                    self._upload_predictions(item, all_predictions[idx], cleanup=cleanup)
        return all_predictions

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

    def _create_partitions(self, train_split=0.7, val_split=0.3, test_split=0.0):
        """ Updates partitions on the current items by the splits ratios"""

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
    # ===============
    # Scale and Grid
    # ===============
    def set_grids_by_nof_boxes(self, size_wh, nof_rows=None, nof_cols=None, overlap_scale=1.1, override=False):
        """Return list of grid in LTRB"""
        if self.grids is not None:
            if override:
                self.logger.warning("You are overriding existing grids")
            else:
                self.logger.warning("grids already exist! using existing ({})".format(self.grids))
                return self.grids

        width, height = size_wh
        rect_width = np.ceil(width / nof_cols)
        rect_height = np.ceil(height / nof_rows)
        overlap_width = rect_width * overlap_scale / 2
        overlap_height = rect_height * overlap_scale / 2
        grids = np.empty((0, 4))
        for col in range(nof_cols):
            for row in range(nof_rows):
                # better to use np.min .. for case we will use numpy and not PIL crop
                box = np.array([[
                    col * rect_width - overlap_width,
                    row * rect_height - overlap_height,
                    (col + 1) * rect_width + overlap_width,
                    (row + 1) * rect_height + overlap_height,
                ]])
                box = np.round(box).astype('int')
                grids = np.concatenate([grids, box])
        self.grids = grids
        self.logger.info('set grids:\n{}'.format(self.grids))
        return grids

    def set_grids_by_size(self, size_wh, rect_size=None, overlap=0, override=False):
        """Return list of grid in LTRB"""
        if self.grids is not None:
            if override:
                self.logger.warning("You are overriding existing grids")
            else:
                self.logger.warning("grids already exist! using existing ({})".format(self.grids))
                return self.grids

        width, height = size_wh
        grids = np.empty((0, 4))
        left = 0
        while left < width:
            top = 0
            while top < height:
                box = np.array([[left, top, left + rect_size, top + rect_size]])
                box = np.round(box).astype('int')
                grids = np.concatenate([grids, box])
                top = top + rect_size - overlap
            left = left + rect_size - overlap
        self.grids = grids
        self.logger.info('set grids:\n{}'.format(self.grids))
        return grids

    def aggregate_single_image_predictions(self, grids_predictions, by_class=False):
        """
         TEST FOR NMS WITH TORCH

        :param grids_predictions:
        :param by_class: `bool`

        :return:
        """
        scale_wh = (1, 1)  # # FIXME currently static
        scaled_predictions = []
        current_classes = set()
        for grid_id, crop_preds in enumerate(grids_predictions):
            curr_offset = self.grids[grid_id]
            for p in crop_preds:
                current_classes.add(p.label)
                scaled_predictions += [self.scale_and_shift_box_prediction(p, scale_wh=(1, 1), offset_xy=curr_offset)]

        nms_predictions = []
        if by_class:
            for cls in current_classes:
                nms_predictions += self._torch_nms(predictions=[p for p in scaled_predictions if p.label == cls])
        else:
            nms_predictions = self._torch_nms(predictions=scaled_predictions)
        return nms_predictions

    @staticmethod
    def _torch_nms(predictions):
        try:
            import torch
            from torchvision.ops import nms
        except (ImportError, ModuleNotFoundError) as err:
            logger.critical("Please install pytorch, torchvision package. ")
            raise RuntimeError("method need external package") from err

        boxes = torch.tensor([[p.left, p.top, p.right, p.bottom] for p in predictions],
                             dtype=torch.float32)
        scores = torch.tensor([p.score for p in predictions], dtype=torch.float32)
        keep = nms(boxes=boxes, scores=scores, iou_threshold=0.5)
        return [predictions[k] for k in keep]

    @staticmethod
    def _tf_nms(predictions):
        try:
            import tensorflow as tf
        except (ImportError, ModuleNotFoundError) as err:
            logger.critical("Please install tensorflow package. ")
            raise RuntimeError("method need external package") from err

        boxes = tf.tensor([[p.top, p.left, p.bottom, p.right] for p in predictions], dtype=tf.float32)
        scores = tf.tensor([p.score for p in predictions], dtype=tf.float32)
        selected_indices = tf.image.non_max_suppression(boxes, scores, max_output_size=None, iou_threshold=0.5)
        selected_boxes = tf.gather(boxes, selected_indices)

    def scale_and_shift_box_prediction(self, pred, scale_wh, offset_xy):
        new_left = pred.left * scale_wh[0] + offset_xy[0]
        new_top = pred.top * scale_wh[1] + offset_xy[1]
        new_right = pred.right * scale_wh[0] + offset_xy[0]
        new_bottom = pred.bottom * scale_wh[1] + offset_xy[1]
        new_pred = self.BoxPrediction(top=new_top, left=new_left, bottom=new_bottom, right=new_right,
                                      score=pred.score, label=pred.label)
        return new_pred

    def _prepare_grids_trainset(self, images_filepaths=None, data_path=None):
        """
        The function takes the data in local format of items/json and creates a local version of the crops
        :param images_filepaths: `list` of all images paths to parse
        :param data_path: `str` path where we downloaded the images from dlp servers
                          (optional, in case images_filepaths is None)
        :return: `list` of `str` of all the new images created
        """

        self.logger.info("preparing grids local images from full images")

        if images_filepaths is None:
            # Build a list of all items
            json_dir = os.path.join(data_path, 'json')
            items_dir = os.path.join(data_path, 'items')
            json_filepaths, images_filepaths = [], []

            for path, subdirs, files in os.walk(items_dir):
                for fname in files:
                    # if fname.endswith('json'):
                    #     json_filepaths.append(os.path.join(path, fname))
                    filename, ext = os.path.splitext(fname)
                    if ext.lower() in ['png', 'jpeg', 'jpg']:
                        images_filepaths.append(os.path.join(path, fname))

        # TODO: delete the old versions of jsons..
        # dict_keys(['_id', 'filename', 'annotations', 'itemMetadata'])

        out_images = []
        # parse each image to crops
        for img_path in tqdm.tqdm(images_filepaths, unit='im'):

            base_img_path, ext = os.path.splitext(img_path)
            # read the full image
            im = Image.open(img_path)
            # read the full item + annotations
            json_filepath = base_img_path.replace('items', 'json') + '.json'
            with open(json_filepath, 'r') as fh:
                data = json.load(fh)
            local_item = entities.Item.from_json(data['itemMetadata'], self.model_entity._client_api)
            local_annotations = entities.AnnotationCollection.from_json(_json=data['annotations'])

            for grid in self.grids:
                new_base_img_path = base_img_path + '_crop_r{}_c{}'.format(grid[0], grid[1])
                out_images.append(new_base_img_path + ext)
                # crop image
                crop = im.crop(grid)
                crop.save(new_base_img_path + ext)
                # crop json: annotations
                crop_anns_list = []
                for ann in local_annotations:
                    in_grid_x = ann.left <= grid[2] and ann.right >= grid[0]
                    in_grid_y = ann.top <= grid[3] and ann.bottom >= grid[1]
                    if in_grid_x and in_grid_y:
                        crp_left = max(ann.left, grid[0])
                        crp_top = max(ann.top, grid[1])
                        crp_right = min(ann.right, grid[2])
                        crp_bottom = min(ann.bottom, grid[3])
                        cropped_ann = entities.Annotation.new(
                            item=local_item,
                            annotation_definition=entities.Box(top=crp_top, left=crp_left,
                                                               bottom=crp_bottom, right=crp_right,
                                                               label=ann.label)
                        )
                        crop_anns_list.append(cropped_ann)

                # create a new local_item format json
                crop_item_dict = {'_id': None,
                                  'filename': new_base_img_path + ext,
                                  'annotations': [ann.to_json() for ann in crop_anns_list],
                                  'itemMetadata': {'system': {}}}
                crop_item_dict['itemMetadata']['system']['width'] = grid[2] - grid[0]
                crop_item_dict['itemMetadata']['system']['height'] = grid[3] - grid[1]

                # save the new json
                new_json_path = new_base_img_path.replace('items', 'json') + '.json'
                with open(new_json_path, 'w') as fh:
                    json.dump(crop_item_dict, fh)

        return out_images
