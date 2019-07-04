def main():
    """
    Download and show an image with it's annotations
    :return:
    """
    import dtlpy as dl
    from PIL import Image
    import numpy as np

    # Get project and dataset
    project = dl.projects.get(project_name='Ants')
    dataset = project.datasets.get(dataset_name='Acrobat')
    # Get item
    item = dataset.items.get(filepath='/ants/from/house.jpg')

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
