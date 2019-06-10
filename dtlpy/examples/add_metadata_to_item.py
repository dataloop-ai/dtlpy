def main():
    """
    Add any metadata to item
    :return:
    """
    # import Dataloop SDK
    import dtlpy as dl
    # get dataset
    dataset = dl.projects.get(project_name='Project').datasets.get(dataset_name='Dataset')
    # get item
    item = dataset.items.get(filename='/file')

    # modify metadata
    item.metadata['user']['MyKey'] = 'MyVal'
    # update item
    item.update()
