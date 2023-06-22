import behave


@behave.when(u'I get the dpk by id')
def step_impl(context):
    context.dpk = context.dl.dpks.get(dpk_id=context.published_dpk.id)


@behave.when(u'I get the dpk by name')
def step_impl(context):
    context.dpk = context.dl.dpks.get(dpk_name=context.published_dpk.name)


@behave.then(u'I have the same dpk as the published dpk')
def step_impl(context):
    to_json = context.dpk.to_json()
    to_json.pop('trusted', None)
    assert to_json == context.published_dpk.to_json()


@behave.when(u'I get a dpk with invalid id')
def step_impl(context):
    try:
        context.dpk = context.dl.dpks.get(dpk_id="1")
    except Exception as e:
        context.e = e


@behave.then(u'I should get an exception')
def step_impl(context):
    assert context.e is not None
