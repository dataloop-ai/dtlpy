import io
import time

import behave
import json
import datetime
from PIL import Image
import os


def update_trigger(context):
    filters = None
    resource = None
    actions = None
    active = None
    execution_mode = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "filters":
            if param[1] != "None":
                filters = json.loads(param[1])
        elif param[0] == "resource":
            if param[1] != "None":
                resource = param[1]
        elif param[0] == "action":
            if param[1] != "None":
                actions = [param[1]]
        elif param[0] == "active":
            active = param[1] == "True"
        elif param[0] == "executionMode":
            if param[1] != "None":
                execution_mode = param[1]

    if filters is not None:
        context.trigger.filters = filters
    if resource is not None:
        context.trigger.resource = resource
    if actions is not None:
        context.trigger.actions = actions
    if active is not None:
        context.trigger.active = active
    if execution_mode is not None:
        context.trigger.execution_mode = execution_mode

    context.trigger_update = context.trigger.update()


@behave.when(u"I try to update trigger")
def step_impl(context):
    try:
        update_trigger(context=context)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u"I update trigger")
def step_impl(context):
    update_trigger(context=context)


@behave.then(u"Trigger attributes are modified")
def step_impl(context):
    filters = None
    resource = None
    actions = None
    active = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "filters":
            if param[1] != "None":
                filters = json.loads(param[1])
        elif param[0] == "resource":
            if param[1] != "None":
                resource = param[1]
        elif param[0] == "action":
            if param[1] != "None":
                actions = [param[1]]
        elif param[0] == "active":
            active = param[1] == "True"

    assert context.trigger_update.filters == filters if filters is not None else True
    assert context.trigger_update.resource == resource if resource is not None else True
    assert context.trigger_update.actions == actions if actions is not None else True
    assert context.trigger_update.active == active if active is not None else True


@behave.then(u"I receive an updated Trigger object")
def step_impl(context):
    assert isinstance(context.trigger_update, context.dl.entities.Trigger)


def upload_item(context, directory):
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], '0000000162.jpg')
    image = Image.open(item_local_path)
    buffer = io.BytesIO()
    image.save(buffer, format='jpeg')
    buffer.name = 'item-{}'.format(datetime.datetime.now().isoformat().replace('.', '-').replace(':', '-'))
    return context.dataset.items.upload(
        local_path=buffer,
        remote_path=directory
    )


def executed_on_item(e, i):
    return e.input['item'] == i.id if isinstance(e.input['item'], str) else e.input['item']['item_id'] == i.id


@behave.then(u'Trigger works only on items in "{directory}"')
def step_impl(context, directory: str):

    item_should_not_work = upload_item(context=context, directory='/some_other_dir')
    item_should_work = upload_item(context=context, directory=directory)

    time.sleep(15)

    executions = context.service.executions.list()
    success = False
    for execution in executions.items:
        if executed_on_item(execution, item_should_not_work):
            assert False, 'Trigger created execution for item that does not pass filter'
        elif executed_on_item(execution, item_should_work):
            success = True

    assert success, "Service was not executed on item that passes filter" if not success else ''


@behave.then(u'Trigger is inactive')
def step_impl(context):
    item = upload_item(context=context, directory='/some_other_dir')
    time.sleep(30)
    executions = context.service.executions.list()
    for execution in executions.all():
        if executed_on_item(execution, item):
            assert False, 'Inactive trigger created execution for item that does not pass filter'


@behave.then(u"Trigger works only on items updated")
def step_impl(context):
    # important - this should be a json item that does not trigger global functions
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], 'classes_new.json')
    item = context.dataset.items.upload(local_path=item_local_path)

    time.sleep(20)
    executions = context.service.executions.list()
    for execution in executions.all():
        if executed_on_item(execution, item):
            assert False, 'Service was executed on item created'

    item.metadata['user'] = {'key': 'val'}
    item.update()

    time.sleep(20)
    executions = context.service.executions.list()
    success = False
    for execution in executions.all():
        if executed_on_item(execution, item):
            success = True

    assert success, 'Updating item did not trigger service' if not success else ''
