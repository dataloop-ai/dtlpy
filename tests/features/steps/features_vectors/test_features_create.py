import behave
import random
import string


@behave.given(u'There are no feature sets')
def step_impl(context):
    try:
        for f in context.project.feature_sets.list():
            f.delete()
        assert len(context.project.feature_sets.list()) == 0
    except Exception as error:
        assert 'not found' in error.args[1]


@behave.when(u'I create a feature sets with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    feature_sets_name = 'random_{}'.format(rand_str)
    context.feature_set = context.project.feature_sets.create(name=feature_sets_name,
                                                              set_type='model',
                                                              entity_type='item',
                                                              size=3)
    context.to_delete_feature_set_ids.append(context.feature_set.id)


@behave.when(u'I create a feature')
def step_impl(context):
    context.feature = context.feature_set.features.create(value=[0, 2, 15],
                                                          feature_set_id=context.feature_set.id,
                                                          entity_id=context.item.id,
                                                          version='1.0.0',
                                                          project_id=context.project.id)
    context.to_delete_feature_ids.append(context.feature.id)


@behave.then(u'FeatureSet object should be exist')
def step_impl(context):
    assert isinstance(context.feature_set, context.dl.entities.FeatureSet)


@behave.then(u'Feature object should be exist')
def step_impl(context):
    assert isinstance(context.feature, context.dl.entities.Feature)


@behave.then(u'Feature object should be exist in host')
def step_impl(context):
    feature_get = context.project.features.get(feature_id=context.feature.id)
    assert feature_get.to_json() == context.feature.to_json()


@behave.then(u'FeatureSet object should be exist in host')
def step_impl(context):
    feature_set_get = context.project.feature_sets.get(feature_set_id=context.feature_set.id)
    assert feature_set_get.to_json() == context.feature_set.to_json()


@behave.then(u'FeatureSet list have len 1')
def step_impl(context):
    assert len(context.project.feature_sets.list()) == 1


@behave.then(u'Feature list have len 1')
def step_impl(context):
    assert len(context.feature_set.features.list()) == 1


@behave.when(u'I get feature sets')
def step_impl(context):
    context.feature_set_get = context.project.feature_sets.get(feature_set_id=context.feature_set.id)


@behave.then(u'It is equal to feature sets created')
def step_impl(context):
    assert context.feature_set.to_json() == context.feature_set_get.to_json()


@behave.when(u'I get feature')
def step_impl(context):
    context.feature_get = context.project.features.get(feature_id=context.feature.id)


@behave.then(u'It is equal to feature created')
def step_impl(context):
    assert context.feature.to_json() == context.feature_get.to_json()
