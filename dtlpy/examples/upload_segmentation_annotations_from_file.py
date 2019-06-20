"""

"""


def main():
    from PIL import Image
    import numpy as np
    import dtlpy as dl
    from dtlpy.utilities.annotations import ImageAnnotation

    # get project and dataset
    dataset = dl.projects.get('MyProject').datasets.get('MyDataset')

    # image filepath
    image_filepath = r'E:\Images\img_000.png'
    # annotations filepath - RGB with color for each label
    annotations_filepath = r'E:\annotations\img_000.png'

    # upload item to root directory
    item = dataset.items.update(image_filepath, remote_path='/')

    # read mask from file
    mask = np.array(Image.open(annotations_filepath))

    # get unique color (labels)
    unique_colors = np.unique(mask.reshape(-1, mask.shape[2]), axis=0)

    # init dataloop annotations builder
    builder = item.annotations.builder()
    # for each label - create a dataloop mask annotation
    for i, color in enumerate(unique_colors):
        print(color)
        if i == 0:
            # ignore background
            continue
        # get mask of same color
        class_mask = np.all(color == mask, axis=2)
        # # plot mask for debug
        # plt.figure()
        # plt.imshow(class_mask)
        # add annotation to builder
        builder.add(annotation_definition=dl.Segmentation(geo=class_mask, label=str(i)))
    # upload all annotations
    builder.upload()
