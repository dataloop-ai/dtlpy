import behave
import json


@behave.when(u'I create a deployment')
def step_impl(context):
    deployment_name = None
    plugin = None
    revision = None
    config = None
    runtime = None

    params = context.table.headings
    for param in params:
        param = param.split('=')
        if param[0] == 'deployment_name':
            if param[1] != 'None':
                deployment_name = param[1]
        elif param[0] == 'plugin':
            if param[1] != 'None':
                plugin = param[1]
        elif param[0] == 'revision':
            if param[1] != 'None':
                revision = int(param[1])
        elif param[0] == 'config':
            if param[1] != 'None':
                config = json.loads(param[1])
        elif param[0] == 'runtime':
            if param[1] != 'None':
                runtime = json.loads(param[1])

    context.deployment = context.plugin.deployments.create(
        deployment_name=deployment_name,
        plugin=context.plugin,
        revision=revision,
        config=config,
        runtime=runtime
    )
    if hasattr(context, 'first_deployment'):
        context.second_deployment = context.deployment
    else:
        context.first_deployment = context.deployment


@behave.then(u"I receive a Deployment entity")
def step_impl(context):
    assert isinstance(context.deployment, context.dl.entities.Deployment)
