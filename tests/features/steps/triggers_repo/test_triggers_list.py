import behave


@behave.when(u"I list triggers")
def step_impl(context):
    context.trigger_list = context.service.triggers.list()


@behave.then(u'I receive a Trigger list of "{count}" objects')
def step_impl(context, count):
    assert len(context.trigger_list) == int(count)
    if int(count) > 0:
        for trigger in context.trigger_list:
            assert isinstance(trigger, context.dl.entities.Trigger)
