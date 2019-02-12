def main():
    """
    Copy folder from project/dataset/folder
    :return:
    """
    from dtlpy import PlatformInterface

    dlp = PlatformInterface()

    # FROM get the annotations from item
    project = dlp.projects.get(project_name='FirstProject')
    dataset_from = project.datasets.get(dataset_name='FirstDataset')
    # ll items from folder
    pages = dataset_from.items.list(query={'filenames': ['/source_folder']})

    # TO post annotations to other item
    project = dlp.projects.get(project_name='SecondProjects')
    dataset_to = project.datasets.get(dataset_name='SecondDataset')

    for page in pages:
        for item in page:
            if page.type == 'dir':
                continue

            # download item
            buffer = dataset_from.items.download(item_id=item.id)
            # upload item
            success = dataset_to.items.upload(filepath=buffer, remote_path='/destination_folder')
