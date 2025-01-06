from behave import given, when, then
import os
import time


@given(u'There is an item "{with_or_without}" "{key}" in its metadata system')
def step_impl(context, key: str, with_or_without: str):
    local_path = "sample_video.mp4"
    local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], local_path)
    context.item = context.dataset.items.upload(
        local_path=local_path,
        remote_name="sample_video-{}-{}-{}.mp4".format(with_or_without, key, time.time())
    )

    start = time.time()
    interval = 5
    timeout = 100

    while key not in context.item.metadata['system']:
        time.sleep(interval)
        context.item = context.dataset.items.get(item_id=context.item.id)
        if time.time() - start > timeout:
            raise Exception('Item was not created with {} in metadata'.format(key))

    if with_or_without == 'without':
        context.item.metadata['system'].pop(key)
        context.item = context.item.update(system_metadata=True)
        assert key not in context.item.metadata['system']


@when(u'I clone the item')
def step_impl(context):
    context.item_clone = context.item.clone(
        dst_dataset_id=context.dataset.id,
        remote_filepath='{}-cloned.jpg'.format(context.item.filename)
    )


@then(u'The cloned item should trigger video preprocess function')
def step_impl(context):
    start = time.time()
    interval = 5
    timeout = 20

    def is_triggered():
        re = context.item_clone.resource_executions.list()
        e = [e for e in re.items if e.service_name == 'video-metadata-extractor' and e.function_name == 'on_create']
        return len(e) > 0

    while not is_triggered():
        time.sleep(interval)
        if time.time() - start > timeout:
            raise Exception('Item was not created with fps in metadata')


@then(u'The cloned item should have "{key}" in its metadata')
def step_impl(context, key: str):
    start = time.time()
    interval = 5
    timeout = 60
    while key not in context.item_clone.metadata['system']:
        if time.time() - start > timeout:
            raise Exception('Item was not created with fps in metadata')
        time.sleep(interval)
        context.item_clone = context.dataset.items.get(item_id=context.item_clone.id)
