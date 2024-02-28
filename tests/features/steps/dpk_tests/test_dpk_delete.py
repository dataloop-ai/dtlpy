import behave


@behave.when(u'I delete published_dpk')
def step_impl(context):
    context.published_dpk.delete()
    if hasattr(context.feature, 'dpks'):
        context.feature.dpks.pop()


@behave.when(u'I delete dpk with all revisions')
def step_impl(context):
    for dpk in context.dpk.revisions.items:
        dpk.delete()
        if hasattr(context.feature, 'dpks'):
            context.feature.dpks.pop()


