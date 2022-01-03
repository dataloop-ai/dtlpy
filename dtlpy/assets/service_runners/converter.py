import dtlpy as dl
import logging
import shutil
import tempfile
import os
import zipfile
import datetime

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

    def run(self, dataset, query=None, progress=None):
        """
        In this example we create a task for annotated items in dataset

        :param query: Dictionary
        :param dataset: dl.Dataset
        :param progress: Use this to update the progress of your package
        :return:
        """
        local_path = tempfile.mkdtemp()

        try:

            converted_folder = os.path.join(local_path, dataset.name)
            filters = None
            if query is not None:
                filters = dl.Filters(resource=dl.FiltersResource.ITEM, custom_filter=query)

            pages = dataset.items.list(filters=filters)

            for i_page, page in enumerate(pages):
                for item in page:
                    self._convert_single_item(item=item, local_path=converted_folder)
                progress.update(status='inProgress', progress=(i_page + 1) / pages.total_pages_count)

            zip_filename = os.path.join(local_path,
                                        '{}_{}.zip'.format(dataset.name, int(datetime.datetime.now().timestamp())))
            self._zip_directory(zip_filename=zip_filename, directory=converted_folder)

            zip_item = dataset.items.upload(local_path=zip_filename,
                                            remote_path='/my_converted_annotations',
                                            overwrite=True)

            return zip_item.id

        except Exception:
            # implement exception handling
            pass
        finally:
            shutil.rmtree(local_path)

    def _convert_single_item(self, item, local_path):
        """
        Implement single item conversion here and save converted files to local path
        :param item:
        :return:
        """
        pass

    @staticmethod
    def _zip_directory(zip_filename, directory):
        """
        Method to zip a directory
        :param zip_filename:
        :param directory:
        :return:
        """
        zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    zip_file.write(filepath, arcname=os.path.relpath(filepath, directory))
        finally:
            zip_file.close()


if __name__ == "__main__":
    """
    Run this main to locally debug your package
    """
    dl.packages.test_local_package()
