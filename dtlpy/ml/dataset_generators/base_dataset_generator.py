from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import torchvision
import numpy as np
import collections
import traceback
import logging
import imgaug
import shutil
import json
import copy
import tqdm
import os

from ... import entities

logger = logging.getLogger('dtlpy')


class DataItem(dict):
    def __init__(self, *args, **kwargs):
        super(DataItem, self).__init__(*args, **kwargs)

    @property
    def image_filepath(self):
        return self['image_filepath']

    @image_filepath.setter
    def image_filepath(self, val):
        self['image_filepath'] = val


class BaseGenerator:
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

    def __init__(self,
                 dataset_entity: entities.Dataset,
                 annotation_type: entities.AnnotationType,
                 filters: entities.Filters = None,
                 data_path=None,
                 overwrite=False,
                 label_to_id_map=None,
                 transforms=None,
                 num_workers=0,
                 shuffle=True,
                 seed=None,
                 to_categorical=False,
                 class_balancing=False,
                 # debug flags
                 return_originals=False,
                 ignore_empty=True
                 ) -> None:
        """
        Base Dataset Generator to build and iterate over images and annotations

        :param dataset_entity: dl.Dataset entity
        :param annotation_type: dl.AnnotationType - type of annotation to load from the annotated dataset
        :param filters: dl.Filters - filtering entity to filter the dataset items
        :param data_path: Path to Dataloop annotations (root to "item" and "json").
        :param overwrite:
        :param label_to_id_map: dict - {label_string: id} dictionary
        :param transforms: Optional transform to be applied on a sample. list or torchvision.Transform
        :param num_workers:
        :param shuffle: Whether to shuffle the data (default: True) If set to False, sorts the data in alphanumeric order.
        :param seed: Optional random seed for shuffling and transformations.
        :param to_categorical: convert label id to categorical format
        :param class_balancing: if True - performing random over-sample with class ids as the target to balance training data
        :param return_originals: bool - If True, return ALSO images and annotations before transformations (for debug)
        :param ignore_empty: bool - If True, generator will NOT collect items without annotations
        """

        if data_path is None:
            data_path = os.path.join(os.path.expanduser('~'),
                                     '.dataloop',
                                     'datasets',
                                     "{}_{}".format(dataset_entity.name,
                                                    dataset_entity.id))
        download = False
        if os.path.isdir(data_path):
            if overwrite:
                logger.warning('overwrite flag is True! deleting and overwriting')
                shutil.rmtree(data_path)
                download = True
        else:
            download = True
        if download:
            if annotation_type in [entities.AnnotationType.SEGMENTATION]:
                annotation_options = entities.ViewAnnotationOptions.INSTANCE
            else:
                annotation_options = entities.ViewAnnotationOptions.JSON
            _ = dataset_entity.items.download(filters=filters,
                                              local_path=data_path,
                                              annotation_options=annotation_options)
        self.root_dir = data_path
        self._items_path = Path(self.root_dir).joinpath('items')
        self._json_path = Path(self.root_dir).joinpath('json')
        self._mask_path = Path(self.root_dir).joinpath('instance')
        self._transforms = transforms
        self._dataset_entity = dataset_entity
        if label_to_id_map is None:
            labels = [label for label in dataset_entity.labels_flat_dict]
            labels.sort()
            label_to_id_map = {label: i_label for i_label, label in enumerate(labels)}
        self.id_to_label_map = {v: k for k, v in label_to_id_map.items()}
        self.label_to_id_map = label_to_id_map
        self.annotation_type = annotation_type
        self.imgaug_ann_type = self._type_to_var_name()
        self.num_workers = num_workers
        self.to_categorical = to_categorical
        self.num_classes = len(label_to_id_map)
        self.shuffle = shuffle
        self.seed = seed
        self.class_balancing = class_balancing
        # inits
        self.data_items = list()
        # flags
        self.return_originals = return_originals
        self.ignore_empty = ignore_empty

        ####################
        # Load annotations #
        ####################
        self.load_annotations()

    def _load_single(self, image_filepath, pbar=None):
        try:
            is_empty = False
            item_info = DataItem()
            # add image path
            item_info.image_filepath = str(image_filepath)
            # get "platform" path
            rel_path = image_filepath.relative_to(self._items_path)
            # replace suffix to JSON
            rel_path_wo_png_ext = rel_path.with_suffix('.json')
            # create local path
            annotation_filepath = Path(self._json_path, rel_path_wo_png_ext)

            if os.path.isfile(annotation_filepath):
                with open(annotation_filepath, 'r') as f:
                    data = json.load(f)
                    item_id = data.get('_id')
                    annotations = entities.AnnotationCollection.from_json(data)
            else:
                item_id = ''
                annotations = None
            item_info.update(item_id=item_id)
            if self.annotation_type is not None:
                # add item id from json

                box_coordinates = list()
                classes_ids = list()
                labels = list()
                if annotations is not None:
                    for annotation in annotations:
                        if 'user' in annotation.metadata and \
                                'model' in annotation.metadata['user']:
                            # and 'name' in annotation.metadata['user']['model']:
                            # Do not use prediction annotations in the data generator
                            continue
                        if annotation.type == self.annotation_type:
                            classes_ids.append(self.label_to_id_map[annotation.label])
                            labels.append(annotation.label)

                            if annotation.type == entities.AnnotationType.BOX:
                                # [x1, y1, x2, y2]
                                annotation: entities.Box
                                box_coordinates.append(np.asarray([annotation.left,
                                                                   annotation.top,
                                                                   annotation.right,
                                                                   annotation.bottom]))
                                classes_ids.append(self.label_to_id_map[annotation.label])
                                labels.append(annotation.label)
                            elif annotation.type in [entities.AnnotationType.CLASSIFICATION,
                                                     entities.AnnotationType.SEGMENTATION]:
                                ...
                            else:
                                raise ValueError(
                                    'unsupported annotation type: {}'.format(annotation.type))
                # reorder for output
                item_info.update({entities.AnnotationType.BOX.value: np.asarray(box_coordinates).astype(float),
                                  entities.AnnotationType.CLASSIFICATION.value: np.asarray(classes_ids),
                                  'labels': labels})
                if len(item_info['labels']) == 0:
                    logger.debug('Empty annotation for image filename: {}'.format(image_filepath))
                    is_empty = True
            if self.annotation_type in [entities.AnnotationType.SEGMENTATION]:
                # get "platform" path
                rel_path = image_filepath.relative_to(self._items_path)
                # replace suffix to PNG
                rel_path_wo_png_ext = rel_path.with_suffix('.png')
                # create local path
                mask_filepath = Path(self._mask_path, rel_path_wo_png_ext)
                if not os.path.isfile(mask_filepath):
                    logger.debug('Empty annotation for image filename: {}'.format(image_filepath))
                    is_empty = True
                item_info.update({entities.AnnotationType.SEGMENTATION.value: str(mask_filepath)})
            item_info.update(annotation_filepath=str(annotation_filepath))
            return item_info, is_empty
        except Exception:
            logger.exception('failed loading item in generator! {!r}'.format(image_filepath))
            return None, True
        finally:
            if pbar is not None:
                pbar.update()

    def load_annotations(self):
        logger.info(f"Collecting items with the following extensions: {self.IMAGE_EXTENSIONS}")
        files = list()
        for ext in self.IMAGE_EXTENSIONS:
            files.extend(self._items_path.rglob(f'*{ext}'))

        pool = ThreadPoolExecutor(max_workers=32)
        jobs = list()
        pbar = tqdm.tqdm(total=len(files), desc='Loading Data Generator')
        for image_filepath in files:
            jobs.append(pool.submit(self._load_single,
                                    image_filepath=image_filepath,
                                    pbar=pbar))
        outputs = [job.result() for job in jobs]
        pbar.close()

        n_items = len(outputs)
        n_empty_items = sum([1 for _, is_empty in outputs if is_empty is True])

        output_msg = 'Done loading items. Total items loaded: {}.'.format(n_items)
        if n_empty_items > 0:
            output_msg += '{action} {n_empty_items} items without annotations'.format(
                action='IGNORING' if self.ignore_empty else 'INCLUDING',
                n_empty_items=n_empty_items)

        if self.ignore_empty:
            # take ONLY non-empty
            data_items = [data_item for data_item, is_empty in outputs if is_empty is False]
        else:
            # take all
            data_items = [data_item for data_item, is_empty in outputs]

        self.data_items = data_items
        logger.info(output_msg)
        ###################
        # class balancing #
        ###################
        labels = [label for item in self.data_items for label in item.get('labels', list())]
        logger.info(f"Data Generator labels balance statistics: {collections.Counter(labels)}")
        if self.class_balancing:
            try:
                from imblearn.over_sampling import RandomOverSampler
            except Exception:
                logger.error(
                    'Class balancing is on but missing "imbalanced-learn". run "pip install -U imbalanced-learn" and try again')
                raise
            logger.info('Class balance is on!')
            class_ids = [class_id for item in self.data_items for class_id in item['class']]
            dummy_inds = [i_item for i_item, item in enumerate(self.data_items) for _ in item['class']]
            over_sampler = RandomOverSampler(random_state=42)
            X_res, y_res = over_sampler.fit_resample(np.asarray(dummy_inds).reshape(-1, 1), np.asarray(class_ids))
            over_sampled_data_items = [self.data_items[i] for i in X_res.flatten()]
            oversampled_labels = [label for item in over_sampled_data_items for label in item['labels']]
            logger.info(f"Data Generator labels after oversampling: {collections.Counter(oversampled_labels)}")
            self.data_items = over_sampled_data_items

        if self.shuffle:
            if self.seed is None:
                self.seed = 42
            np.random.seed(self.seed)
            np.random.shuffle(self.data_items)

    @property
    def dataset_entity(self):
        assert isinstance(self._dataset_entity, entities.Dataset)
        return self._dataset_entity

    @dataset_entity.setter
    def dataset_entity(self, val):
        assert isinstance(val, entities.Dataset)
        self._dataset_entity = val

    def __len__(self):
        return len(self.data_items)

    def _type_to_var_name(self):
        if self.annotation_type == entities.AnnotationType.BOX:
            return 'bounding_boxes'
        elif self.annotation_type == entities.AnnotationType.SEGMENTATION:
            return 'segmentation_maps'
        elif self.annotation_type == entities.AnnotationType.POLYGON:
            return 'polygons'
        else:
            return None

    def transform(self, image, target=None):
        if isinstance(self._transforms, torchvision.transforms.Compose):
            # use torchvision compose
            ts = self._transforms.transforms
        elif isinstance(self._transforms, imgaug.augmenters.meta.Sequential):
            # use imgaug
            ts = list(self._transforms)
        elif isinstance(self._transforms, list):
            # use list of functions
            ts = self._transforms
        else:
            raise ValueError('unknown transformers type')

        # go over transformation in list
        for t in ts:
            if isinstance(t, imgaug.augmenters.meta.Sequential):
                # handle imgaug calls
                if target is not None and self.imgaug_ann_type is not None:
                    # works for batch but running on a single image
                    image, target = t(images=[image], **{self.imgaug_ann_type: [target]})
                    target = target[0]
                else:
                    image = t(images=[image])
                image = image[0]
            else:
                # all other function in the Compose
                image = t(image)
        return image, target

    def _to_dtlpy(self, targets, labels=None):
        annotations = entities.AnnotationCollection(item=None)
        annotations._dataset = self._dataset_entity
        if labels is None:
            labels = [None] * len(targets)
        if self.annotation_type == entities.AnnotationType.SEGMENTATION:
            for label, label_ind in self.label_to_id_map.items():
                target = targets == label_ind
                if np.any(target):
                    annotations.add(annotation_definition=entities.Segmentation(geo=target,
                                                                                label=label))
        elif self.annotation_type == entities.AnnotationType.BOX:
            for target, label in zip(targets, labels):
                annotations.add(annotation_definition=entities.Box(left=target[0],
                                                                   top=target[1],
                                                                   right=target[2],
                                                                   bottom=target[3],
                                                                   label=label))
        elif self.annotation_type == entities.AnnotationType.CLASSIFICATION:
            for target, label in zip(targets, labels):
                annotations.add(annotation_definition=entities.Classification(label=label))
        else:
            raise ValueError('unsupported annotation type: {}'.format(self.annotation_type))
        # set dataset for color
        for annotation in annotations:
            annotation._dataset = self._dataset_entity
        return annotations

    def visualize(self, idx=None, return_output=False, plot=True):
        import matplotlib.pyplot as plt
        if idx is None:
            idx = np.random.randint(self.__len__())
        data_item = self.__getitem__(idx)
        image = data_item.get('image')
        labels = data_item.get('labels')
        targets = data_item.get('annotations')
        annotations = self._to_dtlpy(targets=targets, labels=labels)
        marked_image = annotations.show(image=image,
                                        height=image.shape[0],
                                        width=image.shape[1],
                                        alpha=0.8,
                                        with_text=False)
        if plot:
            plt.figure()
            plt.imshow(marked_image)
        if return_output:
            return marked_image, annotations

    def __getsingleitem__(self, idx):
        data_item = copy.deepcopy(self.data_items[idx])

        image_filename = data_item.get('image_filepath')
        image = np.asarray(Image.open(image_filename))
        data_item.update({'image': image})

        annotations = data_item.get(self.annotation_type)
        if self.annotation_type == entities.AnnotationType.SEGMENTATION:
            # if segmentation - read from file
            mask_filepath = annotations
            annotations = np.asarray(Image.open(mask_filepath).convert('L'))
        data_item.update({'annotations': annotations})

        if self.return_originals:
            annotations = data_item.get('annotations')
            data_item.update({'orig_image': image.copy(),
                              'orig_annotations': annotations.copy()})

        ###########################
        # perform transformations #
        ###########################
        if self._transforms:
            annotations = data_item.get('annotations')
            image, annotations = self.transform(image, annotations)
            data_item.update({'image': image,
                              'annotations': annotations})
        return data_item

    def __getitem__(self, idx):
        """
            Support single index or a slice.
            Uses ThreadPoolExecutor is num_workers != 0
        """
        if isinstance(idx, int):
            to_return = self.__getsingleitem__(idx)

        elif isinstance(idx, slice):
            to_return = list()
            idxs = list(range(idx.start, idx.stop,
                              idx.step if idx.step else 1))
            if self.num_workers == 0:
                for dx in idxs:
                    to_return.append(self.__getsingleitem__(dx))
            else:
                with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                    for sample in executor.map(lambda i: self.__getsingleitem__(i), idxs):
                        to_return.append(sample)
        else:
            raise TypeError('list indices must be integers or slices, not {}'.format(type(idx)))
        return to_return
