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
    context.ontology_id = context.recipe.ontology_ids[0]
    context.ontology = context.recipe.ontologies.get(context.ontology_id)
    for label in context.labels:
        context.ontology.labels.append(context.dl.Label.from_root(label))
    context.ontology.attributes = ['Occlusion1', 'Occlusion2']
    context.recipe.ontologies.update(ontology=context.ontology, system_metadata=True)


@behave.given(u'There is annotation x')
def step_impl(context):
    context.annotation_x = context.item.annotations.list()[0]

@behave.then(u'I validate that I have "{number}" annotations in item')
def atp_step_impl(context, number):
    filters = context.dl.Filters(resource=context.dl.FiltersResource.ANNOTATION)
    context.annotations = context.dataset.annotations.list(filters=filters)
    assert context.annotations.items_count == int(number)

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


@behave.given(u'I get AnnotationCollection from json "{annotations_path}"')
def step_impl(context, annotations_path):
    annotations_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotations_path)

    try:
        context.annotation_collection = context.dl.AnnotationCollection.from_json_file(filepath=annotations_path, item=context.item)
    except Exception as e:
        context.error = e
        assert False, context.error

@behave.then(u'I validate that I have an annotation in item with the name "{name}"')
def atp_step_impl(context, name):
    context.annotations = context.item.annotations.list()
    for i in range(0, len(context.annotations)):
        if context.annotations[i].label == name:
           break
    else:
        assert False, f"No annotation found with the name '{name}'"

@behave.then(u'I have "{number}" "{type}" annotations')
def atp_step_impl(context, number, type):
    count = int(number)
    context.annotations = context.item.annotations.list()
    type_annotations = [annotation for annotation in context.annotations if annotation.type == type]
    assert len(type_annotations) == count, f"Expected {count} {type} annotations, but found {len(type_annotations)}"