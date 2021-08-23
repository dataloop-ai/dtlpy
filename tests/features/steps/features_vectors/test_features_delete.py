import behave
import random
import string


@behave.then(u'features set does not exists')
def step_impl(context):
    try:
        context.project.feature_sets.get(feature_set_id=context.feature_set.id)
    except context.dl.exceptions.NotFound:
        # good results
        pass
    except:
        # features still exists
        assert False


@behave.then(u'features does not exists')
def step_impl(context):
    try:
        context.feature_set.features.get(feature_id=context.feature.id)
    except context.dl.exceptions.NotFound:
        # good results
        pass
    except:
        # features still exists
        assert False


@behave.when(u'I delete the features set that was created')
def step_impl(context):
    context.project.feature_sets.delete(feature_set_id=context.feature_set.id)


@behave.when(u'I delete the features that was created')
def step_impl(context):
    context.feature_set.features.delete(feature_id=context.feature.id)
