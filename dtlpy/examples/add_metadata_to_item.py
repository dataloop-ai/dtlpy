def main(project_name, dataset_name, item_path):
    """
    Add any metadata to item
    :return:
    """
    # import Dataloop SDK
    import dtlpy as dl

    # get dataset
    dataset = dl.projects.get(project_name=project_name).datasets.get(dataset_name=dataset_name)

    # upload and claim item
    item = dataset.items.upload(local_path=item_path)

    # modify metadata
    item.metadata['user'] = dict()
    item.metadata['user']['MyKey'] = 'MyVal'
    # update and reclaim item
    item = item.update()

    # item in platform should have section 'user' in metadata with field 'MyKey' and value 'MyVal'
