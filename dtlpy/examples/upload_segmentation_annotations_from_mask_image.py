"""

"""


def main():
    from PIL import Image
    import numpy as np
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Presidents')
    dataset = project.datasets.get(dataset_name='William Henry Harrison')

    # image filepath
    image_filepath = '/home/images/with_family.png'
    # annotations filepath - RGB with color for each label
    annotations_filepath = '/home/masks/with_family.png'

    # upload item to root directory
    item = dataset.items.upload(local_path=image_filepath,
                                remote_path='/')

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
        # add annotation to builder
        builder.add(annotation_definition=dl.Segmentation(geo=class_mask,
                                                          label=str(i)))
    # upload all annotations
    item.annotations.upload(builder)
