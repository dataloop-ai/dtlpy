from dtlpy.platform_interface import PlatformInterface
from dtlpy.utilities.videos import Videos

import logging


def main():
    logger = logging.getLogger('dataloop.examples')
    logging.basicConfig(level=logging.INFO)

    dlp = PlatformInterface()

    # login
    # dlp.login()
    #####################
    # create and delete #
    #####################
    project = dlp.projects.create(project_name='MyProject')

    dataset = project.datasets.create(dataset_name='MyDataset',
                                      classes={'pinky': (255, 0, 0), 'the brain': (0, 0, 255)})

    result = project.datasets.delete(dataset_name='MyDataset')

    dlp.projects.delete(project_name='MyProject')

    #########
    # lists #
    #########
    # list projects
    projects = dlp.projects.list().print()

    project = dlp.projects.get(project_name='MyProject').print()

    # list dataset
    datasets = project.datasets.list().print()

    dataset = project.datasets.get(dataset_name='MyDataset').list()

    #######################
    # upload and download #
    #######################
    # upload images
    dataset.items.upload(filepath='/images/000000000036.jpg',
                         remote_path='/dog')

    # upload dataset
    filename = project.datasets.upload(dataset_name='MyDataset',
                                       local_path='/home/images',
                                       upload_options='overwrite')

    # download dataset
    filenames = project.datasets.download(dataset_name='MyDataset',
                                          local_path='/home/images',
                                          download_options='merge')
    # upload video
    Videos.split_and_upload(filepath='/home/videos/messi.mp4',
                            project_name='MyProject',
                            dataset_name='MyDataset',
                            split_pairs=[(0, 5), (10, 20)],
                            remote_path='/')
