import behave


@behave.when(u"I list deployments")
def step_impl(context):
    context.deployment_list = context.plugin.deployments.list()


@behave.then(u'I receive a Deployment list of "{count}" objects')
def step_impl(context, count):
    assert len(context.deployment_list) == int(count)
    if int(count) > 0:
        for deployment in context.deployment_list:
            assert isinstance(deployment, context.dl.entities.Deployment)
