import behave


@behave.when(u"I list triggers")
def step_impl(context):
    context.trigger_list = context.service.triggers.list()


@behave.then(u'I receive a Trigger list of "{count}" objects')
def step_impl(context, count):
    assert context.trigger_list.items_count == int(count)
    if int(count) > 0:
        for page in context.trigger_list:
            for trigger in page:
                assert isinstance(trigger, context.dl.entities.Trigger) or \
                       isinstance(trigger, context.dl.entities.trigger.CronTrigger)


@behave.then(u'I have "{count}" triggers in project')
def step_impl(context, count):
    triggers_count = context.project.triggers.list().items_count
    assert triggers_count == int(count), f"Expected {count} triggers, but got {triggers_count}"
