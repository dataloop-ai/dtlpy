import behave
import threading
import time
import os
import shutil


@behave.when('I unlock a dataset')
def step_impl(context):
    dataset = context.dataset
    try:
        dataset.unlock()
    except Exception as e:
        context.error = e


@behave.Then(u'I able to rename item to "{name}" while Exporting locked dataset')
def step_impl(context, name):
    def export_with_locking():
        try:
            context.dataset.export(dataset_lock=True)
        except Exception as e:
            context.export_error = e

    context.buffer = threading.Thread(target=export_with_locking)
    context.buffer.start()
    time.sleep(2)
    try:
        context.dataset.unlock()
        context.item.filename = name
        context.item_update = context.dataset.items.update(item=context.item)
    except Exception as e:
        context.unlock_error = e

    context.buffer.join()

    if getattr(context, "export_error", None):
        raise RuntimeError(f"Export failed: {context.export_error}")
    if getattr(context, "unlock_error", None):
        raise RuntimeError(f"Unlock failed: {context.unlock_error}")

    assert type(context.item_update) == context.dl.Item
    assert context.item_update.filename == name


@behave.when('I export dataset to created folder with lock dataset and export time out "{export_timeout}"')
def step_impl(context, export_timeout):
    assert context.dataset.readonly == False, "Dataset already in read-only mode"

    def export_with_locking():
        try:
            context.dataset.export(dataset_lock=True, local_path=context.folder_path,
                                   lock_timeout_sec=int(export_timeout))
        except Exception as e:
            context.export_error = e

    context.buffer = threading.Thread(target=export_with_locking)
    context.buffer.start()


@behave.when('I create "{folder_path}" folder')
def step_impl(context, folder_path):
    context.folder_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], folder_path)
    if os.path.exists(context.folder_path):
        shutil.rmtree(context.folder_path)
    os.makedirs(context.folder_path, exist_ok=True)


@behave.when('I check dataset is locked')
def step_impl(context):
    context.dataset = context.project.datasets.get(None, context.dataset.id)
    assert context.dataset.readonly == True, "Expected True after Starting Export with lock but it's False"


@behave.then('I check dataset is not locked')
def step_impl(context):
    context.dataset = context.project.datasets.get(None, context.dataset.id)
    assert context.dataset.readonly == False, "Expected False after timeout but got True"


@behave.Then('I check if created folder is empty')
def step_impl(context):
    assert os.path.exists(context.folder_path), f"Folder '{context.folder_path}' does not exist"
    assert not os.listdir(context.folder_path), f"Folder '{context.folder_path}' is not empty"


@behave.Then('I check if created folder is not empty')
def step_impl(context):
    assert os.path.exists(context.folder_path), f"Folder '{context.folder_path}' does not exist"
    assert os.listdir(context.folder_path), f"Folder '{context.folder_path}' is empty"
    if hasattr(context, "buffer"):
        context.buffer.join()


@behave.then('delete the folder and its content')
def step_impl(context):
    if os.path.exists(context.folder_path):
        shutil.rmtree(context.folder_path)

    assert not os.path.exists(context.folder_path), f"Failed to delete '{context.folder_path}'"
