import behave
import os
import json
import filecmp
import os.path
import xmltodict


@behave.given('I use "{converter_name}" converter to upload items with annotations to the dataset using the given params')
def step_impl(context, converter_name):
    context.items_path = None
    context.labels_path = None
    context.annotations_path = None

    for parameter in context.table.rows:
        if parameter.cells[0] == "local_items_path":
            context.items_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "local_labels_path":
            context.labels_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

        if parameter.cells[0] == "local_annotations_path":
            context.annotations_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

    converter = context.dl.Converter()
    converters_list = {
        "COCO": context.dl.AnnotationFormat.COCO,
        "YOLO": context.dl.AnnotationFormat.YOLO,
        "VOC": context.dl.AnnotationFormat.VOC,
    }

    converter.upload_local_dataset(
        from_format=converters_list[converter_name],
        dataset=context.dataset,
        local_items_path=context.items_path,
        local_labels_path=context.labels_path,
        local_annotations_path=context.annotations_path
    )


@behave.given('I download the dataset items annotations in "{converter_name}" format using the given params')
def step_impl(context, converter_name):
    context.local_path = None

    converter = context.dl.Converter()
    converters_list = {
        "COCO": context.dl.AnnotationFormat.COCO,
        "YOLO": context.dl.AnnotationFormat.YOLO,
        "VOC": context.dl.AnnotationFormat.VOC,
    }

    for parameter in context.table.rows:
        if parameter.cells[0] == "local_path":
            context.local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], parameter.cells[1])

    context.downloaded_annotations = converter.convert_dataset(
        dataset=context.dataset,
        to_format=converters_list[converter_name],
        local_path=context.local_path
    )


@behave.then('I use "{converter_name}" format to compare the uploaded annotations with the downloaded annotations')
def step_impl(context, converter_name):
    converters_list = {
        "COCO": coco_annotations_compare,
        "YOLO": yolo_annotations_compare,
        "VOC": voc_annotations_compare,
    }

    converters_list[converter_name](context)


def coco_annotations_compare(context):
    with open(context.annotations_path, 'r') as annotations_file:
        context.uploaded_annotations = json.load(annotations_file)

    # Sorting images lists
    for uploaded_image in context.uploaded_annotations['images']:
        uploaded_image.pop('id')

    for downloaded_image in context.downloaded_annotations['images']:
        downloaded_image.pop('id')

    context.uploaded_annotations['images'] = sorted(context.uploaded_annotations['images'],
                                                    key=lambda img: img['file_name'])

    context.downloaded_annotations['images'] = sorted(context.downloaded_annotations['images'],
                                                      key=lambda img: img['file_name'])

    # Removing info field
    context.uploaded_annotations.pop('info')
    context.downloaded_annotations.pop('info')

    # Sorting annotations lists
    for uploaded_annotation in context.uploaded_annotations['annotations']:
        uploaded_annotation.pop('id')
        uploaded_annotation.pop('image_id')

    for downloaded_annotation in context.downloaded_annotations['annotations']:
        downloaded_annotation.pop('id')
        downloaded_annotation.pop('image_id')

    context.uploaded_annotations['annotations'] = sorted(context.uploaded_annotations['annotations'],
                                                         key=lambda img: img['area'])

    context.downloaded_annotations['annotations'] = sorted(context.downloaded_annotations['annotations'],
                                                           key=lambda img: img['area'])

    # Comparing the sorted files
    assert context.downloaded_annotations == context.downloaded_annotations


def yolo_annotations_compare(context):
    # Comparing labels
    with open(context.labels_path, 'r') as uploaded_labels_file:
        uploaded_labels = uploaded_labels_file.readlines()
        downloaded_labels_path = os.path.join(context.local_path, context.dataset.name+".names")

        with open(downloaded_labels_path, 'r') as downloaded_labels_file:
            downloaded_labels = downloaded_labels_file.readlines()
            assert uploaded_labels == downloaded_labels

    # Comparing annotations
    downloaded_annotations_path = os.path.join(context.local_path, "yolo")

    # Function to compare txt files of type yolo
    def compare_directory_files_yolo(dir1, dir2):
        dirs_cmp = filecmp.dircmp(dir1, dir2)
        # Compare the directories structure
        if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
            return False

        # Compare files data
        for item in os.listdir(dir1):
            if item.endswith('.txt'):
                file1_path = os.path.join(dir1, item)
                file2_path = os.path.join(dir2, item)

                with open(file1_path, 'r') as annotations_file1:
                    file1 = annotations_file1.readlines()

                with open(file2_path, 'r') as annotations_file2:
                    file2 = annotations_file2.readlines()

                file1.sort()
                file2.sort()

                file1_split_values = []
                file2_split_values = []

                # Floor the data for accuracy of 10 digits after the floating point
                for i in range(len(file1)):
                    file1_split_values.append(['{:.10f}'.format(float(i)) for i in file1[i].split()])
                    file2_split_values.append(['{:.10f}'.format(float(i)) for i in file2[i].split()])

                # Comparing the sorted files
                assert file1_split_values == file2_split_values, "mismatch data on file: " + item

        for common_dir in dirs_cmp.common_dirs:
            new_dir1 = os.path.join(dir1, common_dir)
            new_dir2 = os.path.join(dir2, common_dir)
            if not compare_directory_files_yolo(new_dir1, new_dir2):
                return False
        return True

    assert compare_directory_files_yolo(context.annotations_path, downloaded_annotations_path)


def voc_annotations_compare(context):
    downloaded_annotations_path = os.path.join(context.local_path, "voc")

    # Function to compare xml files of type voc
    def compare_directory_files_voc(dir1, dir2):
        # Compare the directories structure
        dirs_cmp = filecmp.dircmp(dir1, dir2)
        if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
            return False

        # Compare files data
        for item in os.listdir(dir1):
            if item.endswith('.xml'):
                file1_path = os.path.join(dir1, item)
                file2_path = os.path.join(dir2, item)

                with open(file1_path, 'r') as annotations_file1:
                    file1_json = xmltodict.parse(annotations_file1.read())

                with open(file2_path, 'r') as annotations_file2:
                    file2_json = xmltodict.parse(annotations_file2.read())

                # Sorting annotations list
                if isinstance(file1_json['annotation']['object'], list) and isinstance(file2_json['annotation']['object'], list):
                    file1_json['annotation']['object'] = sorted(
                        file1_json['annotation']['object'],
                        key=lambda obj: (obj['name'],
                                         obj['bndbox']['xmin'], obj['bndbox']['ymin'], obj['bndbox']['xmax'], obj['bndbox']['ymax'])
                    )

                    file2_json['annotation']['object'] = sorted(
                        file2_json['annotation']['object'],
                        key=lambda obj: (obj['name'],
                                         obj['bndbox']['xmin'], obj['bndbox']['ymin'], obj['bndbox']['xmax'], obj['bndbox']['ymax'])
                    )

                    for obj1_attr in file1_json['annotation']['object']:
                        obj1_attr.pop('attributes')

                    for obj2_attr in file2_json['annotation']['object']:
                        obj2_attr.pop('attributes')

                else:
                    file1_json['annotation']['object'].pop('attributes')
                    file2_json['annotation']['object'].pop('attributes')

                # Comparing the sorted files
                assert file1_json == file2_json, "mismatch data on file:" + item

        # Dive to deeper directories
        for common_dir in dirs_cmp.common_dirs:
            new_dir1 = os.path.join(dir1, common_dir)
            new_dir2 = os.path.join(dir2, common_dir)
            if not compare_directory_files_voc(new_dir1, new_dir2):
                return False
        return True

    assert compare_directory_files_voc(context.annotations_path, downloaded_annotations_path)
