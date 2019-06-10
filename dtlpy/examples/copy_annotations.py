def main():
    """
    Copy annotations between items
    :return:
    """
    import dtlpy as dl

    # FROM get the annotations from item
    project = dl.projects.get(project_name='FirstProject')
    dataset = project.datasets.get(dataset_name='FirstDataset')
    item = dataset.items.get(filepath='/image1.jpg')

    # annotations
    annotations = item.annotations.list()

    # TO post annotations to other item
    project = dl.projects.get(project_name='SecondProjects')
    dataset = project.datasets.get(dataset_name='SecondDataset')
    item = dataset.items.get(filepath='/image2.jpg')
    # post
    item.annotations.upload(annotations=annotations)
