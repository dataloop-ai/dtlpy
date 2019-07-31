def main():
    """
    This is an example how to upload files and annotations to Dataloop platform.
    Image folder contains the images to upload.
    Annotations folder contains json file of the annotations. Same name as the image.
    We read the images one by one and create the Dataloop annotations using the annotation builder.
    Finally, we upload both the image and the matching annotations

    :return:
    """
    import json
    import os
    import dtlpy as dl

    # Get project and dataset
    project = dl.projects.get(project_name='Yachts')
    dataset = project.datasets.get(dataset_name='Open Seas')

    images_folder = '/home/local/images'
    annotations_folder = '/home/local/annotations'

    for img_filename in os.listdir(images_folder):
        # get the matching annotations json
        _, ext = os.path.splitext(img_filename)
        ann_filename = os.path.join(annotations_folder, img_filename.replace(ext, '.json'))
        img_filename = os.path.join(images_folder, img_filename)

        # Upload or get annotations from platform (if already exists)
        item = dataset.items.upload(local_path=img_filename,
                                    remote_path='/in_storm',
                                    overwrite=False)
        assert isinstance(item, dl.Item)

        # read annotations from file
        with open(ann_filename, 'r') as f:
            annotations = json.load(f)

        # create a Builder instance and add all annotations to it
        builder = item.annotations.builder()
        for annotation in annotations:
            # line format if 4 points of bbox
            # this is where you need to update according to your annotation format
            label_id = annotation['label']
            left = annotation['left']
            top = annotation['top']
            right = annotation['right']
            bottom = annotation['bottom']
            builder.add(annotation_definition=dl.Box(top=top,
                                                     left=left,
                                                     bottom=bottom,
                                                     right=right,
                                                     label=str(label_id)))

        # upload annotations
        item.annotations.upload(builder)
