import behave
import json


@behave.when(u"I update deployment")
def step_impl(context):
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "revision":
            if param[1] != "None":
                revision = int(param[1])
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])

    context.deployment.revision = revision
    context.deployment.config = config
    context.deployment.runtime = runtime

    context.deployment_update = context.deployment.update()


@behave.then(u"Deployment attributes are modified")
def step_impl(context):
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split("=")
        if param[0] == "revision":
            if param[1] != "None":
                revision = int(param[1])
        elif param[0] == "config":
            if param[1] != "None":
                config = json.loads(param[1])
        elif param[0] == "runtime":
            if param[1] != "None":
                runtime = json.loads(param[1])

    assert context.trigger_update.revision == revision
    assert context.trigger_update.config == config
    assert context.trigger_update.runtime == runtime

@behave.then(u"I receive an updated Deployment object")
def step_impl(context):
    assert isinstance(context.deployment_update, context.dl.entities.Deployment)
