import dtlpy as dl
import logging

logger = logging.getLogger(name=__name__)


class ServiceRunner(dl.BaseServiceRunner):
    """
    Package runner class

    """

    def __init__(self, **kwargs):
        """
        Init package attributes here

        :param kwargs: config params
        :return:
        """

    def first_method(self, config, progress=None):
        """
        In this example we copy dataset items by query to a new dataset

        :param config: This is a json input
        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        source_dataset = dl.datasets.get(dataset_id=config['source_dataset_id'])
        filters = dl.Filters(custom_filter=config['query'])
        new_dataset = source_dataset.project.datasets.create(dataset_name='{}-copy'.format(source_dataset.name),
                                                             labels=source_dataset.labels)
        new_dataset.items.upload(local_path=source_dataset.items.download(filters=filters))
        logger.info('Dataset copied successfully')

    def second_method(self, config, progress=None):
        """
        Write your main package service here

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
