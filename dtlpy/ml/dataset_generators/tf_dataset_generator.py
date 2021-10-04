import numpy as np

from .base_dataset_generator import BaseGenerator
from ... import entities
import tensorflow.keras.utils


class DataGenerator(BaseGenerator, tensorflow.keras.utils.Sequence):

    def __init__(self,
                 dataset_entity: entities.Dataset,
                 annotation_type: entities.AnnotationType,
                 data_path=None,
                 label_to_id_map=None,
                 transforms=None,
                 to_categorical=False,
                 shuffle=True,
                 seed=None,
                 # debug flags
                 with_orig=False,
                 separate_labels=False,
                 # keras
                 batch_size=32
                 ) -> None:
        """
        """
        super(DataGenerator, self).__init__(dataset_entity=dataset_entity,
                                            annotation_type=annotation_type,
                                            data_path=data_path,
                                            label_to_id_map=label_to_id_map,
                                            transforms=transforms,
                                            to_categorical=to_categorical,
                                            shuffle=shuffle,
                                            seed=seed,
                                            # debug flags
                                            with_orig=with_orig,
                                            separate_labels=separate_labels)
        self.batch_size = batch_size

    def __getitem__(self, index):
        indices = slice(index * self.batch_size, (index + 1) * self.batch_size)
        batch = super(DataGenerator, self).__getitem__(indices)
        # convert to x, y
        return np.asarray([x[0] for x in batch]), np.asarray([x[1] for x in batch])

    def __iter__(self):
        """Create a generator that iterate over the Sequence."""
        for item in (self[i] for i in range(len(self))):
            yield item

    def __len__(self):
        n_data = super(DataGenerator, self).__len__()
        return int(np.floor(n_data / self.batch_size))
