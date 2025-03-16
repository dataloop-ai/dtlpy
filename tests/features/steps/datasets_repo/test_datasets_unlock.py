import behave
import threading
import time

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
