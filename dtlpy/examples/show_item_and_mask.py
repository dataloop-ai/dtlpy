def main(project_name, dataset_name, item_remote_path):
    """
    Download and show an image with it's annotations
    :return:
    """
    import dtlpy as dl
    from PIL import Image
    import numpy as np

    # Get project and dataset
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)
    # Get item
    item = dataset.items.get(filepath=item_remote_path)

    # download item as a buffer
    buffer = item.download(save_locally=False)

    # open image
    image = Image.open(buffer)

    # download annotations
    annotations = item.annotations.show(width=image.size[0],
                                        height=image.size[1],
                                        thickness=3)
    annotations = Image.fromarray(annotations.astype(np.uint8))

    # show separate
    annotations.show()
    image.show()

    # plot on top
    image.paste(annotations, (0, 0), annotations)
    image.show()
