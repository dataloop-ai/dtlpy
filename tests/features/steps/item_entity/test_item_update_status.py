import behave
import random


@behave.when(u'I update items status to default task actions')
def step_impl(context):
    pages = context.task.get_items()
    try:
        for page in pages:
            for item in page:
                if item.annotated:
                    item.update_status(status=context.dl.ItemStatus.COMPLETED)
                else:
                    # item.update_status(status=context.dl.ItemStatus.DISCARDED)
                    item.update_status(status='discard')

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I update items status to default task actions with task id')
def step_impl(context):
    pages = context.task.get_items()
    try:
        for page in pages:
            for item in page:
                if item.annotated:
                    item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id)
                else:
                    # item.update_status(status=context.dl.ItemStatus.DISCARDED,task_id=context.task.id)
                    item.update_status(status='discard', task_id=context.task.id)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I validate default items status in task')
def step_impl(context):
    pages = context.dataset.items.list()

    for page in pages:
        for item in page:
            if item.annotated:
                assert item.metadata['system']['taskStatusLog'][0]["status"]["status"] == "completed", "Failed , Item missing status Completed"
            else:
                assert item.metadata['system']['taskStatusLog'][0]["status"]["status"] == "discard", "Failed , Item missing status Discarded"


@behave.when(u'I update items status to custom task actions "{action_1}" "{action_2}" "{action_3}"')
def step_impl(context,action_1,action_2,action_3):
    pages = context.task.get_items()
    try:
        for page in pages:
            for item in page:
                rand = random.randrange(0,3)
                if rand == 0:
                    item.update_status(status=action_1)
                elif rand == 1:
                    item.update_status(status=action_2)
                else:
                    item.update_status(status=action_3)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I validate items status in task')
def step_impl(context):
    pages = context.dataset.items.list()

    for page in pages:
        for item in page:
            assert len(item.metadata['system']['taskStatusLog']) == 1, "Failed to set status to item"


@behave.then(u'I update item status to "{status}" with task id')
def step_impl(context, status):
    try:
        context.item.update_status(status=status, task_id=context.task.id)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I remove specific "{status}" from item with task id')
def step_impl(context, status):
    try:
        context.item.update_status(status=status, task_id=context.task.id, clear=True)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)