import shutil

import behave
import os


@behave.when(u'I download dataset entity annotations to assets')
def step_impl(context):
    local_path = os.environ['DATALOOP_TEST_ASSETS']
    if os.path.isdir(os.path.join(local_path, 'json')):
        shutil.rmtree(os.path.join(local_path, 'json'))
    context.dataset.download_annotations(local_path=local_path, overwrite=True)


@behave.when(u'I download dataset entity to "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    context.dataset.download(filters=None,
                             local_path=local_path,
                             annotation_options=['mask', 'instance', 'json'],
                             thickness=3)


@behave.when(u'I delete a dataset entity')
def step_impl(context):
    context.dataset.delete(sure=True,
                           really=True)


@behave.when(u'I create a new recipe to dataset entity')
def step_impl(context):
    context.recipe = context.dataset.recipes.create()


@behave.when(u'I upload to dataset entity a file in path "{item_local_path}"')
def step_impl(context, item_local_path):
    item_local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_local_path)
    context.item = context.dataset.upload_item(
        filepath=item_local_path,
        remote_path=None,
        uploaded_filename=None,
        callback=None
    )
