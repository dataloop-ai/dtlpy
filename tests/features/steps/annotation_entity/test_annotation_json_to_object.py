import logging
import behave
import json
import random as r
import time


@behave.then(u'Object "{entity}" to_json() equals to Platform json.')
def step_impl(context, entity):
    if entity != 'Annotations':
        entity = entity.lower()
        url_path = "/{}s/{}".format(entity, getattr(context, entity).id)
        success, response = getattr(context, entity)._client_api.gen_request(
            req_type="get",
            path=url_path
        )
        
        entity_to_json = getattr(context, entity).to_json()
        response = response.json()

        assert success
        if entity == 'item':
            if 'metadata' in response and 'system' in response['metadata']:
                response['metadata']['system'].pop('executionLogs', None)
            if 'metadata' in entity_to_json and 'system' in entity_to_json['metadata']:
                entity_to_json['metadata']['system'].pop('executionLogs', None)
        elif entity == 'service':
            if 'runtime' in response:
                if 'autoscaler' not in response['runtime']:
                    response['runtime']['autoscaler'] = None
        if entity_to_json != response:
            logging.error('FAILED: response json is:\n{}\n\nto_json is:\n{}'.format(json.dumps(response,
                                                                                               indent=2),
                                                                                    json.dumps(entity_to_json,
                                                                                               indent=2)))
            assert False
    else:
        annotations_list = context.item.annotations.list()
        for ann in annotations_list:
            success, response = context.item._client_api.gen_request(
                req_type="get",
                path="/datasets/%s/items/%s/annotations/%s"
                     % (context.item.dataset.id, context.item.id, ann.id),
            )
            ann_json = ann.to_json()
            response = response.json()
            assert success

            # TODO - temporary - need to check why platform dict doesnt have hash attribute
            if ann_json.get('hash', None) is None and response.get('hash', None):
                ann_json.pop('hash', None)
                response.pop('hash', None)

            # 'segment', 'polyline'  remove metadata because response has no metadata
            # 'box', 'point', 'ellipse' sdk remove the system metadata if empty
            if ann.type in ['segment', 'polyline', 'box', 'point', 'ellipse']:
                if 'metadata' in ann_json:
                    ann_json.pop('metadata')
                if 'metadata' in response:
                    response.pop('metadata')

            # compare json
            if response != ann_json:
                logging.error('FAILED: response json is:\n{}\n\nto_json is:\n{}'.format(json.dumps(response,
                                                                                                   indent=2),
                                                                                        json.dumps(ann_json,
                                                                                                   indent=2)))
                assert False


@behave.when(u"I create a blank annotation to item")
def step_impl(context):
    context.dataset = context.dataset.update()
    context.item = context.item.update()
    if context.item.fps is None:
        context.item.fps = 25
    logging.warning('item fps is: {}'.format(context.item.fps))
    context.annotation = context.dl.Annotation.new(item=context.item)


@behave.when(u"I add annotation to item using add annotation method")
def step_impl(context):
    context.dataset = context.dataset.update()
    item = context.item.update()
    labels = context.dataset.labels
    height = item.height
    if height is None:
        height = 768
    width = item.width
    if width is None:
        width = 1536

    # box
    top = r.randrange(0, height)
    left = r.randrange(0, width)
    right = left + 100
    bottom = top + 100
    annotation_definition = context.dl.Box(
        top=top,
        left=left,
        right=right,
        bottom=bottom,
        label=r.choice(labels).tag,
        attributes=["attr1", "attr2"],
    )
    context.annotation = context.dl.Annotation.new(
        annotation_definition=annotation_definition, item=context.item
    )


@behave.when(u"I upload annotation created")
def step_impl(context):
    logging.warning('item fps is: {}'.format(context.item.fps))
    context.annotation.upload()


@behave.when(u"I add some frames to annotation")
def step_impl(context):
    if context.item.fps is None:
        context.item.fps = 25
    ann = context.annotation
    for i in range(20):
        top = ann.top + (i * 10)
        left = ann.left + (i * 10)
        right = ann.right + (i * 10)
        bottom = ann.bottom + (i * 10)
        annotation_definition = context.dl.Box(
            top=top,
            left=left,
            right=right,
            bottom=bottom,
            label=ann.label,
            attributes=ann.attributes,
        )
        frame_num = i * 10
        ann.add_frame(annotation_definition=annotation_definition, frame_num=frame_num)


@behave.then(u"Item in host has annotation added")
def step_impl(context):
    if context.item.fps is None:
        context.item.fps = 25
        context.item.update(system_metadata=True)
        time.sleep(4)
        context.item = context.dataset.items.get(item_id=context.item.id)
    if context.item.fps is None:
        context.item.fps = 25
        time.sleep(1)
    try:
        annotations = context.item.annotations.list()
        context.annotation_get = annotations[0]
    except:
        logging.error(context.item.to_json())
    assert context.annotation_get.label == context.annotation.label
    assert context.annotation_get.attributes == context.annotation.attributes
    assert context.annotation_get.coordinates == context.annotation.coordinates


@behave.when(u"I add frames to annotation")
def step_impl(context):
    ann = context.annotation
    top = 100
    left = 100
    right = left + 100
    bottom = top + 100
    label = context.dataset.labels[0]
    for i in range(20):
        top = top + (i * 10)
        left = left + (i * 10)
        right = right + (i * 10)
        bottom = bottom + (i * 10)
        annotation_definition = context.dl.Box(
            top=top, left=left, right=right, bottom=bottom, label=label.tag
        )
        frame_num = i * 10
        ann.add_frame(annotation_definition=annotation_definition, frame_num=frame_num)


@behave.then(u"Item in host has video annotation added")
def step_impl(context):
    context.annotation_get = context.item.annotations.list()[0]
    assert context.annotation_get.label == context.annotation.label
    assert context.annotation_get.attributes == context.annotation.attributes
    assert context.annotation_get.coordinates == context.annotation.coordinates
    # can check frames since the video decoder
    # assert len(context.annotation_get.frames) == len(context.annotation.frames)
