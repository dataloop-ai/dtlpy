import behave


@behave.when(u'I delete trigger by "{deletion_format}"')
def step_impl(context, deletion_format):
    if deletion_format == 'id':
        assert context.deployment.triggers.delete(trigger_id=context.trigger.id)
    elif deletion_format == 'name':
        assert context.deployment.triggers.delete(trigger_name=context.trigger.name)
    else:
        assert context.trigger.delete()


@behave.then(u"There are no triggers")
def step_impl(context):
    assert len(context.deployment.triggers.list()) == 0
