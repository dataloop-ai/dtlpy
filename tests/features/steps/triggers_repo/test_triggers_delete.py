import behave, time


@behave.when(u'I delete trigger by "{deletion_format}"')
def step_impl(context, deletion_format):
    if deletion_format == 'id':
        assert context.service.triggers.delete(trigger_id=context.trigger.id)
    elif deletion_format == 'name':
        assert context.service.triggers.delete(trigger_name=context.trigger.name)
    else:
        assert context.trigger.delete()
    time.sleep(3)


@behave.then(u"There are no triggers")
def step_impl(context):
    assert context.service.triggers.list().items_count == 0
