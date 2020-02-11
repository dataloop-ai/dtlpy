import behave


@behave.when(u"I list services")
def step_impl(context):
    context.service_list = context.package.services.list()


@behave.then(u'I receive a Service list of "{count}" objects')
def step_impl(context, count):
    assert len(context.service_list) == int(count)
    if int(count) > 0:
        for service in context.service_list:
            assert isinstance(service, context.dl.entities.Service)
