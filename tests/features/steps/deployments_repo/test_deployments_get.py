import behave
import os


@behave.when(u'I get deployment by id')
def step_impl(context):
    context.deployment_get = context.project.deployments.get(deployment_id=context.deployment.id)


@behave.when(u'I get deployment by name')
def step_impl(context):
    context.deployment_get = context.project.deployments.get(deployment_name=context.deployment.name)

@behave.then(u'Deployment received equals to deployment created')
def step_impl(context):
    assert context.deployment.to_json() == context.deployment_get.to_json()
