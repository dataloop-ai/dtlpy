def main(first_project_name, second_project_name, first_dataset_name, second_dataset_name):
    """
    Copy folder from project/dataset/folder
    :return:
    """
    import dtlpy as dl

    # Get source project and dataset
    project = dl.projects.get(project_name=first_project_name)
    dataset_from = project.datasets.get(dataset_name=first_dataset_name)
    # filter to get all files of a specific folder
    filters = dl.Filters()
    filters.add(field='type', values='file')  # get only files
    filters.add(field='filename', values='/source_folder/**')  # get all items in folder (recursive)
    pages = dataset_from.items.list(filters=filters)

    # Get destination project and annotations
    project = dl.projects.get(project_name=second_project_name)
    dataset_to = project.datasets.get(dataset_name=second_dataset_name)

    # go over all projects and copy file from src to dst
    for page in pages:
        for item in page:
            # download item (without save to disk)
            buffer = item.download(save_locally=False)
            # give the items name to the buffer
            buffer.name = item.name
            # upload item
            new_item = dataset_to.items.upload(local_path=buffer,
                                               remote_path='/destination_folder')
            print(new_item.filename)
