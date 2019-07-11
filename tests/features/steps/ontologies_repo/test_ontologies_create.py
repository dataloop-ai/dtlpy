import time
import behave
import os
import json


@behave.given(u"dataset has recipe")
def step_impl(context):
    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    assert len(context.dataset.metadata["system"]["recipes"]) > 0


@behave.given(u"dataset has at least {count} ontology")
def step_impl(context, count):
    assert len(context.recipe.ontologyIds) >= int(count)


@behave.when(u'I create a new ontology with labels from file "{file_path}" and attributes "{attributes}"')
def step_impl(context, file_path, attributes):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)

    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    context.ontology = context.recipe.ontologies.create(labels=context.labels,
                                                        project_ids=context.dataset.project.id,
                                                        attributes=attributes)


@behave.when(u'I create a new ontology with labels from file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)

    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    context.ontology = context.recipe.ontologies.create(labels=context.labels,
                                                        project_ids=context.dataset.project.id,
                                                        attributes=list())


@behave.when(u'I create a new ontology with no projectIds, with labels from file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)

    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    context.ontology = context.recipe.ontologies.create(
        labels=context.labels,
        attributes=list())


@behave.when(u"I try to create a new ontology with labels '{labels}'")
def step_impl(context, labels):
    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    try:
        context.ontology = context.recipe.ontologies.create(
            labels=json.loads(labels),
            attributes=list())
        context.error = None
    except Exception as e:
        context.error = e


@behave.when(u'I update dataset ontology to the one created')
def step_impl(context):
    context.recipe.ontologyIds = [context.ontology.id]
    context.dataset.recipes.update(context.recipe)


@behave.when(u'I try toupdate dataset ontology to the one created')
def step_impl(context):
    context.recipe.ontologyIds = [context.ontology.id]
    try:
        context.dataset.recipes.update(context.recipe)
        context.error = None
    except Exception as e:
        context.error = e


@behave.then(u'Dataset ontology in host equal ontology uploaded')
def step_impl(context):
    ontology_get = context.recipe.ontologies.get(ontology_id=context.ontology.id)
    assert ontology_get.to_json() == context.ontology.to_json()
    for root in ontology_get.to_json()['roots']:
        assert root in context.labels


@behave.when(u'I create a new ontology with labels and project id of "{other_project_name}" from file "{file_path}"')
def step_impl(context, other_project_name, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)

    context.other_project = context.dl.projects.get(project_name=other_project_name)

    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    context.ontology = context.recipe.ontologies.create(
        labels=context.labels,
        project_ids=context.other_project.id,
        attributes=list())


@behave.when(u'I try create a new ontology with labels and "{some_project_id}" from file "{file_path}"')
def step_impl(context, some_project_id, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)
    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata["system"]["recipes"][0])
    try:
        context.ontology = context.recipe.ontologies.create(
            labels=context.labels,
            project_ids=some_project_id,
            attributes=list())
        context.error = None
    except Exception as e:
        context.error = e


@behave.given(u'There is another project by the name of "{other_project_name}"')
def step_impl(context, other_project_name):
    context.other_project = context.dl.projects.create(other_project_name)
    time.sleep(5)  # to sleep because authorization takes time
