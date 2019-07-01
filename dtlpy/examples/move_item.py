def main():
    """
    Move items to another folder in platform
    :return:
    """
    import dtlpy as dl

    # FROM get the annotations from item
    project = dl.projects.get(project_name='Project')
    dataset = project.datasets.get(dataset_name='Dataset')
    # ll items from folder
    pages = dataset_from.items.list(filters=dl.Filters(filenames='/source_folder',  # take files from the directory only
                                                       itemType='file'  # only files
                                                       ))

    new_folder = '/new_folder'
    # iterate through items
    for page in pages:
        for item in page:
            # move item
            item.move(new_path=new_folder)