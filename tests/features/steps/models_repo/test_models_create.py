import behave
import random
import string
import os


@behave.when(u'I create a model with a random name')
@behave.given(u'I create a model with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    model_name = 'random-model-{}'.format(rand_str)
    # create dataset
    try:
        context.dataset = context.project.datasets.get('model_dataset')
    except context.dl.exceptions.NotFound:
        context.dataset = context.project.datasets.create('model_dataset', index_driver=context.index_driver_var)


    # create model
    context.model = context.package.models.create(model_name=model_name,
                                                  dataset_id=context.dataset.id,
                                                  ontology_id=context.dataset.ontology_ids[0],
                                                  train_filter=context.dl.Filters(),
                                                  project_id=context.project.id)
    if not hasattr(context, 'model_count'):
        context.model_count = 0
    context.model_count += 1


@behave.when(u'I create a model without dataset')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
    model_name = 'random_model-{}'.format(rand_str)
    context.model = context.package.models.create(model_name=model_name, dataset_id=None, project_id=context.project.id)
    if not hasattr(context, 'model_count'):
        context.model_count = 0
    context.model_count += 1


@behave.when(u'I create a model without filter')
def step_impl(context):
    try:
        rand_str = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
        model_name = 'random_model-{}'.format(rand_str)
        # create dataset
        try:
            context.dataset = context.project.datasets.get('model_dataset')
        except context.dl.exceptions.NotFound:
            context.dataset = context.project.datasets.create('model_dataset', index_driver=context.index_driver_var)
        # create model
        context.model = context.package.models.create(model_name=model_name,
                                                      dataset_id=context.dataset.id,
                                                      ontology_id=context.dataset.ontology_ids[0],
                                                      project_id=context.project.id)
    except Exception as e:
        context.error = e


@behave.when(u'I update model status to "{model_status}"')
@behave.given(u'I update model status to "{model_status}"')
def step_impl(context, model_status):
    context.model.status = model_status
    context.model.update()


@behave.when(u'I deploy the model')
def step_impl(context):
    context.model.deploy()


@behave.when(u'I train the model')
def step_impl(context):
    try:
        context.model.train()
    except Exception as e:
        context.error = e


@behave.Then(u'Model filter should not be empty')
def step_impl(context):
    assert context.model.metadata['system'].get('subsets', {}).get('train',
                                                                   None) is not None, 'train filter is empty'


@behave.then(u'The project have only one bot')
def step_impl(context):
    bots = context.project.bots.list()
    assert len(bots) == 1, 'more than one bot was created'


@behave.then(u'Model object with the same name should be exist')
def step_impl(context):
    assert isinstance(context.model, context.dl.entities.Model)


@behave.then(u'Model object with the same name should be exist in host')
def step_impl(context):
    model_get = context.project.models.get(model_name=context.model.name)
    assert model_get.to_json() == context.model.to_json()


@behave.then(u'Model module_name should be "{module_name}"')
def step_impl(context, module_name):
    module_name_input = module_name.split(",")
    if len(module_name_input) > 1:
        for i in range(len(module_name_input)):
            assert context.models[i].module_name == module_name_input[i]
    else:
        assert context.model.module_name == module_name


@behave.when(u'I create a model with the same name')
def step_impl(context):
    try:
        context.package.models.create(model_name=context.model.name,
                                      dataset_id=context.dataset.id,
                                      ontology_id=context.dataset.ontology_ids[0],
                                      project_id=context.project.id)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No model was created')
def step_impl(context):
    pages = context.project.models.list()
    assert pages.items_count == context.model_count, 'model count doesnt match. {} from server, {} from test'.format(
        pages.items_count, context.model_count)

@behave.when(u'I upload an artifact "{artifact_path}" to the model')
def step_impl(context, artifact_path):
    artifact_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], artifact_path)
    context.model.artifacts.upload(filepath=artifact_path)


@behave.when(u'I clone the model')
def step_impl(context):
    context.model_clone = context.model.clone(model_name='clone_{}'.format(context.model.name))


@behave.when(u'I delete the clone model')
def step_impl(context):
    context.model_clone.delete()


@behave.then(u'artifact is exist in the host')
def step_impl(context):
    try:
        artifact = context.dl.items.get(item_id=context.model.model_artifacts[0].id)
    except context.dl.exceptions.NotFound:
        artifact = None
    assert artifact is not None, 'artifact not found'
