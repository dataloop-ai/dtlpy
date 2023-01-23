from behave import given, when, then
import os
import traceback
import shutil
import random
import json
import logging
import xml.etree.ElementTree as Et
from PIL import Image


########################
# to dataloop features #
########################
@given(u'There is a local "{from_format}" dataset in "{local_path}"')
def step_impl(context, from_format, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    content = os.listdir(local_path)
    if from_format != 'coco':
        assert 'labels' in content
    assert 'images' in content

    if from_format == 'yolo':
        assert 'd.names' in content
        context.local_labels_path = os.path.join(local_path, 'd.names')
        context.local_annotations_path = os.path.join(local_path, 'labels')
    elif from_format == 'coco':
        assert 'annotations.json' in content
        context.local_labels_path = None
        context.local_annotations_path = os.path.join(local_path, 'annotations.json')
    elif from_format == 'dataloop':
        pass
    else:
        assert 'classes' in content
        context.local_labels_path = os.path.join(local_path, 'classes')
        context.local_annotations_path = os.path.join(local_path, 'labels')

    context.local_dataset = local_path
    context.local_items_path = os.path.join(local_path, 'images')


@when(u'I convert local "{from_format}" dataset to "{to_format}"')
def step_impl(context, from_format, to_format):
    converter = context.dl.Converter()

    if to_format == 'dataloop':
        converter.upload_local_dataset(
            from_format=from_format,
            dataset=context.dataset,
            local_items_path=context.local_items_path,
            local_annotations_path=context.local_annotations_path,
            local_labels_path=context.local_labels_path
        )
    else:
        converter.convert_directory(
            from_format=from_format,
            to_format=to_format,
            local_path=context.local_dataset,
            dataset=context.dataset
        )


@when(u'I convert platform dataset to "{to_format}" in path "{local_path}"')
def step_impl(context, to_format, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)

    get_items_height_and_width(dataset=context.dataset, to_format=to_format)

    ann_filters = None
    if to_format in ['yolo', 'voc']:
        ann_filters = context.dl.Filters()
        ann_filters.resource = 'annotations'
        ann_filters.add(field='type', values='box')

    converter = context.dl.Converter()
    converter.convert_dataset(
        dataset=context.platform_dataset,
        to_format=to_format,
        annotation_filter=ann_filters,
        local_path=local_path
    )


@given(u'Local path in "{reverse_path}" is clean')
def step_impl(_, reverse_path):
    reverse_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], reverse_path)
    for item in os.listdir(reverse_path):
        if item != 'folder_keeper':
            path = os.path.join(reverse_path, item)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)


@when(u'I reverse dataloop dataset to local "{to_format}" in "{reverse_path}"')
def step_impl(context, to_format, reverse_path):
    reverse_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], reverse_path)
    converter = context.dl.Converter()

    get_items_height_and_width(dataset=context.dataset, to_format=to_format)

    converter.convert_dataset(
        to_format=to_format,
        dataset=context.dataset,
        local_path=reverse_path
    )


@then(u'local "{annotation_format}" dataset in "{src_path}" is equal to reversed dataset in "{dest_path}"')
def step_impl(_, annotation_format, dest_path, src_path):
    dest_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], dest_path)
    src_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], src_path)

    if annotation_format == 'yolo':
        compare_yolo(src_path=src_path, dest_path=dest_path)
    elif annotation_format == 'coco':
        compare_coco(src_path=src_path, dest_path=dest_path)
    elif annotation_format == 'voc':
        compare_voc(src_path=src_path, dest_path=dest_path)
    elif annotation_format == 'dataloop':
        compare_dataloop(src_path=src_path, dest_path=dest_path)
    else:
        raise Exception('Unknown format: {}'.format(annotation_format))


#########################
# from dataloop feature #
#########################
@then(u'Converted "{annotation_format}" dataset in "{dest_path}" is equal to dataset in "{should_be_path}"')
def step_impl(_, annotation_format, dest_path, should_be_path):
    dest_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], dest_path)
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)

    if annotation_format == 'yolo':
        compare_yolo(src_path=should_be_path, dest_path=dest_path)
    elif annotation_format == 'voc':
        compare_voc(src_path=should_be_path, dest_path=dest_path, reverse=False)
    elif annotation_format == 'coco':
        compare_coco(src_path=should_be_path, dest_path=dest_path, reverse=False)
    else:
        raise Exception('Unknown format: {}'.format(annotation_format))


@given(u'There is a platform dataloop dataset from "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    dataset = context.platform_dataset = context.dataset = context.project.datasets.create(
        'platform_dataset_{}'.format(random.randrange(100, 100000)))
    dataset.items.upload(local_path=os.path.join(local_path, 'images'),
                         local_annotations_path=os.path.join(local_path, 'labels'))
    dataset.add_labels(['building', 'rock', 'eye', 'hat', ])


###########
# compare #
###########
def compare_yolo(src_path, dest_path):
    for root, dirs, files in os.walk(src_path):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = src_file.replace(src_path, dest_path).replace('labels', 'yolo')
            _, ext = os.path.splitext(file)
            try:
                if ext == '.txt':
                    assert os.path.isfile(dest_file)
                    assert compare_yolo_files(file_a=src_file, file_b=dest_file)
                elif ext == '.names':
                    dest_file = os.path.join(dest_path, [f for f in os.listdir(dest_path) if f.endswith('.names')][0])
                    with open(src_file, 'r') as fp:
                        src_labels = set([label.strip() for label in fp.readlines()])
                    with open(dest_file, 'r') as fp:
                        dest_labels = set([label.strip() for label in fp.readlines()])
                    assert len(dest_labels) == len(src_labels)
                    logging.error('Source Labels: {}\n Dest Labels: {}'.format(src_labels, dest_labels))
                    assert dest_labels == src_labels
                    for label in src_labels:
                        assert label in dest_labels
            except AssertionError:
                assert False, "yolo files don't match. file: {} \n {}".format(src_file, traceback.format_exc())
            except Exception:
                raise Exception("Error in comparing yolo files. file: {}".format(src_file))


def compare_coco(src_path, dest_path, reverse=True):
    if reverse:
        src_path = os.path.join(src_path, 'annotations.json')
        dest_path = os.path.join(dest_path, 'coco.json')

    with open(src_path, 'r') as f:
        src_coco = json.load(f)
    with open(dest_path, 'r') as f:
        dest_coco = json.load(f)

    assert len(src_coco['images']) == len(dest_coco['images'])
    assert len(src_coco['annotations']) == len(dest_coco['annotations'])

    if reverse:
        dest_categoties_count = 0
        for category in dest_coco['categories']:
            if 'supercategory' in category:
                dest_categoties_count += 1

        assert len(src_coco['categories']) == dest_categoties_count
    else:
        assert len(src_coco['categories']) == len(dest_coco['categories'])


def compare_voc(src_path, dest_path, reverse=True):
    if reverse:
        src_path = os.path.join(src_path, 'labels')
        dest_path = os.path.join(dest_path, 'voc')

    src_content = os.listdir(src_path)
    dest_content = os.listdir(dest_path)

    assert len(src_content) == len(dest_content)

    for f in src_content:
        src_file = os.path.join(src_path, f)
        try:
            assert f in dest_content
            assert compare_voc_files(src_file=src_file, dest_file=os.path.join(dest_path, f))
        except:
            assert False, "voc files don't match. file: {} \n {}".format(src_file, traceback.format_exc())


def compare_dataloop(src_path, dest_path):
    src_path = os.path.join(src_path, 'labels')
    dest_path = os.path.join(dest_path, 'yolo')

    src_content = os.listdir(src_path)
    dest_content = os.listdir(dest_path)

    for f in src_content:
        src_file = os.path.join(src_path, f)
        _, ext = os.path.splitext(f)
        try:
            if ext == '.txt':
                assert f in dest_content
                assert compare_yolo_files(file_a=src_file, file_b=os.path.join(dest_path, f))
            elif ext == '.names':
                with open(src_path, 'r') as fp:
                    src_labels = [label.strip() for label in fp.readlines()]
                with open(os.path.join(dest_path, fp), 'r') as f:
                    dest_labels = [label.strip() for label in fp.readlines()]
                assert len(dest_labels) == len(src_labels)
                for label in src_labels:
                    assert label in dest_labels
        except AssertionError:
            assert False, "yolo files don't match. file: {} \n {}".format(src_file, traceback.format_exc())
        except Exception:
            raise Exception("Error in comparing yolo files. file: {}".format(src_file))


#########
# utils #
#########
def compare_attributes(attributes, obj):
    success = True
    for attr_key, attr_val in attributes.items():
        suc = False
        for elem in obj.iter():
            suc = elem.tag == attr_key and elem.text == str(attr_val)
            suc = suc or elem.text == attr_key
            if suc:
                break
        success = success and suc

    return success


def compare_xml_object(obj_a, obj_b):
    success = True

    try:
        for e in list(obj_a):
            if e.tag == 'bndbox':
                success = success and compare_xml_object(obj_a=e, obj_b=obj_b.find('bndbox'))
            elif e.tag == 'attributes':
                if e.text:
                    attributes = json.loads(e.text.replace("'", '"'))
                    success = success and compare_attributes(attributes=attributes, obj=obj_b)
            else:
                success = success and e.text == obj_b.find(e.tag).text
    except Exception as e:
        success = False

    return success


def compare_objects(src_objects, dest_objects):
    equal = True
    for src_obj in src_objects:
        found_match = False
        for des_obj in dest_objects:
            if compare_xml_object(obj_a=des_obj, obj_b=src_obj):
                found_match = True
                break
        equal = equal and found_match

    return equal


def compare_voc_files(src_file, dest_file):
    src_elem = Et.parse(src_file)
    dest_elem = Et.parse(dest_file)

    src_objects = src_elem.findall('object')
    dest_objects = dest_elem.findall('object')

    success = compare_objects(src_objects=src_objects, dest_objects=dest_objects)

    src_size = src_elem.find('size')
    dest_size = dest_elem.find('size')

    success = success and compare_xml_object(obj_a=src_size, obj_b=dest_size)
    success = success and src_elem.find('filename').text == dest_elem.find('filename').text

    return success


def includes_yolo_line(line, lines):
    includes = False
    split_line = [format(float(val), '.2f') for val in line.split()]

    for l in lines:
        split_l = [format(float(val), '.2f') for val in l.split()]
        line_equal = len(split_l) == len(split_line)
        line_equal = line_equal and \
                     split_l[0] == split_line[0] and \
                     split_l[1] == split_line[1] and \
                     split_l[2] == split_line[2] and \
                     split_l[3] == split_line[3] and \
                     split_l[4] == split_line[4]
        if line_equal:
            includes = line_equal
            break

    return includes


def compare_yolo_files(file_a, file_b):
    f_src = open(file_a, 'r')
    f_dest = open(file_b, 'r')
    src_lines = [line.strip() for line in f_src.readlines()]
    dest_lines = [line.strip() for line in f_dest.readlines()]

    success = len(dest_lines) == len(src_lines)

    if success:
        for line in src_lines:
            success = success and includes_yolo_line(line=line, lines=dest_lines)

    if not success:
        print('Error in files: {}, {}'.format(file_a, file_b))
        print('{}:\n {}'.format(file_a, src_lines))
        print('{}:\n {}'.format(file_b, dest_lines))

    return success


def get_items_height_and_width(dataset, to_format):

    items_shapes = {
        "picture3 copy.jpg": {
            "width": 1200,
            "height": 800},
        "lena copy 2.png": {
            "width": 512,
            "height": 512
        },
        "picture2 copy 11.jpg": {
            "width": 648,
            "height": 365
        }
    }

    for page in dataset.items.list():
        for item in page:
            if item.width is None or item.height is None:
                if to_format == 'coco':
                    try:
                        height = item.metadata['user']['height']
                        width = item.metadata['user']['width']
                    except Exception:
                        height = items_shapes[item.name]['height']
                        width = items_shapes[item.name]['width']

                    item.metadata['system']['height'] = height
                    item.metadata['system']['width'] = width
                elif to_format in ['voc', 'yolo']:
                    im = Image.open(item.download(save_locally=False))
                    item.metadata['system']['height'] = im.size[1]
                    item.metadata['system']['width'] = im.size[0]
                item.update(system_metadata=True)


@then(u'The converter do not overwrite the existing label')
def step_impl(context):
    dataset = context.dl.datasets.get(dataset_id=context.dataset.id)
    for label in dataset.labels:
        if label.tag == context.nested_labels[0]['label_name']:
            assert label.color == context.nested_labels[0]['color'], 'The converter overwrite the existing label'
