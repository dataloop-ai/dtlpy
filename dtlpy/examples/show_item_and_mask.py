def main():
    """
    Download and show an image with it's annotations
    :return:
    """
    from dtlpy.platform_interface import PlatformInterface
    from PIL import Image

    dlp = PlatformInterface()

    project_name = 'MyProject'
    dataset_name = 'MyDataset'
    item_name = '/path/to/image.jpg'

    # get dataset from platform
    dataset = dlp.projects.get(project_name=project_name).datasets.get(dataset_name=dataset_name)

    # get item
    item = dataset.items.get(filepath=item_name)

    # download item as a buffer
    buffer = dataset.items.download(filepath=item_name, save_locally=False)

    # open image
    image = Image.open(buffer)

    # download annotations
    annotations = item.annotations.to_mask(width=image.size[1], height=image.size[0])
    annotations = Image.fromarray(annotations)

    # show separate
    annotations.show()
    image.show()

    # plot on top
    image.paste(annotations, (0, 0), annotations)
    image.show()


