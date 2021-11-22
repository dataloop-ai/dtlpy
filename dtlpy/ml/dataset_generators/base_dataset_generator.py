from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
import torchvision
import numpy as np
import logging
import imgaug
import shutil
import json
import os

from ... import entities

logger = logging.getLogger(__name__)


class BaseGenerator:
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

    def __init__(self,
                 dataset_entity: entities.Dataset,
                 annotation_type: entities.AnnotationType,
                 data_path=None,
                 overwrite=False,
                 label_to_id_map=None,
                 transforms=None,
                 num_workers=0,
                 shuffle=True,
                 seed=None,
                 to_categorical=False,
                 # debug flags
                 return_originals=False,
                 return_separate_labels=False,
                 return_filename=False,
                 return_label_string=False,
                 ) -> None:
        """
        Base Dataset Generator to build and iterate over images and annotations

        :param dataset_entity: dl.Dataset entity
        :param annotation_type: dl.AnnotationType - type of annotation to load from the annotated dataset
        :param data_path: Path to Dataloop annotations (root to "item" and "json").
        :param overwrite:
        :param label_to_id_map: dict - {label_string: id} dictionary
        :param transforms: Optional transform to be applied on a sample. list or torchvision.Transform
        :param num_workers:
        :param shuffle: Whether to shuffle the data (default: True) If set to False, sorts the data in alphanumeric order.
        :param seed: Optional random seed for shuffling and transformations.
        :param to_categorical: convert label id to categorical format
        :param return_originals: bool - If True, return ALSO images and annotations before transformations (for debug)
        :param return_separate_labels: bool - If True, return labels and geo separately and not concatenated to single array
        :param return_filename: bool - If True, return the parsed itemname along with image array and annotation
        :param return_label_string: bool - If True, the returned annotation is by it's label string and not label id mapping
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
            # TODO optimize
            _ = dataset_entity.download_annotations(local_path=data_path)
            _ = dataset_entity.items.download(local_path=data_path)
        self.root_dir = data_path
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
        # inits
        self.image_paths = list()
        self.annotations = list()
        # flags
        self.return_filename = return_filename
        self.return_label_string = return_label_string
        self.return_originals = return_originals
        self.return_separate_labels = return_separate_labels

        ####################
        # Load annotations #
        ####################
        self.load_annotations()

    def load_annotations(self):
        root_path = Path(self.root_dir)
        for json_path in root_path.rglob('**/*.json'):
            with open(json_path, 'r') as f:
                data = json.load(f)
            img_path = root_path.joinpath('items').joinpath(data['filename'][1:])
            geos, labels_ids = None, None
            if self.annotation_type is not None:
                annotation = entities.AnnotationCollection.from_json(data)
                if img_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    # loading a single item's annotations
                    # get label ids as [N, 1], boxes [N, 4]
                    geos, labels_ids = self._from_dtlpy(annotation)
                    if labels_ids.shape[0] == 0:
                        logger.warning('Empty annotation for image filename: {}'.format(img_path))
                        continue
            self.image_paths.append(img_path)
            self.annotations.append((geos, labels_ids))

        if self.shuffle:
            if self.seed is None:
                self.seed = 42
            np.random.seed(self.seed)
            np.random.shuffle(self.annotations)
            np.random.seed(self.seed)
            np.random.shuffle(self.image_paths)

    @property
    def dataset_entity(self):
        assert isinstance(self._dataset_entity, entities.Dataset)
        return self._dataset_entity

    @dataset_entity.setter
    def dataset_entity(self, val):
        assert isinstance(val, entities.Dataset)
        self._dataset_entity = val

    def __len__(self):
        return len(self.image_paths)

    def _type_to_var_name(self):
        if self.annotation_type == entities.AnnotationType.BOX:
            return 'bounding_boxes'
        elif self.annotation_type == entities.AnnotationType.SEGMENTATION:
            return 'segmentation_map'
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

    def _from_dtlpy(self, annotations):
        # collect annotations
        geos = list()
        labels_id = list()
        for annotation in annotations:
            if annotation.type == self.annotation_type:
                if annotation.type == entities.AnnotationType.BOX:
                    # [x1, y1, x2, y2]
                    geo = np.asarray([annotation.left,
                                      annotation.top,
                                      annotation.right,
                                      annotation.bottom])
                elif annotation.type == entities.AnnotationType.CLASSIFICATION:
                    # None
                    geo = None
                else:
                    raise ValueError(
                        'unsupported annotation type: {}'.format(annotation.type))
                geos.append(geo)
                if self.return_label_string:
                    labels_id.append(annotation.label)
                else:
                    labels_id.append(self.label_to_id_map[annotation.label])

        # reorder for output
        geos = np.asarray(geos).astype(float)
        if self.return_label_string:
            labels_id = np.asarray(labels_id).reshape((-1, 1))
        else:
            labels_id = np.asarray(labels_id).reshape((-1, 1)).astype(float)
        if self.annotation_type == entities.AnnotationType.BOX:
            geos = geos.reshape(-1, 4)
        return geos, labels_id

    def _to_dtlpy(self, targets, labels=None):
        annotations = entities.AnnotationCollection(item=None)
        if labels is None:
            labels = [None] * len(targets)
        for target, label in zip(targets, labels):
            if self.annotation_type == entities.AnnotationType.BOX:
                annotations.add(annotation_definition=entities.Box(left=target[0],
                                                                   top=target[1],
                                                                   right=target[2],
                                                                   bottom=target[3],
                                                                   label=label))
            elif self.annotation_type == entities.AnnotationType.CLASSIFICATION:
                annotations.add(
                    annotation_definition=entities.Classification(label=label))
            else:
                raise ValueError(
                    'unsupported annotation type: {}'.format(self.annotation_type))
        return annotations

    def visualize(self, idx=None, return_output=False, plot=True):
        import matplotlib.pyplot as plt
        if idx is None:
            idx = np.random.randint(self.__len__())
        t = self.return_separate_labels
        self.return_separate_labels = True
        image, targets, labels = self.__getitem__(idx)
        self.return_separate_labels = t
        annotations = self._to_dtlpy(targets=targets, labels=labels)
        marked_image = annotations.show(image=image,
                                        height=image.shape[0],
                                        width=image.shape[1],
                                        color=(255, 0, 0),
                                        with_text=True)
        if plot:
            plt.figure()
            plt.imshow(marked_image)
        if return_output:
            return marked_image, annotations

    def __getsingleitem__(self, idx):
        image_filename = self.image_paths[idx]
        geos, labels_ids = self.annotations[idx]
        parsed_filename = os.path.basename(image_filename)
        image = np.asarray(Image.open(image_filename).convert('RGB'))

        orig_image = None
        orig_geos = None
        if self.return_originals:
            orig_image = image.copy()
            orig_geos = geos.copy()

        ###########################
        # perform transformations #
        ###########################
        if self._transforms:
            image, geos = self.transform(image, geos)

        to_return = (image,)
        if self.annotation_type is not None:
            # build the annotations format to return
            targets = (geos, labels_ids)
            if not self.return_separate_labels:
                if self.annotation_type == entities.AnnotationType.CLASSIFICATION:
                    # support only for single classification label
                    y = labels_ids.flatten()[0]
                    if self.to_categorical:
                        categorical = np.zeros(self.num_classes, dtype='float32')
                        categorical[int(y)] = 1
                        y = categorical
                    targets = (y,)
                else:
                    targets = (np.concatenate((geos, labels_ids), axis=1),)
            to_return += targets
        # return original images flag
        if self.return_originals:
            to_return += (orig_image, orig_geos)
        # return item filename flag
        if self.return_filename:
            to_return += (parsed_filename,)
        return to_return

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
