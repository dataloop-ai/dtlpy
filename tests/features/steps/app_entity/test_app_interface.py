import behave


@behave.when(u'I create a context.custom_installation var')
def step_impl(context):
    if hasattr(context, "dpk"):
        context.custom_installation = context.dpk.to_json()
    else:
        raise AttributeError("'dpk' not found in 'context'")
