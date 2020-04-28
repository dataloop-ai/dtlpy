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

    def first_method(self, annotation, progress=None):
        """
        In this example we update item's metadata if annotation id of specific type

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        assert isinstance(annotation, dl.Annotation)
        if annotation.label == 'box' and annotation.label == 'dog':
            logger.info('Dog was detected in item')
            annotation.attributes.append('Dog detection')
            annotation.item.metadata['dogInPicture'] = True
            annotation.update()
            annotation.item.update()
        logger.info('Function finished successfully!')

    def second_method(self, annotation, progress=None):
        """
        In this example we update item's metadata if annotation id of specific type

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        assert isinstance(annotation, dl.Annotation)


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
