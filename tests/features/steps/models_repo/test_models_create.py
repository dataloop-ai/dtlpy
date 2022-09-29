import behave
import random
import string
import os


@behave.when(u'I create a model with a random name')
@behave.given(u'I create a model with a random name')
def step_impl(context):
    rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    model_name = 'random_model_{}'.format(rand_str)
    # create dataset
    try:
        context.dataset = context.project.datasets.get('model_dataset')
    except context.dl.exceptions.NotFound:
        context.dataset = context.project.datasets.create('model_dataset')
    # create model
    context.model = context.package.models.create(model_name=model_name,
                                                  dataset_id=context.dataset.id,
                                                  ontology_id=context.dataset.ontology_ids[0])
    if not hasattr(context, 'model_count'):
        context.model_count = 0
    context.model_count += 1


@behave.then(u'Model object with the same name should be exist')
def step_impl(context):
    assert isinstance(context.model, context.dl.entities.Model)


@behave.then(u'Model object with the same name should be exist in host')
def step_impl(context):
    model_get = context.package.models.get(model_name=context.model.name)
    assert model_get.to_json() == context.model.to_json()


@behave.when(u'I create a model with the same name')
def step_impl(context):
    try:
        context.package.models.create(model_name=context.model.name,
                                      dataset_id=context.dataset.id,
                                      ontology_id=context.dataset.ontology_ids[0])
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'No model was created')
def step_impl(context):
    pages = context.package.models.list()
    assert pages.items_count == context.model_count, 'model count doesnt match. {} from server, {} from test'.format(pages.items_count, context.model_count)
