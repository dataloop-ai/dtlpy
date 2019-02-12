def main():
    """
    Convert polygon annotations to mask
    :return:
    """
    from dtlpy import PlatformInterface
    from dtlpy.utilities.annotations import ImageAnnotation
    from PIL import Image
    import matplotlib.pyplot as plt

    dlp = PlatformInterface()
    project_name = 'MyProject'
    dataset_name = 'MyDataset'
    item_path = '/img.jpg'

    dataset = dlp.projects.get(project_name=project_name).datasets.get(dataset_name=dataset_name)
    item = dataset.items.get(filepath=item_path)
    buffer = dataset.items.download(item_id=item.id, save_locally=False)

    img = Image.open(buffer)
    ann = ImageAnnotation()
    ann.annotations = item.annotations.list
    new_ann = ImageAnnotation()
    for annotation in ann.annotations:
        new_ann.add_annotation(pts=annotation['coordinates'],
                               label=annotation['label'],
                               annotation_type='segment',
                               to_annotation_type='binary',
                               color=dataset.classes[annotation['label']],
                               img_shape=img.size[::-1])
    new_mask = new_ann.to_image(img_shape=img.size[::-1],
                                colors_dict=dataset.classes)
    plt.figure()
    plt.imshow(new_mask)
