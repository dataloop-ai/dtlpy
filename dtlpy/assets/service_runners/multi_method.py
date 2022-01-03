import dtlpy as dl
import logging

logger = logging.getLogger(name='dtlpy')


class ServiceRunner(dl.BaseServiceRunner):
    """
    Package runner class

    """

    def __init__(self):
        """
        Init package attributes here

        :return:
        """

    def first_method(self, progress=None):
        """
        In this example we print print 'Hello World'

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        progress.update(status='inProgress', progress=0)
        print('Hello World from Dataloop :)')

    def second_method(self, progress=None):
        """
        In this example we print print 'Hello World'

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        progress.update(status='inProgress', progress=0)
        print('Hello World from Dataloop :)')


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
