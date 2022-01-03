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

    def run(self, item, dataset, config, annotation, progress=None):
        """
        In this example we upload annotation to item, update its metadata and add it to a task in the dataset

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        assert isinstance(item, dl.Item)
        assert isinstance(dataset, dl.entities.Dataset)
        assert isinstance(annotation, dl.Annotation)
        item.annotations.upload(annotations=annotation)
        item.metadata['user'] = config['metadata']
        item.update()
        if annotation.label == 'street':
            task = dataset.tasks.get(task_name='streetAnnotation')
            task.add_items(items=item)
        logger.info('Function completed successfully')


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
