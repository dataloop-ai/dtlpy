import numpy as np
import tensorflow as tf
import tensorflow.keras.utils
import collections.abc
import re

from .base_dataset_generator import BaseGenerator
from ... import entities

np_str_obj_array_pattern = re.compile(r'[SaUO]')

default_collate_err_msg_format = (
    "default_collate: batch must contain tensors, numpy arrays, numbers, "
    "dicts or lists; found {}")


class DataGenerator(BaseGenerator, tensorflow.keras.utils.Sequence):

    def __init__(self,
                 dataset_entity: entities.Dataset,
                 annotation_type: entities.AnnotationType,
                 data_path=None,
                 overwrite=False,
                 label_to_id_map=None,
                 transforms=None,
                 to_categorical=False,
                 shuffle=True,
                 seed=None,
                 # keras
                 batch_size=32,
                 # flags
                 return_originals=False,
                 ignore_empty=True
                 ) -> None:
        """
        """
        super(DataGenerator, self).__init__(dataset_entity=dataset_entity,
                                            annotation_type=annotation_type,
                                            data_path=data_path,
                                            overwrite=overwrite,
                                            label_to_id_map=label_to_id_map,
                                            transforms=transforms,
                                            to_categorical=to_categorical,
                                            shuffle=shuffle,
                                            seed=seed,
                                            # flags
                                            return_originals=return_originals,
                                            ignore_empty=ignore_empty
                                            )
        self.batch_size = batch_size

    def __getitem__(self, index):
        indices = slice(index * self.batch_size, (index + 1) * self.batch_size)
        batch = super(DataGenerator, self).__getitem__(indices)
        # convert from list of sample to a unified dict of all samples
        return collate(batch=batch)

    def __iter__(self):
        """Create a generator that iterate over the Sequence."""
        for item in (self[i] for i in range(len(self))):
            yield item

    def __len__(self):
        n_data = super(DataGenerator, self).__len__()
        return int(np.floor(n_data / self.batch_size))


def collate(batch):
    r"""Puts each data field into a tensor with outer dimension batch size"""

    elem = batch[0]
    elem_type = type(elem)
    if isinstance(elem, tf.Tensor):
        return tf.stack(batch, axis=0)
    elif elem_type.__module__ == 'numpy' and elem_type.__name__ != 'str_' and elem_type.__name__ != 'string_':
        if elem_type.__name__ == 'ndarray' or elem_type.__name__ == 'memmap':
            # array of string classes and object
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError(default_collate_err_msg_format.format(elem.dtype))
            return tf.convert_to_tensor(batch)
            # return [tf.convert_to_tensor(b) for b in batch]
        elif elem.shape == ():  # scalars
            return tf.convert_to_tensor(batch)
    elif isinstance(elem, float):
        return tf.convert_to_tensor(batch, dtype=tf.float64)
    elif isinstance(elem, int):
        return tf.convert_to_tensor(batch)
    elif isinstance(elem, str) or isinstance(elem, bytes) or elem is None:
        return batch
    elif isinstance(elem, collections.abc.Mapping):
        return {key: collate([d[key] for d in batch]) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, '_fields'):  # namedtuple
        return elem_type(*(collate(samples) for samples in zip(*batch)))
    elif isinstance(elem, collections.abc.Sequence):
        transposed = zip(*batch)
        return transposed
    raise TypeError(default_collate_err_msg_format.format(elem_type))
