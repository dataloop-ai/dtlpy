import dtlpy as dl


class ModelAdapter(dl.BaseModelAdapter):
    """
    Specific Model adapter.
    The class bind a dl.Model entity with the package code
    """
    # TODO:
    #   1) docstring for your ModelAdapter
    #   2) implement the virtual methods for full adapter support
    #   3) add your _defaults

    _defaults = {}

    def __init__(self, model_entity):
        super(ModelAdapter, self).__init__(model_entity)

    # ===============================
    # NEED TO IMPLEMENT THESE METHODS
    # ===============================

    def load(self, local_path, **kwargs):
        """ Loads model and populates self.model with a `runnable` model

            Virtual method - need to implement

            This function is called by load_from_model (download to local and then loads)

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'load' method in {}".format(self.__class__.__name__))

    def save(self, local_path, **kwargs):
        """ saves configuration and weights locally

            Virtual method - need to implement

            the function is called in save_to_model which first save locally and then uploads to model entity

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'save' method in {}".format(self.__class__.__name__))

    def train(self, data_path, dump_path, **kwargs):
        """
        Virtual method - need to implement
        Train the model according to data in local_path and save everything to dump_path

        :param data_path: `str` local File System path to where the data was downloaded and converted at
        :param dump_path: `str` local File System path where to dump training mid-results (checkpoints, logs...)
        """
        raise NotImplementedError("Please implement 'train' method in {}".format(self.__class__.__name__))

    def predict(self, batch, **kwargs):
        """ Model inference (predictions) on batch of images

            Virtual method - need to implement

        :param batch: `np.ndarray`
        :return: `list[dl.AnnotationCollection]` each collection is per each image / item in the batch
        """
        raise NotImplementedError("Please implement 'predict' method in {}".format(self.__class__.__name__))

    def convert(self, data_path, **kwargs):
        """ Convert Dataloop structure data to model structured

            Virtual method - need to implement

            e.g. take dlp dir structure and construct annotation file

        :param data_path: `str` local File System directory path where
                           we already downloaded the data from dataloop platform
        :return:
        """
        raise NotImplementedError("Please implement 'convert' method in {}".format(self.__class__.__name__))

    # NOT IN USE
    def convert_dlp(self, items: dl.entities.PagedEntities):
        """ This should implement similar to convert only to work on dlp items.  ->
                   -> meaning create the converted version from items entities"""
        # TODO
        pass
