import behave
import os


@behave.when(u'I download dataset entity annotations to assets')
def step_impl(context):
    local_path = os.environ['DATALOOP_TEST_ASSETS']
    context.dataset.download_annotations(local_path=local_path)


@behave.when(u'I download dataset entity to "{local_path}"')
def step_impl(context, local_path):
    local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
    context.dataset.download(query=None,
                             local_path=local_path,
                             filetypes=None,
                             num_workers=None,
                             download_options=None,
                             save_locally=True,
                             download_item=True,
                             annotation_options=['mask', 'img_mask', 'instance', 'json'],
                             opacity=1,
                             with_text=False,
                             thickness=3)


@behave.when(u'I delete a dataset entity')
def step_impl(context):
    context.dataset.delete(sure=True,
                           really=True)


# @behave.when(u'I list items in dataset entity')
# def step_impl(context):
#     context.list = context.dataset.list_items(query=None, page_offset=0, page_size=100)


# @behave.when(u'I get the dataset entity item by id')
# def step_impl(context):
#     context.item_get = context.dataset.get_item(item_id=context.item.id)


# @behave.when(u'I download dataset entity items to local path "{local_path}"')
# def step_impl(context, local_path):
#     local_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], local_path)
#     items = context.dataset.items.get_all_items()
#     context.buffer = context.dataset.download_batch(
#         items=items,
#         save_locally=True,
#         local_path=local_path,
#         chunk_size=8192,
#         download_options=None,
#         download_item=True,
#         annotation_options=None,
#         verbose=True,
#         show_progress=False,
#     )


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
        callback=None,
        upload_options=None,
    )
