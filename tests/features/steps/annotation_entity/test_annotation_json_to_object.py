import logging
import behave
import json
import random as r
import time


@behave.then(u'Object "{entity}" to_json() equals to Platform json.')
def step_impl(context, entity):
    if entity != 'Annotations':
        entity = entity.lower()
        if entity == 'feature_set':
            url_path = '/features/sets/{}'.format(getattr(context, entity).id)
        elif entity == 'feature':
            url_path = '/features/vectors/{}'.format(getattr(context, entity).id)
        else:
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
        elif entity == 'dataset':
            entity_to_json.pop('export', None)
            response.pop('export', None)
        elif entity == 'execution':
            entity_to_json.pop('status')
            response.pop('status')
            entity_to_json.pop('latestStatus')
            response.pop('latestStatus')
            entity_to_json.pop('statusLog')
            response.pop('statusLog')
            entity_to_json.pop('updatedAt')
            response.pop('updatedAt')
        elif entity == 'project':
            entity_to_json.pop('isBlocked', None)
            response.pop('isBlocked', None)

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

            if ann_json.get('hash', None) is not None and ann_json.get('hash', None).startswith('NO'):
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


@behave.when(u"I add annotation to audio using add annotation method")
def step_impl(context):
    context.dataset = context.dataset.update()
    item = context.item.update()
    labels = context.dataset.labels
    builder = item.annotations.builder()

    builder.add(annotation_definition=context.dl.Subtitle(text="this is a test", label=r.choice(labels).tag),
                start_time=10,
                end_time=12,
                object_id=1)

    item.annotations.upload(builder)


@behave.when(u"I upload annotation created")
def step_impl(context):
    logging.warning('item fps is: {}'.format(context.item.fps))
    context.annotation = context.annotation.upload()


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
    assert context.annotation_get.to_json() == context.annotation.to_json()
    if 'snapshots_' in context.annotation_get.metadata['system']:
        assert len(context.annotation_get.metadata['system']['snapshots_']) == 19


@behave.then(u"audio in host has annotation added")
def step_impl(context):
    context.item = context.dataset.items.get(item_id=context.item.id)
    try:
        annotations = context.item.annotations.list()
        context.annotation_get = annotations[0]
    except:
        logging.error(context.item.to_json())
    assert context.annotation_get.start_time == 10
    assert context.annotation_get.end_time == 12


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


@behave.when(u"I create a false fixed annotation in video")
def step_impl(context):
    system = context.item.metadata.get('system', dict())
    nb_frames = system.get('nb_frames', None)

    num_tries = 60
    interval_time = 5
    found_frames = False

    if not nb_frames:
        for i in range(num_tries):
            time.sleep(interval_time)
            nb_frames = system.get('ffmpeg', dict()).get('nb_read_frames', None)
            if nb_frames:
                nb_frames = int(nb_frames)
                found_frames = True
                break

    assert isinstance(nb_frames, int), f"TEST FAILED: nb_frames is not defined after {round(num_tries * interval_time / 60, 1)} minutes"
    ann = context.annotation
    label = context.dataset.labels[0]
    for frame in range(nb_frames):
        annotation_definition = context.dl.Box(
            top=100, left=100, right=500, bottom=500, label=label.tag
        )
        frame_num = frame
        ann.add_frame(annotation_definition=annotation_definition, frame_num=frame_num, fixed=False)

    return found_frames


@behave.then(u"Video has annotation without snapshots")
def step_impl(context):
    assert context.item.annotations.list()[0].metadata['system']['snapshots_'] == []


@behave.when(u"I get annotation using dl")
def step_impl(context):
    context.dl_annotation = context.dl.annotations.get(annotation_id=context.annotation.id)


@behave.then(u"I validate annotation have frames")
def step_impl(context):
    assert context.dl_annotation.start_time == 0.0
    assert context.dl_annotation.end_time == 7.6
    assert context.dl_annotation.start_frame == 0
    assert context.dl_annotation.end_frame == 190
    assert context.dl_annotation.to_json()['metadata']['system']['snapshots_'] == \
           context.annotation.to_json()['metadata']['system']['snapshots_']


@behave.when(u'I update annotation start time to "{start_time}"')
def step_impl(context, start_time):
    context.start_time = float(start_time)
    context.annotation_get = context.item.annotations.list()[0]
    context.annotation_get.start_time = context.start_time
    context.annotation_get = context.annotation_get.update(True)
    context.start_frame = context.annotation_get.start_frame


@behave.then(u"I validate snapshot has the correct start frame")
def step_impl(context):
    assert context.annotation_get.metadata['system']['snapshots_'][0][
        'frame'], "TEST FAILED: Missing frame in snapshots_ \n{}".format(context.annotation_get.metadata['system'])
    assert context.annotation_get.metadata['system']['snapshots_'][0][
               'frame'] > context.start_frame, "TEST FAILED: Wrong start frame"


@behave.when(u'I update annotation start time "{start_time}" end time "{end_time}"')
def step_impl(context, start_time, end_time):
    context.start_time = float(start_time)
    context.end_time = float(end_time)
    context.annotation_get = context.item.annotations.list()[0]
    context.annotation_get.start_time = context.start_time
    context.annotation_get.end_time = context.end_time
    context.annotation_get = context.annotation_get.update(True)
    context.start_time = context.annotation_get.start_time
    context.end_time = context.annotation_get.end_time


@behave.then(u"I validate audio has the correct start and end time")
def step_impl(context):
    assert context.annotation_get.metadata['system'][
               'startTime'] == context.start_time, "TEST FAILED: failed to update startTime from {} to {}".format(
        context.annotation_get.metadata['system']['startTime'], context.start_time)
    assert context.annotation_get.metadata['system'][
               'endTime'] == context.end_time, "TEST FAILED: failed to update endTime from {} to {}".format(
        context.annotation_get.metadata['system']['endTime'],
        context.end_time)


@behave.when(u"I add class annotation to item using add annotation method")
def step_impl(context):
    labels = context.dataset.labels
    context.label = r.choice(labels).tag
    context.annotation_definition = context.dl.Classification(
        label=context.label,
        attributes=["attr1", "attr2"],
    )
    context.annotation = context.dl.Annotation.new(
        annotation_definition=context.annotation_definition, item=context.item, end_time=1
    )


@behave.when(u'I set frame "{frame}" annotation attributes')
def step_impl(context, frame):
    context.new_attributes = ["attr3", "attr4"]
    context.old_attributes = context.annotation_definition.attributes
    annotation_definition = context.dl.Classification(
        label=context.label,
        attributes=context.new_attributes,
    )
    context.annotation.add_frame(annotation_definition=annotation_definition, frame_num=int(frame))


@behave.then(u'I validity "{frames}" has the updated attributes')
def step_impl(context, frames):
    context.annotation_get = context.item.annotations.list()[0]
    assert context.annotation_get.attributes == context.old_attributes, "TEST FAILED: attributes not updated"
    assert context.annotation_get.frames[
               int(frames)].attributes == context.new_attributes, "TEST FAILED: attributes not updated"
