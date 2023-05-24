import behave
import os
import json


@behave.when(u'I create a new plain recipe')
def step_impl(context):
    context.recipe = context.dataset.recipes.create()


@behave.when(u'I create a new project recipe')
def step_impl(context):
    context.recipe = context.dl.recipes.create(recipe_name="test-checkout")


@behave.then(u'recipe in host is exist')
def step_impl(context):
    recipes = context.project.recipes.list()
    for recipe in recipes.items:
        if recipe.id == context.recipe.id:
            assert True
            return
    assert False, "recipe not found"


@behave.when(u'I update dataset recipe to the new recipe')
def step_impl(context):
    context.dataset.metadata['system']['recipes'] = [context.recipe.id]
    context.project.datasets.update(dataset=context.dataset,
                                    system_metadata=True)


@behave.then(u'Dataset recipe in host equals the one created')
def step_impl(context):
    dataset_get = context.project.datasets.get(dataset_id=context.dataset.id)
    recipe_ids = dataset_get.metadata['system']['recipes']
    assert len(recipe_ids) == 1
    context.recipe_get = context.dataset.recipes.get(recipe_ids[0])
    assert context.recipe.to_json() == context.recipe_get.to_json()


@behave.when(
    u'I create a new recipe with param labels from "{class_file}" and attributes: "{attribute1}", "{attribute2}"')
def step_impl(context, class_file, attribute1, attribute2):
    class_file = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], class_file)
    with open(class_file) as f:
        context.labels = json.load(f)
    context.recipe = context.dataset.recipes.create(attributes=[attribute1, attribute2],
                                                    labels=context.labels)


@behave.then(u'Dataset ontology in host has labels from "{class_file}" and attributes: "{attribute1}", "{attribute2}"')
def step_impl(context, class_file, attribute1, attribute2):
    ontology_get = context.recipe.ontologies.get(ontology_id=context.recipe.ontology_ids[0])
    for root in ontology_get.to_json()['roots']:
        assert root in context.labels
    assert ontology_get.attributes == [attribute1, attribute2]


@behave.when(u'I create a new plain recipe with existing ontology id')
def step_impl(context):
    recipe = context.dataset.recipes.get(context.dataset.metadata['system']['recipes'][0])
    context.ontology = recipe.ontologies.get(recipe.ontology_ids[0])
    context.recipe = context.dataset.recipes.create(ontology_ids=context.ontology.id)
