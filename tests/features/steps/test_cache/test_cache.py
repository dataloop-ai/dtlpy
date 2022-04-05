import os

import behave
import dtlpy as dl


@behave.then(u'i make project get and i get hit')
def step_impl(context):
    context.project = dl.projects.get(project_id=context.project.id)
    assert context.project.metadata['cache'] == 'hit'


@behave.then(u'i make dataset get and i get hit')
def step_impl(context):
    context.dataset = dl.datasets.get(dataset_id=context.dataset.id)
    assert context.dataset.metadata['cache'] == 'hit'


@behave.then(u'i make item get and i get hit')
def step_impl(context):
    context.item = dl.items.get(item_id=context.item.id)
    assert context.dataset._client_api.last_request.method != 'GET'


@behave.then(u'i make all item get and i get hit')
def step_impl(context):
    for item in context.item:
        item_get = dl.items.get(item_id=item.id)
        assert context.dataset._client_api.last_request.method != 'GET'


@behave.then(u'the lru is work')
def step_impl(context):
    path = os.path.join(dl.sdk_cache.cache_path_bin, 'items')
    files = os.listdir(path)
    assert len(files) < 100


@behave.when(u'set binary cache size to 10')
def step_impl(context):
    dl.sdk_cache.bin_size = 10


@behave.Given(u'cache is on')
def step_impl(context):
    dl.sdk_cache.use_cache = True


@behave.then(u'cache is off')
def step_impl(context):
    dl.sdk_cache.use_cache = False


@behave.then(u'i make annotation get and i get hit')
def step_impl(context):
    annotation = dl.annotations.get(annotation_id=context.annotation.id)
    assert annotation.metadata['cache'] == 'hit'


@behave.then(u'I upload a annotation for the item')
def step_impl(context):
    context.builder = context.item.annotations.builder()
    context.builder.add(annotation_definition=dl.Classification(label='test'))
    context.item.annotations.upload(context.builder)
    for ann in context.item.annotations.list():
        context.annotation = ann


@behave.then(u'i make dataset get and i get miss')
def step_impl(context):
    try:
        context.dataset = dl.datasets.get(dataset_id=context.dataset.id)
        assert False
    except:
        assert True


@behave.then(u'i make all item get and i get miss')
def step_impl(context):
    try:
        for item in context.item:
            item_get = dl.items.get(item_id=item.id)
        assert False
    except:
        assert True


@behave.then(u'i make item get and i get miss')
def step_impl(context):
    try:
        context.item = dl.items.get(item_id=context.item.id)
        assert False
    except:
        assert True


@behave.then(u'i make annotation get and i get miss')
def step_impl(context):
    try:
        context.annotation = dl.annotations.get(annotation_id=context.annotation.id)
        assert False
    except:
        assert True


@behave.then(u'I download the item')
def step_impl(context):
    context.download_path = context.item.download()


@behave.then(u'I git cache bin hit')
def step_impl(context):
    assert 'stream' not in str(context.dataset._client_api.last_request)
    assert os.path.isfile(context.download_path)


@behave.then(u'Item was updated')
def step_impl(context):
    assert context.item.metadata["system"]["modified"] == "True"
