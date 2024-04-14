from abc import ABC

from base_model_adapter import BaseModelAdapter
from .. import entities


class BaseFeatureExtractorAdapter(BaseModelAdapter, ABC):
    def __int__(self, model_entity: entities.Model = None):
        super().__init__(model_entity)

    def extract_features(self, batch: list, **kwargs):
        """ Runs inference with the model, but does not predict. Instead, extracts features for the input batch.

            Virtual method - need to implement

        :param batch: `list` a list containing a batch of items whose features will be extracted
        """
        raise NotImplementedError("Please implement 'extract_features' method in {}".format(self.__class__.__name__))

    def extract_dataset_features(self, dataset: entities.Dataset, **kwargs):
        """ Runs inference to extract features for all items in a dataset.

            Virtual method - need to implement

        :param dataset: `entities.Dataset` dataset entity whose items will have their features extracted
        """
        raise NotImplementedError("Please implement 'extract_dataset_features' method in "
                                  "{}".format(self.__class__.__name__))