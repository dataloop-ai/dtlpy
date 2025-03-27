import behave
import time
from operator import attrgetter



@behave.when(u'I get Task by "{get_method}"')
def step_impl(context, get_method):
    if get_method == 'name':
        context.task_get = context.project.tasks.get(task_name=context.task.name)
    elif get_method == 'id':
        context.task_get = context.project.tasks.get(task_id=context.task.id)


@behave.when(u'I get Task by wrong "{get_method}"')
def step_impl(context, get_method):
    try:
        if get_method == 'name':
            context.task_get = context.project.tasks.get(task_name='randomName')
        elif get_method == 'id':
            context.task_get = context.project.tasks.get(task_id='111111111111')
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I validate "{status}" status on a "{task_type}"')
def step_impl(context, status, task_type):
    try:
        if task_type == "task":
            if status == "open":
                active_status = context.dl.tasks.get(task_id=context.task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            elif status == "completed":
                active_status = context.dl.tasks.get(task_id=context.task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            elif status == "completed with issues":
                active_status = context.dl.tasks.get(task_id=context.task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            else:
                assert False, "Failed, Wrong status (open / completed / completed with issues)"
        elif task_type == "qa_task":
            if status == "open":
                active_status = context.dl.tasks.get(task_id=context.qa_task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            elif status == "completed":
                active_status = context.dl.tasks.get(task_id=context.qa_task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            elif status == "completed with issues":
                active_status = context.dl.tasks.get(task_id=context.task.id).status
                assert active_status == status, f"Failed, Wrong status got {active_status} and expected {status}"
            else:
                assert False, "Failed, Wrong status (open / completed / completed with issues)"
        else:
            assert False, "Failed, Wrong task_type (task / qa_task)"

    except context.dl.exceptions.PlatformException as e:
        assert False, "Failed to update item_status \n".format(e)


@behave.then(u'Task received equals task created')
def step_impl(context):
    assert context.task.to_json() == context.task_get.to_json()


@behave.then(u'I expect "{task}" created with "{total_items}" items')
def step_impl(context, task, total_items):
    num_try = 15
    interval = 10
    success = False

    for i in range(num_try):
        time.sleep(interval)
        if int(total_items) == attrgetter(task)(context).get_items(get_consensus_items=True).items_count:
            success = True
            break

    assert success, "TEST FAILED: Task total expected : {} , Actual : {}".format(total_items, context.task.get_items(
        get_consensus_items=True).items_count)
