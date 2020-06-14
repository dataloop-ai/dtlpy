import behave


@behave.when(u'I delete service by "{deletion_format}"')
def step_impl(context, deletion_format):
    if deletion_format == 'id':
        assert context.package.services.delete(service_id=context.service.id)
    elif deletion_format == 'name':
        assert context.package.services.delete(service_name=context.service.name)
    else:
        assert context.service.delete()


@behave.then(u"There are no services")
def step_impl(context):
    assert context.package.services.list().items_count == 0
