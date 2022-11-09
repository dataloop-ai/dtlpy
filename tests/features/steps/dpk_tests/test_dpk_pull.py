import os.path

import behave


@behave.when(u'I pull the dpk')
def step_impl(context):
    context.dpk_path = context.dl.dpks.pull(dpk_id=context.published_dpk.id)


@behave.then(u'I should have a dpk file')
def step_impl(context):
    assert os.path.exists(context.dpk_path)
