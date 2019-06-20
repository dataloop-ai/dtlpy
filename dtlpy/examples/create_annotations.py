def main():
    import dtlpy as dl
    import numpy as np
    import matplotlib.pyplot as plt

    # Get working dataset
    dataset = dl.datasets.get()
    # get item from platform
    item = dataset.items.get(filepath='/image.jpg')
    # Create a builder instance

    builder = item.annotations.builder()

    # add annotations of type box and label person
    builder.add(annotation_definition=dl.Box(top=10,
                                             left=10,
                                             bottom=100,
                                             right=100,
                                             label='person'))
    # add annotations of type point with attribute
    builder.add(annotation_definition=dl.Point(x=80,
                                               y=80,
                                               label='right eye'),
                attribute=['blue'])
    # add annotations of type polygon
    builder.add(annotation_definition=dl.Polyline(geo=[[80, 40],
                                                       [100, 120],
                                                       [110, 130]],
                                                  label='arm'))
    # create a mask
    mask = np.zeros(shape=(item.height, item.width))
    # mark some part in the middle
    mask[50:100, 200:250] = 1
    # add annotations of type segmentation
    builder.add(annotation_definition=dl.Segmentation(geo=mask,
                                                      label='face'))

    # plot the all of the annotations you created
    plt.figure()
    plt.imshow(builder.show())
    for annotation in builder:
        plt.figure()
        plt.imshow(annotation.show())
        plt.title(annotation.label)
    # upload annotations to the item
    item.annotations.upload(builder)