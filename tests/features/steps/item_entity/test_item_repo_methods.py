import behave
import os
import json


@behave.when(u'I download an item entity by the name of "{item_name}" to "{download_path}"')
def step_impl(context, item_name, download_path):
    download_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], download_path)
    context.item.download(save_locally=True,
                          local_path=download_path,
                          download_options=None,
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


@behave.when(u'I uploade to item entity annotations from file: "{file_path}"')
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
        name  = context.new_path + '/' + context.item_name
    elif '.' in context.new_path:
        name = '/' + context.new_path
    else:
        name  = '/' + context.new_path + '/' + context.item_name
    assert context.moved_item.filename == name
