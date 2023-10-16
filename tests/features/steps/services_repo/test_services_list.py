import behave


@behave.when(u"I list services")
def step_impl(context):
    context.service_list = context.package.services.list()


@behave.when(u"I list services in project")
def step_impl(context):
    context.service_list = context.project.services.list()


@behave.then(u'I receive a Service list of "{count}" objects')
def step_impl(context, count):
    assert context.service_list.items_count == int(count)
    if int(count) > 0:
        for page in context.service_list:
            for service in page:
                assert isinstance(service, context.dl.entities.Service)
