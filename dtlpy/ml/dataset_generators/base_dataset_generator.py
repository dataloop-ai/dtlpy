import os
import json
from pathlib import Path
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import imgaug
import torchvision

from ... import entities


class BaseGenerator:
    def __init__(self,
                 dataset_entity: entities.Dataset,
                 annotation_type: entities.AnnotationType,
                 data_path=None,
                 label_to_id_map=None,
                 transforms=None,
                 num_workers=0,
                 shuffle=True,
                 seed=None,
                 # debug flags
                 with_orig=False,
                 separate_labels=False,
                 to_categorical=False) -> None:
        """
        Args:
            dataset_entity: dl.Dataset entity
            label_to_id_map: dict - {label_string: id} dictionary
            annotation_type: dl.AnnotationType - type of annotation to load from the annotated dataset
            data_path (string): Path to Dataloop annotations (root to "item" and "json").
            transforms (callable, optional): Optional transform to be applied on a sample.
            shuffle: Whether to shuffle the data (default: True) If set to False, sorts the data in alphanumeric order.
            seed: Optional random seed for shuffling and transformations.
            with_orig: bool - to return items before transformations (for debug)
            separate_labels: bool -  return labels and geo (and not concatenated to single array
        """
        if data_path is None:
            data_path = os.path.join(os.path.expanduser('~'),
                                     '.dataloop',
                                     'datasets',
                                     "{}_{}".format(dataset_entity.name,
                                                    dataset_entity.id))
            _ = dataset_entity.items.download(local_path=data_path,
                                              annotation_options=[entities.ViewAnnotationOptions.JSON])
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

        ####################
        # Load annotations #
        ####################
        self.image_paths = list()
        self.annotations = list()
        root_path = Path(self.root_dir)
        for json_path in root_path.rglob('**/*.json'):
            with open(json_path, 'r') as f:
                data = json.load(f)
            annotation = entities.AnnotationCollection.from_json(data)
            img_path = root_path.joinpath('items').joinpath(data['filename'][1:])
            if img_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                self.image_paths.append(img_path)
                self.annotations.append(annotation)

        if shuffle:
            if seed is None:
                seed = 42
            np.random.seed(seed)
            np.random.shuffle(self.annotations)
            np.random.seed(seed)
            np.random.shuffle(self.image_paths)

        #########
        # Debug #
        #########
        self.with_orig = with_orig
        self.separate_labels = separate_labels

    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

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
                    raise ValueError('unsupported annotation type: {}'.format(annotation.type))
                geos.append(geo)
                labels_id.append(self.label_to_id_map[annotation.label])

        # reorder for output
        geos = np.asarray(geos).astype(float)
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
                annotations.add(annotation_definition=entities.Classification(label=label))
            else:
                raise ValueError('unsupported annotation type: {}'.format(self.annotation_type))
        return annotations

    def visualize(self, idx=None, return_output=False, plot=True):
        import matplotlib.pyplot as plt
        if idx is None:
            idx = np.random.randint(self.__len__())
        t = self.separate_labels
        self.separate_labels = True
        image, targets, labels = self.__getitem__(idx)
        self.separate_labels = t
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
        image = np.asarray(Image.open(self.image_paths[idx]).convert('RGB'))
        # get label ids as [N, 1], boxes [N, 4]
        geos, labels_ids = self._from_dtlpy(self.annotations[idx])

        orig_image = None
        orig_geos = None
        if self.with_orig:
            orig_image = image.copy()
            orig_geos = geos.copy()

        ###########################
        # perform transformations #
        ###########################
        if self._transforms:
            image, geos = self.transform(image, geos)

        to_return = (image,)
        targets = (geos, labels_ids)
        if not self.separate_labels:
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
        if self.with_orig:
            to_return += (orig_image, orig_geos)

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
            idxs = list(range(idx.start, idx.stop, idx.step if idx.step else 1))
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
