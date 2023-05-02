import behave
import os
import json
from time import sleep


@behave.given(u'I upload annotation in the path "{annotation_path}" to the item')
def step_impl(context, annotation_path):
    context.annotation_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotation_path)
    context.annotation = context.item.annotations.upload(annotations=context.annotation_path)[0]


@behave.given(u'I upload note annotation to the item with the params')
def step_impl(context):
    # Used to get item height and width from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    context.left = 50
    context.top = 50
    context.right = 100
    context.bottom = 100
    context.label = "label1"
    context.attributes = None
    context.assignee = context.dl.info()['user_email']
    context.creator = context.dl.info()['user_email']
    context.description = None
    context.messages = None

    context.object_id = None
    context.frame_num = None
    context.end_frame_num = None

    for parameter in context.table.rows:
        # Annotation params
        if parameter.cells[0] == "left":
            context.left = int(parameter.cells[1])

        if parameter.cells[0] == "top":
            context.top = int(parameter.cells[1])

        if parameter.cells[0] == "right":
            context.right = int(parameter.cells[1])

        if parameter.cells[0] == "bottom":
            context.bottom = int(parameter.cells[1])

        if parameter.cells[0] == "label":
            context.label = parameter.cells[1]

        if parameter.cells[0] == "attributes":
            context.attributes = eval(parameter.cells[1])

        if parameter.cells[0] == "assignee":
            context.assignee = parameter.cells[1]

        if parameter.cells[0] == "creator":
            context.creator = parameter.cells[1]

        if parameter.cells[0] == "description":
            context.description = parameter.cells[1]

        if parameter.cells[0] == "messages":
            context.messages = eval(parameter.cells[1])

        # Builder params
        if parameter.cells[0] == "object_id":
            context.object_id = int(parameter.cells[1])

        if parameter.cells[0] == "frame_num":
            context.frame_num = int(parameter.cells[1])

        if parameter.cells[0] == "end_frame_num":
            context.end_frame_num = int(parameter.cells[1])

    note_annotation = context.dl.Note(
        left=context.left,
        top=context.top,
        right=context.right,
        bottom=context.bottom,
        label=context.label,
        attributes=context.attributes,
        assignee=context.assignee,
        creator=context.creator,
        description=context.description,
        messages=context.messages
    )

    builder = context.item.annotations.builder()
    builder.add(note_annotation, object_id=context.object_id, frame_num=context.frame_num, end_frame_num=context.end_frame_num, fixed=False)
    context.annotation = context.item.annotations.upload(annotations=builder)[0]


@behave.when(u'I upload x annotations to item')
def step_impl(context, x):
    """
    Search keywords: Upload annotations | Add annotations
    """
    context.dataset.add_label(label_name="Box")
    builder = context.item.annotations.builder()
    for i in range(x):
        builder.add(annotation_definition=context.dl.Box(top=10 + i,
                                                         left=10 + i,
                                                         bottom=100 + i,
                                                         right=100 + i,
                                                         label='Box'))
    context.item.annotations.upload(builder)
