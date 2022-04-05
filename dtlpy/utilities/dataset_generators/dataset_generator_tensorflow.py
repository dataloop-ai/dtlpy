import logging

from .dataset_generator import DatasetGenerator

logger = logging.getLogger('dtlpy')

try:
    import tensorflow
except (ImportError, ModuleNotFoundError):
    logger.error('Failed importing tensorflow package, cannot use DatasetGeneratorTensorflow')


class DatasetGeneratorTensorflow(DatasetGenerator, tensorflow.keras.utils.Sequence):
    def __getitem__(self, item):
        batch = super(DatasetGeneratorTensorflow, self).__getitem__(item)
        x = batch['image']
        y = batch['annotations']
        return x, y

    def __iter__(self):
        """Create a generator that iterate over the Sequence."""
        for item in (self[i] for i in range(len(self))):
            yield item
