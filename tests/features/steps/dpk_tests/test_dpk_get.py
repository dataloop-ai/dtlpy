import behave


@behave.when(u'I try get the dpk by id')
def step_impl(context):
    try:
        context.dpk = context.dl.dpks.get(dpk_id=context.published_dpk.id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I get the dpk by name')
def step_impl(context):
    context.dpk = context.dl.dpks.get(dpk_name=context.published_dpk.name)


@behave.then(u'I have the same dpk as the published dpk')
def step_impl(context):
    to_json = context.dpk.to_json()
    to_json.pop('trusted', None)
    if 'context' in to_json and to_json['context'] is None:
        to_json.pop('context', None)
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


@behave.when(u'I get global dpk by name "{dpk_name}"')
def step_impl(context, dpk_name):
    try:
        context.dpk = context.dl.dpks.get(dpk_name=dpk_name)
    except Exception as e:
        raise e
