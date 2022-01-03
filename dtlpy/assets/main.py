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

    def run(self, item, progress=None):
        """
        Write your main package service here

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        progress.update(status='inProgress', progress=0)
        print('Item received! filename: {}'.format(item.filename))
        builder = item.annotations.builder()
        builder.add(dl.Classification(label='from_function'))
        item.annotations.upload(builder)
        print('Annotation uploaded!')

    def hello(self, progress=None):
        """
        Write your main package service here

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
