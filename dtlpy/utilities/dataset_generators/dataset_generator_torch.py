import logging
from .dataset_generator import DatasetGenerator

logger = logging.getLogger('dtlpy')

try:
    import torch
    from torch.utils.data import Dataset
except (ImportError, ModuleNotFoundError):
    logger.error('Failed importing torch package, cannot use DatasetGeneratorTorch')


class DatasetGeneratorTorch(DatasetGenerator, Dataset):
    """

    """

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        return super(DatasetGeneratorTorch, self).__getitem__(idx)
