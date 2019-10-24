import behave
import json


@behave.given(u'There are no deployments')
def step_impl(context):
    assert len(context.plugin.deployments.list()) == 0


@behave.when(u'I deploy a deployment')
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

    context.deployment = context.plugin.deployments.deploy(
        deployment_name=deployment_name,
        plugin=context.plugin,
        revision=revision,
        config=config,
        runtime=runtime
    )


@behave.then(u'There is only one deployment')
def step_impl(context):
    deployments_list = context.plugin.deployments.list()
    assert len(deployments_list) == 1
    assert deployments_list[0].to_json() == context.deployment.to_json()
