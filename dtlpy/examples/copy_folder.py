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
    pages = dataset_from.items.list(filters=dl.Filters(filenames='/source_folder',  # take files from the directory only
                                                       itemType='file'  # only files
                                                       ))

    # TO post annotations to other item
    project = dl.projects.get(project_name='SecondProjects')
    dataset_to = project.datasets.get(dataset_name='SecondDataset')

    for page in pages:
        for item in page:
            # download item (without save to disk)
            buffer = item.download(save_locally=False)
            # upload item
            new_item = dataset_to.items.upload(filepath=buffer,
                                               remote_path='/destination_folder',
                                               uploaded_filename=item.name)
            print(new_item.filename)
