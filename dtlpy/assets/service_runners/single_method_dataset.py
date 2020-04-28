import dtlpy as dl
import logging
import datetime

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

    def run(self, dataset, progress=None):
        """
        In this example we create a task for annotated items in dataset

        :param progress: Use this to update the progress of your package
        :return:
        """
        # these lines can be removed
        assert isinstance(progress, dl.Progress)
        assert isinstance(dataset, dl.entities.Dataset)
        filters = dl.Filters(field='annotated', values=True)
        filters.add_join(field='label', values='person')
        task = dataset.tasks.create(task_name='AutomatedTask',
                                    due_date=datetime.datetime.now().timestamp() + 60*60*24*7,
                                    assignee_ids=['annotator1@dataloop.ai', 'annotator2@dataloop.ai'])
        logger.info('Task created successfully. Task name: {}'.format(task.name))


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
