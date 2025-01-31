import behave
from time import sleep


@behave.when(u'I upload "{number_of_annotations}" annotation with the same object id')
def step_impl(context, number_of_annotations):
    # Used to get item data from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    builder = context.item.annotations.builder()
    for i in range(int(number_of_annotations)):
        builder.add(annotation_definition=context.dl.Box(left=50 + i * 15,
                                                         top=50 + i * 15,
                                                         right=250 + i * 15,
                                                         bottom=250 + i * 15,
                                                         label='label1'),
                    object_visible=True,
                    object_id=1,
                    frame_num=i + 10 * i)
    context.item.annotations.upload(builder)


@behave.then(u'I check that I got "{number_of_keyframes}" keyframes')
def step_impl(context, number_of_keyframes):
    frames = context.item.annotations.list()[0].frames

    for i in range(int(number_of_keyframes)):
        current_frame = frames[i + 10 * i]

        left = current_frame.coordinates[0]['x']
        top = current_frame.coordinates[0]['y']
        right = current_frame.coordinates[1]['x']
        bottom = current_frame.coordinates[1]['y']

        assert left == 50 + i * 15
        assert top == 50 + i * 15
        assert right == 250 + i * 15
        assert bottom == 250 + i * 15


@behave.when(u'I update the "{number_of_keyframes}" frame attribute of the annotation')
def step_impl(context, number_of_keyframes):
    context.annotation = context.item.annotations.list()[0]
    context.annotation.frames[int(number_of_keyframes)].attributes = {"1": "a"}
    context.annotation = context.annotation.update(True)


@behave.then(u'I the only frame "{number_of_keyframes}" attribute is updated')
def step_impl(context, number_of_keyframes):
    assert context.annotation.frames[int(number_of_keyframes)].attributes == {"1": "a"}, "The attribute is not updated"
    assert not context.annotation.frames[0].attributes, "The attribute is not updated"
