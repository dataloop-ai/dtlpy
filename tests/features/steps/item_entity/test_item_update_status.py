import time
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
                    item.update_status(status=context.dl.ItemStatus.DISCARDED)

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
                    item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.task.id)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I update items status to default qa_task actions with qa_task id')
def atp_step_impl(context):
    pages = context.qa_task.get_items()
    try:
        for page in pages:
            for item in page:
                if item.annotated:
                    item.update_status(status=context.dl.ItemStatus.APPROVED, task_id=context.qa_task.id)
                else:
                    item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.qa_task.id)

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I complete all items in task except for discarded items')
def step_impl(context):
    pages = context.task.get_items()
    try:
        for page in pages:
            for item in page:
                if item.status(task_id=context.task.id) != 'discard':
                    item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id)
                else:
                    continue

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I approve all items in task except for discarded items')
def step_impl(context):
    pages = context.qa_task.get_items()
    try:
        for page in pages:
            for item in page:
                if item.status(task_id=context.qa_task.id) != 'discard':
                    item.update_status(status=context.dl.ItemStatus.APPROVED, task_id=context.qa_task.id)
                else:
                    continue

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I validate "{completed_items}" completed and "{discarded_items}" discarded items')
def step_impl(context, discarded_items, completed_items):
    pages = context.task.get_items()
    discarded = 0
    completed = 0
    for page in pages:
        for item in page:
            if item.status(task_id=context.task.id) == 'discard':
                discarded += 1
            elif item.status(task_id=context.task.id) == 'completed':
                completed += 1
    assert int(discarded_items) == discarded, f"Failed, expected {discarded_items} discarded and got {discarded}"
    assert int(completed_items) == completed, f"Failed, expected {completed_items} completed and got {completed}"


@behave.then(u'I validate "{approved_items}" approved and "{discarded_items}" discarded items')
def step_impl(context, discarded_items, approved_items):
    pages = context.qa_task.get_items()
    discarded = 0
    approved = 0
    for page in pages:
        for item in page:
            if item.status(task_id=context.qa_task.id) == 'discard':
                discarded += 1
            elif item.status(task_id=context.qa_task.id) == 'approved':
                approved += 1
    assert int(discarded_items) == discarded, f"Failed, expected {discarded_items} discarded and got {discarded}"
    assert int(approved_items) == approved, f"Failed, expected {approved_items} completed and got {approved}"


@behave.when(u'I "{action}" the "{status}" status of the item on the task')
def step_impl(context, status, action):
    try:
        if action == "add":
            if status == "complete":
                context.item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id)
            elif status == "discard":
                context.item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.task.id)
            else:
                assert False, "Failed, Wrong status (complete / discard)"
        elif action == "clear":
            if status == "complete":
                context.item.update_status(status=context.dl.ItemStatus.COMPLETED, task_id=context.task.id, clear=True)
            elif status == "discard":
                context.item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.task.id, clear=True)
            else:
                assert False, "Failed, Wrong status (complete / discard)"
        else:
            assert False, "Failed, Wrong action (add / clear)"

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I "{action}" the "{status}" status of the item on the QA task')
def step_impl(context, status, action):
    try:
        if action == "add":
            if status == "approve":
                context.item.update_status(status=context.dl.ItemStatus.APPROVED, task_id=context.qa_task.id)
            elif status == "discard":
                context.item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.qa_task.id)
            else:
                assert False, "Failed, Wrong status (approve / discard)"
        elif action == "clear":
            if status == "approve":
                context.item.update_status(status=context.dl.ItemStatus.APPROVED, task_id=context.qa_task.id, clear=True)
            elif status == "discard":
                context.item.update_status(status=context.dl.ItemStatus.DISCARDED, task_id=context.qa_task.id, clear=True)
            else:
                assert False, "Failed, Wrong status (approve / discard)"
        else:
            assert False, "Failed, Wrong action (add / clear)"

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I validate default items status in task')
def step_impl(context):
    pages = context.dataset.items.list()

    for page in pages:
        for item in page:
            if item.annotated:
                assert item.metadata['system']['taskStatusLog'][0]["status"]["status"] == "completed", "Failed, Item missing status completed"
                assert item.status(task_id=context.task.id) == "completed", "Failed, Item missing status completed"
            else:
                assert item.metadata['system']['taskStatusLog'][0]["status"]["status"] == "discard", "Failed, Item missing status discard"
                assert item.status(task_id=context.task.id) == "discard", "Failed, Item missing status discard"


@behave.when(u'I update items status to custom task actions "{action_1}" "{action_2}" "{action_3}"')
def step_impl(context, action_1, action_2, action_3):
    pages = context.task.get_items()
    try:
        for page in pages:
            for item in page:
                rand = random.randrange(0, 3)
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
@behave.when(u'I update item status to "{status}" with task id')
def step_impl(context, status):
    try:
        context.item.update_status(status=status, task_id=context.task.id)
        context.item_status = status
    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'I remove specific "{status}" from item with task id')
def step_impl(context, status):
    try:
        context.item.update_status(status=status, task_id=context.task.id, clear=True)
        context.item_status = status
    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.when(u'I wait for item status to be "{status_value}" with action "{action_type}"')
@behave.then(u'I wait for item status to be "{status_value}" with action "{action_type}"')
def step_impl(context, status_value, action_type):
    num_try = 60
    interval = 10
    success = False
    if status_value == "None":
        status_value = None
    for i in range(num_try):
        context.item = context.dataset.items.get(item_id=context.item.id)
        item_latest_status = context.item.metadata['system']['taskStatusLog'][-1]['status']['status']
        item_latest_action = context.item.metadata['system']['taskStatusLog'][-1]['action']
        if item_latest_status == status_value and item_latest_action == action_type:
            success = True
            break
        time.sleep(interval)

    assert success, f"TEST FAILED: Expected {status_value} | {action_type}, actual status is {item_latest_status} | {item_latest_action}"


