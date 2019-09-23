def main(project_name, dataset_name, remote_filepath):
    """
    Copy annotations between items
    :return:
    """
    import dtlpy as dl

    # FROM get the annotations from item
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)
    item = dataset.items.get(filepath=remote_filepath)

    # get annotations
    annotations = item.annotations.list()

    # delete first annotation
    ann = annotations[0]
    ann.delete()

    ### Or - to delete all annotations ###

    # get annotations
    annotations = item.annotations.list()

    # delete first annotation
    annotations.delete()
