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


@behave.then(u'I validate deleted action trigger on "{resource_type}"')
def step_impl(context, resource_type):

    assert context.service.executions.list().items_count == 1, "No executions in service"

    context.trigger_type = resource_type
    num_try = 60
    interval = 10
    triggered = False

    for i in range(num_try):
        time.sleep(interval)
        if resource_type == 'item':
            if context.service.executions.list()[0][0].input['item']['item_id'] == context.item.id:
                triggered = True
                break
        elif resource_type == 'annotation':
            if context.service.executions.list()[0][0].input['annotation']['annotation_id'] == context.annotation.id:
                triggered = True
                break

    assert triggered