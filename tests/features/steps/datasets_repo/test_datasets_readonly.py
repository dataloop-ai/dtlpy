import behave
import os
import random


@behave.when(u'I set dataset readonly mode to "{state}"')
def step_impl(context, state):
    state = state == 'True'
    context.project.datasets.set_readonly(dataset=context.dataset, state=state)


def item_uploaded_successfully(context):
    try:
        item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], '0000000162.png')
        item = context.dataset.items.upload(
            local_path=item_local_path,
            remote_name='name-{}'.format(random.randrange(100, 10000))
        )
        item_uploaded = isinstance(item, context.dl.Item)
    except Exception:
        item_uploaded = False

    return item_uploaded


def dataset_updated_successfully(context):
    try:
        context.dataset.name = 'name-{}'.format(random.randrange(100, 10000))
        context.dataset.update()
        dataset_updated = True
    except Exception:
        dataset_updated = False

    return dataset_updated


@behave.then(u'Dataset is in readonly mode')
def step_impl(context):
    assert context.dataset.readonly
    assert not item_uploaded_successfully(context=context)
    assert not dataset_updated_successfully(context=context)


@behave.then(u'Dataset is not in readonly mode')
def step_impl(context):
    assert not context.dataset.readonly
    assert item_uploaded_successfully(context=context)
    assert dataset_updated_successfully(context=context)


@behave.then('I try and fail to delete the project with the readonly dataset')
def step_impl(context):
    try:
        context.project.delete(True, True)
    except Exception as e:
        assert 'Failed to perform operation on readonly dataset' in e.args[1]
