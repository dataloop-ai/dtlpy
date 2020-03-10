import behave
import json
import os
from PIL import Image
import io
import random
from multiprocessing.pool import ThreadPool
import logging
import time


@behave.given(u'There are items, path = "{item_path}"')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    dataset = context.dataset
    dl = context.dl

    # import dtlpy as dl
    # assert isinstance(dataset, dl.entities.Dataset)

    directory = None
    annotated_label = None
    annotated_type = None
    name_dir = None
    metadata = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == 'directory':
            if param[1] != 'None':
                directory = json.loads(param[1])
        elif param[0] == 'annotated_label':
            if param[1] != 'None':
                annotated_label = json.loads(param[1])
        elif param[0] == 'annotated_type':
            if param[1] != 'None':
                annotated_type = json.loads(param[1])
        elif param[0] == 'name':
            if param[1] != 'None':
                name_dir = json.loads(param[1])
        elif param[0] == 'metadata':
            if param[1] != 'None':
                metadata = json.loads(param[1])

    image = Image.open(item_path)
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')

    def upload(i_buffer, remote_path, do_next=None, i_ann_type=None, i_label=None, i_meta=None):
        item = dataset.items.upload(local_path=i_buffer, remote_path=remote_path)

        if do_next == 'directory':
            assert isinstance(item, dl.Item)
        elif do_next == 'label':
            assert isinstance(item, dl.Item)
            ann = dl.Annotation.new(annotation_definition=dl.Point(y=100, x=200, label=i_label),
                                    item=item)
            ann.upload()
        elif do_next == 'type':
            assert isinstance(item, dl.Item)

            if i_ann_type == 'box':
                bottom = random.randrange(0, 500)
                top = random.randrange(0, 500)
                right = random.randrange(0, 500)
                left = random.randrange(0, 500)
                ann = dl.Annotation.new(
                    annotation_definition=dl.Box(label="test_label", bottom=bottom, top=top, left=left, right=right),
                    item=item)

            elif i_ann_type == 'polygon':
                geo = [
                    (random.randrange(0, 500), random.randrange(0, 500)),
                    (random.randrange(0, 500), random.randrange(0, 500)),
                    (random.randrange(0, 500), random.randrange(0, 500)),
                    (random.randrange(0, 500), random.randrange(0, 500)),
                    (random.randrange(0, 500), random.randrange(0, 500)),
                    (random.randrange(0, 500), random.randrange(0, 500)),
                ]
                ann = dl.Annotation.new(
                    annotation_definition=dl.Polygon(label="test_label", geo=geo),
                    item=item)
            else:
                return

            ann.upload()
        elif do_next == 'metadata':
            assert isinstance(item, dl.Item)

            # put metadata field
            i_metadata_field = i_meta.split('.')
            i_field_pointer = item.metadata
            for field in i_metadata_field:
                if field not in i_field_pointer:
                    if i_metadata_field.index(field) == len(i_metadata_field) - 1:
                        i_field_pointer[field] = True
                    else:
                        i_field_pointer[field] = dict()
                        i_field_pointer = i_field_pointer[field]
            item.update()

    pool = ThreadPool(processes=32)

    # directory
    name = 'dir.jpg'
    for dir_path in directory:
        for i in range(int(directory[dir_path])):

            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')

            buffer.name = '{}_{}'.format(i, name)

            pool.apply_async(func=upload,
                             kwds={
                                 'i_buffer': buffer,
                                 'remote_path': dir_path
                             })

    # name
    name = '.jpg'
    for item_name in name_dir:
        for i in range(int(name_dir[item_name])):
            dir_name = '/'
            for j in range(random.randrange(0, 5)):
                dir_name = '{}{}/'.format(dir_name, random.randrange(0, 1000))

            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')

            buffer.name = '{}_{}_{}{}'.format(random.randrange(0, 100), item_name, random.randrange(0, 100),
                                              name)

            pool.apply_async(func=upload,
                             kwds={
                                 'i_buffer': buffer,
                                 'remote_path': dir_name
                             })

    # annotated label
    name = 'label.jpg'
    for label in annotated_label:
        for i in range(int(annotated_label[label])):
            dir_name = '/'
            for j in range(random.randrange(0, 5)):
                dir_name = '{}{}/'.format(dir_name, random.randrange(0, 1000))

            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')

            buffer.name = '{}_{}_{}'.format(label, i, name)

            pool.apply_async(func=upload,
                             kwds={
                                 'i_buffer': buffer,
                                 'remote_path': dir_name,
                                 'do_next': 'label',
                                 'i_label': label
                             })

    # annotated type
    name = 'type.jpg'
    for ann_type in annotated_type:
        for i in range(int(annotated_type[ann_type])):
            dir_name = '/'
            for j in range(random.randrange(0, 5)):
                dir_name = '{}{}/'.format(dir_name, random.randrange(0, 1000))

            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')

            buffer.name = '{}_{}_{}'.format(ann_type, i, name)

            pool.apply_async(func=upload,
                             kwds={
                                 'i_buffer': buffer,
                                 'remote_path': dir_name,
                                 'do_next': 'type',
                                 'i_ann_type': ann_type
                             })

    # metadata
    name = 'metadata.jpg'
    for meta in metadata:
        for i in range(int(metadata[meta])):
            dir_name = '/'
            for j in range(random.randrange(0, 5)):
                dir_name = '{}{}/'.format(dir_name, random.randrange(0, 1000))

            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')

            buffer.name = '{}_{}_{}'.format(meta.replace('.', '_'), i, name)

            pool.apply_async(func=upload,
                             kwds={
                                 'i_buffer': buffer,
                                 'remote_path': dir_name,
                                 'do_next': 'metadata',
                                 'i_meta': meta
                             })

    pool.close()
    pool.join()
    pool.terminate()


@behave.when(u'I create filters')
def step_impl(context):
    context.filters = context.dl.Filters()


@behave.when(u'I add field "{field}" with values "{values}" and operator "{operator}"')
def step_impl(context, field, values, operator):
    if operator == 'None':
        operator = None

    if values == 'True':
        values = True
    elif values == 'False':
        values = False
    elif values.startswith('{'):
        values = json.loads(values)

    if field.startswith('{'):
        field = json.loads(field)

    context.filters.add(field=field, values=values, operator=operator)


@behave.when(u'I join field "{field}" with values "{values}" and operator "{operator}"')
def step_impl(context, field, values, operator):
    if operator == 'None':
        operator = None

    if values == 'True':
        values = True
    elif values == 'False':
        values = False
    elif values.startswith('{'):
        values = json.loads(values)

    if field.startswith('{'):
        field = json.loads(field)

    context.filters.add_join(field=field, values=values, operator=operator)


@behave.when(u'I list items with filters')
def step_impl(context):
    context.items_list = context.dataset.items.list(filters=context.filters)


@behave.then(u'I receive "{count}" items')
def step_impl(context, count):
    if len(context.items_list.items) != int(count):
        logging.info('filter: {}'.format(context.filters.prepare()))
        logging.error('Filtering error. expected item count: {}. received item count:{}'.format(int(count), context.items_list.items_count))
        assert False


@behave.when(u'I update items with filters, field "{field}"')
def step_impl(context, field):
    updated_value = {
        'metadata': {
            'user': {
                field: True
            }
        }
    }
    context.dataset.items.update(filters=context.filters, update_values=updated_value)


@behave.when(u'I delete items with filters')
def step_impl(context):
    context.dataset.items.delete(filters=context.filters)
