import dtlpy as dl


class ModelAdapter(dl.BaseModelAdapter):
    """
    Specific Model adapter.
    The class bind Dataloop model and snapshot entities with model code implementation
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

            This function is called by load_from_snapshot (download to local and then loads)

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'load' method in {}".format(self.__class__.__name__))

    def save(self, local_path, **kwargs):
        """ saves configuration and weights locally

            Virtual method - need to implement

            the function is called in save_to_snapshot which first save locally and then uploads to snapshot entity

        :param local_path: `str` directory path in local FileSystem
        """
        raise NotImplementedError("Please implement 'save' method in {}".format(self.__class__.__name__))

    def train(self, data_path, dump_path, **kwargs):
        """
        Virtual method - need to implement
        Train the model according to data in local_path and save the snapshot to dump_path

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

    # =============
    # DTLPY METHODS
    # Do not change
    # =============
    # function are here to ease the traceback...
    def load_from_snapshot(self, local_path, snapshot_id, **kwargs):
        """ Loads a model from given `snapshot`.
            Reads configurations and instantiate self.snapshot
            Downloads the snapshot bucket (if available)

        :param local_path:  `str` directory path in local FileSystem to download the snapshot to
        :param snapshot_id:  `str` snapshot id
        """
        return super(ModelAdapter, self).load_from_snapshot(local_path=local_path,
                                                            snapshot_id=snapshot_id,
                                                            **kwargs)

    def save_to_snapshot(self, local_path, snapshot_name=None, description=None, cleanup=False, **kwargs):
        """ Saves configuration and weights to new snapshot bucket
            loads only applies for remote buckets

        :param local_path: `str` directory path in local FileSystem
        :param snapshot_name: `str` name for the new snapshot
        :param description:  `str` description for the new snapshot
        :param cleanup: `bool` if True (default) remove the data from local FileSystem after upload
        :return:
        """
        return super(ModelAdapter, self).save_to_snapshot(local_path=local_path,
                                                          snapshot_name=snapshot_name,
                                                          description=description,
                                                          cleanup=cleanup,
                                                          **kwargs)

    def prepare_trainset(self, data_path, partitions=None, filters=None, **kwargs):
        """
        Prepares train set for train.
        download the specific partition selected to data_path and preforms `self.convert` to the data_path dir

        :param data_path: `str` directory path to use as the root to the data from Dataloop platform
        :param partitions: `dl.SnapshotPartitionType` or list of partitions, defaults for all partitions
        :param filters: `dl.Filter` in order to select only part of the data
        """
        return super(ModelAdapter, self).prepare_trainset(data_path=data_path,
                                                          partitions=partitions,
                                                          filters=filters,
                                                          **kwargs)

    def predict_items(self, items: list, with_upload=True, cleanup=False, batch_size=16, output_shape=None, **kwargs):
        """
        Predicts all items given

        :param items: `List[dl.Item]`
        :param with_upload: `bool` uploads the predictions back to the given items
        :param cleanup: `bool` if set removes existing predictions with the same model-snapshot name (default: False)
        :param batch_size: `int` size of batch to run a single inference
        :param output_shape: `tuple` (width, height) of resize needed per image

        :return: `List[Prediction]` Prediction is set by model.output_type
        """

        return super(ModelAdapter, self).predict_items(items=items,
                                                       with_upload=with_upload,
                                                       cleanup=cleanup,
                                                       batch_size=batch_size,
                                                       output_shape=output_shape,
                                                       **kwargs)
