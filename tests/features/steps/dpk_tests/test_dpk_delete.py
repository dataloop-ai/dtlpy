import behave


@behave.when(u'I delete dpk')
def step_impl(context):
    context.published_dpk.delete()
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.pop()
