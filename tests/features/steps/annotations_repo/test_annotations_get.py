import behave
import json
import os


@behave.given(u'Item is annotated with annotations in file: "{annotations_path}"')
def step_impl(context, annotations_path):
    annotations_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotations_path)

    with open(annotations_path, 'r') as f:
        context.annotations = json.load(f)
    if not isinstance(context.annotations, list):
        context.annotations = context.annotations['annotations']
    context.item.annotations.upload(context.annotations)


@behave.given(u'Labels in file: "{labels_file_path}" are uploaded to test Dataset')
def step_impl(context, labels_file_path):
    labels_file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], labels_file_path)
    with open(labels_file_path, 'r') as f:
        context.labels = json.load(f)
    context.recipe_id = context.dataset.metadata['system']['recipes'][0]
    context.recipe = context.dataset.recipes.get(context.recipe_id)
    context.ontology_id = context.recipe.ontologyIds[0]
    context.ontology = context.recipe.ontologies.get(context.ontology_id)
    for label in context.labels:
        context.ontology.labels.append(context.dl.Label.from_root(label))
    context.ontology.attributes = ['Occlusion1', 'Occlusion2']
    context.recipe.ontologies.update(ontology=context.ontology, system_metadata=True)


@behave.given(u'There is annotation x')
def step_impl(context):
    context.annotation_x = context.item.annotations.list()[0]


@behave.when(u'I get the annotation by id')
def step_impl(context):
    context.annotation_x_get = context.item.annotations.get(context.annotation_x.id)


@behave.then(u'I receive an Annotation object')
def step_impl(context):
    assert type(context.annotation_x_get) == context.dl.Annotation


@behave.then(u'Annotation received equals to annotation x')
def step_impl(context):
    assert context.annotation_x.to_json() == context.annotation_x_get.to_json()


@behave.when(u'I try to get a non-existing annotation')
def step_impl(context):
    try:
        context.item.annotations.get('some_id')
        context.error = None
    except Exception as e:
        context.error = e
