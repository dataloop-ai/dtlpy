def main():
    """
    Convert yolo annotation and images to Dataloop
    Yolo annotations format:
    For each image there is a text file with same name that has a list of box location and label index
    """
    import dtlpy as dl
    from dtlpy.utilities.annotations import ImageAnnotation
    from PIL import Image
    import os

    dataset_path = r'E:\Projects\Images'
    labels_filepath = r'E:\Projects\obj.names'

    # init platform and get dataset
    project = dl.projects.get(project_name='MyProject')
    dataset = project.datasets.get(dataset_name='MyDataset')

    # read all images from local dataset
    img_filepaths = list()
    for path, subdirs, files in os.walk(dataset_path):
        for filename in files:
            striped, ext = os.path.splitext(filename)
            if ext in ['.jpeg']:
                img_filepaths.append(os.path.join(path, filename))

    # get labels from file
    with open(labels_filepath, 'r') as f:
        labels = {i_line: label.strip() for i_line, label in enumerate(f.readlines())}

    for filepath in img_filepaths:
        # get image height and width
        img = Image.open(filepath)
        width, height = img.size()
        # upload item to platform
        item = dataset.items.update(filepath=filepath)

        # get YOLO annotations
        _, ext = os.path.splitext(filepath)
        annotation_filepath = filepath.replace(ext, '.txt')
        with open(annotation_filepath, 'r') as f:
            annotations = f.read().split('\n')

        builder = item.annotations.builder()
        # convert to Dataloop annotations
        for annotation in annotations:
            if not annotation:
                continue
            # convert annotation format
            elements = annotation.split(" ")
            label_id = elements[0]

            xminAddxmax = float(elements[1]) * (2.0 * float(width))
            yminAddymax = float(elements[2]) * (2.0 * float(height))

            w = float(elements[3]) * float(width)
            h = float(elements[4]) * float(height)

            left = (xminAddxmax - w) / 2
            top = (yminAddymax - h) / 2
            right = left + w
            bottom = top + h

            # add to annotations
            builder.add(dl.Box(annotation_definition=dl.Box(top=10,
                                             left=10,
                                             bottom=100,
                                             right=100,
                                             label='person')))
        # upload all annotations of an item
        builder.upload()
