def main(first_project_name, second_project_name, first_dataset_name, second_dataset_name, first_remote_filepath, second_remote_filepath):
    """
    Copy annotations between items
    :return:
    """
    import dtlpy as dl

    # FROM get the annotations from item
    project = dl.projects.get(project_name=first_project_name)
    dataset = project.datasets.get(dataset_name=first_dataset_name)
    item = dataset.items.get(filepath=first_remote_filepath)

    # get annotations
    annotations = item.annotations.list()

    # TO post annotations to other item
    project = dl.projects.get(project_name=second_project_name)
    dataset = project.datasets.get(dataset_name=second_dataset_name)
    item = dataset.items.get(filepath=second_remote_filepath)

    # post
    item.annotations.upload(annotations=annotations)
