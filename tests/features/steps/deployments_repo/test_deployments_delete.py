import behave


@behave.when(u'I delete deployment by "{deletion_format}"')
def step_impl(context, deletion_format):
    if deletion_format == 'id':
        assert context.plugin.deployments.delete(deployment_id=context.deployment.id)
    elif deletion_format == 'name':
        assert context.plugin.deployments.delete(deployment_name=context.deployment.name)
    else:
        assert context.deployment.delete()


@behave.then(u"There are no deployments")
def step_impl(context):
    assert len(context.plugin.deployments.list()) == 0
