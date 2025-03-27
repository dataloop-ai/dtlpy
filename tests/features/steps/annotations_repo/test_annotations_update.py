import behave
import time


@behave.given(u"I remove annotations attributes")
def step_impl(context):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.attributes = {}


@behave.when(u"I update annotations")
def step_impl(context):
    context.item.annotations.update(
        annotations=context.annotations_get.annotations,
        system_metadata=True
    )
    time.sleep(7)


@behave.then(u"Item annotations has no attributes")
def step_impl(context):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert not annotation.attributes


@behave.given(u"I change annotations attributes to non-existing attributes")
def step_impl(context):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.attributes = ["some_attribute_name"]


@behave.given(u'I change all annotations types to "{type_name}"')
def step_impl(context, type_name):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.type = type_name


@behave.then(u'All item annotations have type "{type_name}"')
def step_impl(context, type_name):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert annotation.type == type_name


@behave.given(u'I change all annotations labels to "{label_name}"')
def step_impl(context, label_name):
    context.annotations_get = context.item.annotations.list()
    for annotation in context.annotations_get:
        annotation.label = label_name


@behave.then(u'All item annotations have label "{label_name}"')
def step_impl(context, label_name):
    annotations_get = context.item.annotations.list()
    for annotation in annotations_get:
        assert annotation.label == label_name


@behave.when(u"I try to update annotations")
def step_impl(context):
    annotation_ids = list()
    for annotation in context.annotations_get:
        annotation_ids.append(annotation.id)
    try:
        context.item.annotations.update(
            annotations=context.annotations_get,
            annotations_ids=annotation_ids,
            system_metadata=True,
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u"I change annotation values")
def step_impl(context):
    context.annotation_x.attributes = list()
    context.annotation_x.label = "person"


@behave.given(u'I change annotation "{number}" value to "{name}"')
def atp_step_impl(context, number, name):
    context.annotations_list[int(number)].label = name
    context.annotations_list[int(number)].update()


@behave.when(u"I update annotation")
def step_impl(context):
    context.item.annotations.update(
        annotations=context.annotation_x,
        system_metadata=True,
    )


@behave.then(u"Annotation should be updated")
def step_impl(context):
    annotation_get = context.item.annotations.get(context.annotation_x.id)
    assert not annotation_get.attributes
    assert annotation_get.label == "person"


@behave.given(u'I add "{raise_value}" to annotation coordinates')
def step_impl(context, raise_value):
    raise_value = int(raise_value)
    context.annotation_x.top += raise_value
    context.annotation_x.right += raise_value
    context.annotation_x.left += raise_value
    context.annotation_x.bottom += raise_value


@behave.given(u'I set start frame to "{start_frame}" and end frame to "{end_frame}"')
def step_impl(context, start_frame, end_frame):
    start_frame = int(start_frame)
    end_frame = int(end_frame)
    context.annotation_x.start_frame = start_frame
    context.annotation_x.end_frame = end_frame


@behave.then(u'annotation x coordinates should be changed accordingly')
def step_impl(context):
    annotation_get = context.item.annotations.get(context.annotation_x.id)
    assert annotation_get.coordinates == context.annotation_x.coordinates


@behave.then(u'annotation x metadata should be changed accordingly')
def step_impl(context):
    annotation_get = context.item.annotations.get(context.annotation_x.id)
    assert annotation_get.start_time == context.annotation_x.start_time
    assert annotation_get.end_time == context.annotation_x.end_time


@behave.when(u'I get the only annotation')
def step_impl(context):
    context.annotation = context.item.annotations.list()[0]


@behave.then(u'Annotation snapshots equal to platform snapshots')
def step_impl(context):
    ann = context.annotation
    assert len(ann.frames.actual_keys()) == 5
    time.sleep(10)
    vals = list(ann.frames.values())
    assert len(vals) == 46
    platform_snapshots = context.annotation._platform_dict['metadata']['system']['snapshots_']
    ann_snapshot = ann.to_json()['metadata']['system']['snapshots_']
    assert len(platform_snapshots) == len(ann_snapshot)
    for platform_snap in platform_snapshots:
        ann_snap = [snap for snap in ann_snapshot if snap['frame'] == platform_snap['frame']][0]
        assert ann_snap
        assert ann_snap['frame'] == platform_snap['frame']
        assert ann_snap['data'] == platform_snap['data']


@behave.when(u'I update items annotations in task with context.annotation_definition')
def step_impl(context):
    filters = context.dl.Filters()
    filters.add(field='annotated', values=True)
    pages = context.task.get_items(filters=filters)
    for item in pages.all():
        for annotation in item.annotations.list():
            annotation.annotation_definition = context.annotation_definition
            annotation.update()


@behave.then(u'I verify that I have annotations')
def step_impl(context):
    filters = context.filters
    annotations = context.dataset.annotations.list(filters=filters)
    assert annotations.items_count != 0


@behave.when(u'I set object id for annotation "{number}" to be "{new_number}"')
def atp_step_impl(context, number, new_number):
    context.annotations_list[int(number)].object_id = new_number
    context.annotations_list[int(number)].update(system_metadata=True)


@behave.then(u'I validate that annotation "{number}" has object id "{new_number}"')
def atp_step_impl(context, number, new_number):
    assert context.annotations_list[int(number)].object_id == new_number


@behave.when(u'I set an issue to the annotation')
def atp_step_impl(context):
    context.annotation.metadata['system']['issueAssignmentId'] = context.assignment.id
    context.annotation.metadata['system']['issueTaskId'] = context.task.id
    context.annotation.status = 'issue'
    context.annotation.update(True)
    time.sleep(1)


@behave.when(u'I update annotation status to "{issue_status}"')
def atp_step_impl(context, issue_status):
    # issue status = (issue, review, approved, clear)
    context.annotation.status = issue_status
    context.annotation.update(True)
    time.sleep(1)


@behave.then(u'annotation status is "{issue_status}"')
def atp_step_impl(context, issue_status):
    # issue status = (issue, review, approved, clear)
    status = context.annotation.status
    assert issue_status == status, f"Failed, Wrong status got {status} and expected {issue_status}"



