def main():
    """

    :return:
    """
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Curling')
    dataset = project.datasets.get(dataset_name='Practice')

    # upload specific files
    dataset.items.upload(local_path=['/home/project/images/John Morris.jpg',
                                     '/home/project/images/John Benton.jpg',
                                     '/home/project/images/Liu Jinli.jpg'],
                         remote_path='/first_batch')

    # upload all files in a folder
    dataset.items.upload(local_path='/home/project/images',
                         remote_path='/first_batch')
