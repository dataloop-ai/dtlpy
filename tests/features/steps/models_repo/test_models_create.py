import behave
import random
import string
import os


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


@behave.when(u'I create a model with a blank name')
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
    if not hasattr(context, 'model_count'):
        context.model_count = 0
    context.model_count += 1


@behave.when(u'I create a model with the same name')
def step_impl(context):
    try:
        context.project.models.create(model_name=context.model.name)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No model was created')
def step_impl(context):
    assert len(context.project.models.list()) == context.model_count


@behave.when(u'I push codebase from "{codebase_path}"')
def step_impl(context, codebase_path):
    try:
        codebase_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], codebase_path)
        model = context.dl.models.push(
            model=context.model,
            src_path=codebase_path
        )
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Model object has ItemCodebase')
def step_impl(context):
    model = context.dl.models.get(model_id=context.model.id)
    assert isinstance(model.codebase, context.dl.ItemCodebase)


@behave.when(u'I rename "{entity}" to {new_name}')
def step_impl(context, entity, new_name):
    entity = getattr(context, entity)
    entity.name = new_name
    entity.update()


@behave.then(u'"{entity}" name is {new_name}')
def step_impl(context, entity, new_name):
    repo_name = '{}s'.format(entity)
    entity_object = getattr(context, entity)
    host_entity = getattr(context.dl, repo_name).get(**{'{}_id'.format(entity): entity_object.id})
    assert host_entity.name == new_name, "Name was not change: current: {!r}, new {!r}".format(host_entity.name,
                                                                                               new_name)
