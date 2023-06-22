import behave


@behave.when(u'I list the dpks')
def step_impl(context):
    context.dpk_list = context.dl.dpks.list()


@behave.then(u'I should see at least {count} dpks')
def step_impl(context, count):
    assert len(context.dpk_list) >= int(count)
