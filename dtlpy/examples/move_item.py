def main():
    """
    Move items to another folder in platform
    :return:
    """
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Ninja Turtles')
    dataset = project.datasets.get(dataset_name='Splinter')

    # Get all items from the source folder
    filters = dl.Filters()
    filters.add(field='filename', values='/fighting/**')  # take files from the directory only (recursive)
    filters.add(field='type', values='file')  # only files
    pages = dataset.items.list(filters=filters)

    dst_folder = '/fighting_shredder'
    # iterate through items
    for page in pages:
        for item in page:
            # move item
            item.move(new_path=dst_folder)
