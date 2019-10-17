import behave
import random


@behave.given(u"I create a trigger")
def step_impl(context):
    name = None
    filters = None
    resource = None
    actions = None
    active = None
    executionMode = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "name":
            if param[1] != "None":
                name = '{}-{}'.format(param[1], random.randrange(1000, 10000))
        elif param[0] == "filters":
            if param[1] != "None":
                filters = context.filters
        elif param[0] == "resource":
            if param[1] != "None":
                resource = param[1]
        elif param[0] == "action":
            if param[1] != "None":
                actions = param[1]
        elif param[0] == "active":
            active = param[1] == "True"
        elif param[0] == "executionMode":
            if param[1] != "None":
                executionMode = param[1]

    context.trigger = context.deployment.triggers.create(
        deployment_id=context.deployment.id,
        name=name,
        filters=filters,
        resource=resource,
        actions=actions,
        active=active,
        executionMode=executionMode,
    )


@behave.when(u"I get trigger by id")
def step_impl(context):
    context.trigger_get = context.deployment.triggers.get(trigger_id=context.trigger.id)


@behave.when(u"I get trigger by name")
def step_impl(context):
    context.trigger_get = context.deployment.triggers.get(trigger_name=context.trigger.name)


@behave.then(u"I receive a Trigger object")
def step_impl(context):
    assert isinstance(context.trigger_get, context.dl.entities.Trigger)


@behave.then(u"Trigger received equals to trigger created")
def step_impl(context):
    assert context.trigger_get.to_json() == context.trigger.to_json()
