import behave
import json


@behave.when(u"I update trigger")
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

    context.trigger.filters = filters
    context.trigger.resource = resource
    context.trigger.actions = actions
    context.trigger.active = active

    context.trigger_update = context.trigger.update()


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

    assert context.trigger_update.filters == filters
    assert context.trigger_update.resource == resource
    assert context.trigger_update.actions == actions
    assert context.trigger_update.active == active

@behave.then(u"I receive an updated Trigger object")
def step_impl(context):
    assert isinstance(context.trigger_update, context.dl.entities.Trigger)
