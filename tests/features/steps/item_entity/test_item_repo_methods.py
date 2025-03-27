import time
import behave
import os
import json


@behave.when(u'I download an item entity by the name of "{item_name}" to "{download_path}"')
def step_impl(context, item_name, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    context.item.download(save_locally=True,
                          local_path=download_path,
                          annotation_options=None)


@behave.when(u'I delete the item')
def step_impl(context):
    context.item.delete()


@behave.when(u'I update item entity name to "{name}"')
def step_impl(context, name):
    context.item.filename = name
    context.item_update = context.item.update(system_metadata=True)


@behave.when(u'I list all item entity annotations')
def step_impl(context):
    context.annotations_list = context.item.annotations.list()


@behave.when(u'I get the item entity annotation by id')
def step_impl(context):
    context.annotation_x_get = context.item.get_annotation(context.annotation_x.id)


@behave.when(u'I upload to item entity annotations from file: "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)

    with open(file_path, "r") as f:
        context.annotations = json.load(f)["annotations"]
    context.item.annotations.upload(context.annotations)


@behave.when(u'I move item to "{new_path}"')
def step_impl(context, new_path):
    context.item_name = context.item.name
    context.moved_item = context.item.move(new_path=new_path)
    context.new_path = new_path


@behave.then(u'Item in host moved to a new directory')
def step_impl(context):
    if context.new_path.startswith('/'):
        name = context.new_path + '/' + context.item_name
    elif '.' in context.new_path:
        name = '/' + context.new_path
    else:
        name = '/' + context.new_path + '/' + context.item_name
    assert context.moved_item.filename == name


@behave.then(u'Item is annotated')
def step_impl(context):
    context.item.annotated = True
    context.item = context.item.update()


@behave.given(u'I upload item in path "{item_path}" to dataset')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)

    # wait for platform attributes
    limit = 10 * 30
    stat = time.time()
    while True:
        time.sleep(3)
        context.item = context.dataset.items.get(item_id=context.item.id)
        if "video" in context.item.mimetype:
            if context.item.fps is not None:
                break
        elif context.item.mimetype is not None:
            break
        if time.time() - stat > limit:
            raise TimeoutError("Timeout while waiting for platform attributes")


@behave.given(u'I add "{new_field}" field to be "{boolean}" in item metadata')
def step_impl(context, new_field, boolean):
    context.item.metadata = {f"{new_field}": boolean}
    context.item.update()
