import json
import os

import numpy as np

import dtlpy as dl
from dtlpy.utilities.annotations import ImageAnnotation

"""

"""


def main():
    """
    This is an example how to upload files and annotations to Dataloop platform.
    Image folder contains the images to upload.
    Annotations folder contains json file of the annotations. Same name as the image.
    We read the images one by one and create the Dataloop annotations using the annotation builder.
    Finally, we upload both the image and the matching annotations

    :return:
    """
    # local path to images folder
    images_folder = 'images'
    # local path to annotations folder
    annotations_folder = 'annotations'

    project_name = 'Example Project'
    dataset_name = 'Example Dataset'

    # init platform
    # dl.login()
    dataset = dl.projects.get(project_name=project_name).datasets.get(dataset_name=dataset_name)

    for img_filename in os.listdir(images_folder):
        # get the matching annotations json
        _, ext = os.path.splitext(img_filename)
        ann_filename = os.path.join(annotations_folder, img_filename.replace(ext, '.json'))
        img_filename = os.path.join(images_folder, img_filename)

        # read annotations from file
        with open(ann_filename, 'r') as f:
            data = json.load(f)
            # data = f.read().split('\n')

        # create a Builder instance and add all annotations to it
        builder = item.annotations.builder()
        for line in data:
            if not line:
                continue
            # line format if 4 points of bbox
            # this is where you need to update according to your annotation format
            label_id, left, top, right, bottom = np.array(line.split()[:5]).astype(float)
            builder.add(
                annotation_definition=dl.Box(top=top,
                                             left=left,
                                             bottom=bottom,
                                             right=right,
                                             label=str(label_id))
            )

        # upload item to platform
        item = dataset.items.update(filepath=img_filename,
                                    remote_path='/')
        # upload annotations
        builder.upload()
