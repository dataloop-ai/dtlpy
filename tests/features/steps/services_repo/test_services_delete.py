import behave


@behave.when(u'I delete service by "{deletion_format}"')
def step_impl(context, deletion_format):
    if deletion_format == 'id':
        assert context.project.services.delete(service_id=context.service.id)
    elif deletion_format == 'name':
        assert context.project.services.delete(service_name=context.service.name)
    else:
        assert context.service.delete()


@behave.then(u"There are no services")
def step_impl(context):
    assert context.package.services.list().items_count == 0


@behave.when(u'I try to uninstall service')
def step_impl(context):
        try:
            context.service = context.project.services.list().items[0]
            assert context.service is not None, f"TEST FAILED: Missing service"
            context.service.delete()
            context.error = None
        except Exception as e:
            context.error = e


@behave.when(u'I uninstall service')
def step_impl(context):
    context.service = context.project.services.list().items[0]
    assert context.service is not None, f"TEST FAILED: Missing service"
    r = context.service.delete()
    assert r
