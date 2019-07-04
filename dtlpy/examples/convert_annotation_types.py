def main():
    """
    Convert annotation types
    :return:
    """
    from PIL import Image
    import matplotlib.pyplot as plt
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Toilet Paper')
    dataset = project.datasets.get(dataset_name='Extra Soft')

    # Get item and binaries
    item = dataset.items.get(filepath='/with_puppies.jpg')
    buffer = item.download(save_locally=False)

    #######################################
    # Convert mask annotations to polygon #
    #######################################
    img = Image.open(buffer)
    builder = item.annotations.builder()
    builder.add(dl.Polygon.from_segmentation(mask=mask,  # binary mask of the annotation
                                             label='roll'))
    # plot the annotation
    plt.figure()
    plt.imshow(builder.show())
    # plot annotation on the image
    plt.figure()
    plt.imshow(builder.show(image=img))

    # upload annotation to platform
    item.annotations.update(builder)

    #######################################
    # Convert polygon annotations to mask #
    #######################################
    img = Image.open(buffer)
    builder = item.annotations.builder()
    builder.add(dl.Segmentation.from_polygon(geo=[[x1, y1], [x2, y2], [x3, y3]],  # list of coordinates
                                             shape=img.size[::-1],  # (h,w)
                                             label='roll'))
    # plot the annotation
    plt.figure()
    plt.imshow(builder.show())
    # plot annotation on the image
    plt.figure()
    plt.imshow(builder.show(image=img))

    # upload annotation to platform
    item.annotations.update(builder)
