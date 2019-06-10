def main():
    """
    Copy folder from project/dataset/folder
    :return:
    """
    import dtlpy as dl

    # FROM get the annotations from item
    project = dl.projects.get(project_name='FirstProject')
    dataset_from = project.datasets.get(dataset_name='FirstDataset')
    # ll items from folder
    pages = dataset_from.items.list(query={'filenames': ['/source_folder']})

    # TO post annotations to other item
    project = dl.projects.get(project_name='SecondProjects')
    dataset_to = project.datasets.get(dataset_name='SecondDataset')

    for page in pages:
        for item in page:
            if page.type == 'dir':
                continue

            # download item
            buffer = item.download(save_locally=False)
            # upload item
            success = dataset_to.items.update(filepath=buffer, remote_path='/destination_folder')
