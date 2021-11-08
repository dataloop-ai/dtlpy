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
                 # keras
                 batch_size=32,
                 # flags
                 return_originals=False,
                 return_separate_labels=False,
                 return_filename=False,
                 return_label_id=True,
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
                                            # flags
                                            return_filename=return_filename,
                                            return_label_id=return_label_id,
                                            return_originals=return_originals,
                                            return_separate_labels=return_separate_labels)
        self.batch_size = batch_size

    def __getitem__(self, index):
        indices = slice(index * self.batch_size, (index + 1) * self.batch_size)
        batch = super(DataGenerator, self).__getitem__(indices)
        # convert from list of sample to a list per column (X, Y, ...)
        nd_batch = np.asarray(batch)
        return nd_batch.T

    def __iter__(self):
        """Create a generator that iterate over the Sequence."""
        for item in (self[i] for i in range(len(self))):
            yield item

    def __len__(self):
        n_data = super(DataGenerator, self).__len__()
        return int(np.floor(n_data / self.batch_size))
