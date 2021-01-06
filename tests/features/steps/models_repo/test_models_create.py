import behave
import random
import string


@behave.fixture
def delete_all_mdoels(context):
    for page in context.project.models.list():
        for model in page:
            context.project.models.delete(model_id=model.id)


@behave.given(u'There are no models')
def step_impl(context):
    behave.use_fixture(delete_all_mdoels, context)
    assert len(context.project.models.list()) == 0
    context.model_count = 0


@behave.when(u'I create a model with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    model_name = 'random_model_{}'.format(rand_str)
    context.model = context.project.models.create(model_name=model_name)
    context.model_count += 1


@behave.then(u'Model object with the same name should be exist')
def step_impl(context):
    assert isinstance(context.model, context.dl.entities.Model)


@behave.then(u'Model object with the same name should be exist in host')
def step_impl(context):
    model_get = context.project.models.get(model_name=context.model.name)
    assert model_get.to_json() == context.model.to_json()


@behave.when(u'When I try to create a model with a blank name')
def step_impl(context):
    try:
        context.project.models.create('')
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Model with same name does not exists')
def step_impl(context):
    try:
        context.project.models.get(model_name=context.model.name)
    except context.dl.exceptions.NotFound:
        # good results
        pass
    except:
        # model still exists
        assert False


@behave.given(u'I create a model with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    model_name = 'random_model_{}'.format(rand_str)
    context.model = context.project.models.create(model_name=model_name)
    context.model_count += 1


@behave.when(u'I try to create a model by the same name')
def step_impl(context):
    try:
        context.project.models.create(model_name=context.model.name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No model was created')
def step_impl(context):
    assert len(context.project.models.list()) == context.model_count
