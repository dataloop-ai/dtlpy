def main():
    """

    :return:
    """
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Curling')
    dataset = project.datasets.get(dataset_name='Practice')

    # upload
    dataset.items.upload(local_path=['/home/project/images/John Morris.jpg',
                                     '/home/project/images/John Benton.jpg',
                                     '/home/project/images/Liu Jinli.jpg'],
                         remote_path='/first_batch')
