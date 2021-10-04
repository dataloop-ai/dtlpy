from .base_dataset_generator import BaseGenerator
import torch
from torch.utils.data import Dataset


class DataGenerator(BaseGenerator, Dataset):
    """

    """

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        return super(DataGenerator, self).__getitem__(idx)
