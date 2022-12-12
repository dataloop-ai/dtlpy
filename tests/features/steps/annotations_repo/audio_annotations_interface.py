import behave
from time import sleep


@behave.given(u'I upload "{annotation_type}" annotation to the audio item')
def step_impl(context, annotation_type):
    # Used to get item data from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    annotations_definitions_list = {
        "subtitle": context.dl.Subtitle(
            text="text1",
            label="label1",
            attributes=[{"attributes1": "subtitle1"}]
        )
    }

    builder = context.item.annotations.builder()
    builder.add(annotations_definitions_list[annotation_type])
    context.annotation = context.item.annotations.upload(annotations=builder)[0]


@behave.given(u'I upload "{annotation_type}" annotation with description "{annotation_description}" to the audio item')
def step_impl(context, annotation_type, annotation_description):
    # Used to get item data from the backend
    sleep(4)
    context.item = context.dl.items.get(item_id=context.item.id)

    annotations_definitions_list = {
        "subtitle": context.dl.Subtitle(
            text="text1",
            label="label1",
            attributes=[{"attributes1": "subtitle1"}],
            description=annotation_description
        )
    }

    builder = context.item.annotations.builder()
    builder.add(annotations_definitions_list[annotation_type])
    context.annotation = context.item.annotations.upload(annotations=builder)[0]
