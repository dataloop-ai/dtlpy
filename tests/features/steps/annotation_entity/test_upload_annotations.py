from behave import given, when, then
import os
import json
from PIL import Image
import numpy as np
import dtlpy as dl


@given(u'Dataset ontology has attributes "{first_attribute}" and "{second_attribute}"')
def step_impl(context, first_attribute, second_attribute):
    context.recipe = context.dataset.recipes.list()[0]
    context.ontology = context.recipe.ontologies.list()[0]
    context.ontology.attributes = [first_attribute, second_attribute]
    context.ontology = context.recipe.ontologies.update(context.ontology)


@when(u'Item is annotated with annotations in file: "{annotations_path}"')
def step_impl(context, annotations_path):
    annotations_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], annotations_path)

    with open(annotations_path, 'r') as f:
        context.annotations = json.load(f)
    context.item.annotations.upload(context.annotations)
    context.last_response = context.item._client_api.last_response.json()


@then(u'Item video annotations in host equal annotations in file "{annotations_path}"')
def step_impl(context, annotations_path):
    annotations_get = context.item.annotations.list()
    for ann in annotations_get:
        metadata = ann.to_json()['metadata']
        ann = {'type': ann.type,
               'attributes': ann.attributes,
               'label': ann.label,
               'coordinates': ann.coordinates,
               'metadata': metadata}

        if 'coordinateVersion' in ann['metadata']['system']:
            ann['metadata']['system'].pop('coordinateVersion')

        assert ann in context.annotations


@then(u'Item annotations in host equal annotations in file "{annotations_path}"')
def step_impl(context, annotations_path):
    annotations_list = context.item.annotations.list()
    anns = list()
    for ann in context.annotations:
        ann = {'type': ann['type'],
               'attributes': ann['attributes'],
               'label': ann['label'],
               'coordinates': ann['coordinates']}
        anns.append(ann)
    for ann in annotations_list:
        ann = {'type': ann.type,
               'attributes': ann.attributes,
               'label': ann.label,
               'coordinates': ann.coordinates}
        assert ann in anns


@when(u'I draw all annotations to image "{image_path}"')
def step_impl(context, image_path):
    image_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], image_path)
    annotations_get = context.item.annotations.list()
    context.item = context.dataset.items.get(item_id=context.item.id)
    # try loading from numpy
    # img_arr = np.asarray(Image.open(image_path))
    img_arr = np.load(image_path + '.npy')

    for ann in annotations_get:
        img_arr = ann.show(image=img_arr)
    context.image_drawn = img_arr


@then(u'Image drawn to "{drawn_image_path}" equal image in "{should_be_path}"')
def step_impl(context, should_be_path, drawn_image_path):
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)
    drawn_image_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], drawn_image_path)

    # try loading from numpy
    # im_drawn = np.asarray(Image.open(drawn_image_path))
    # im_should = np.asarray(Image.open(should_be_path))
    im_drawn = np.load(drawn_image_path + '.npy')
    im_should = np.load(should_be_path + '.npy')

    assert (im_drawn == im_should).all


@when(u'I draw to image in "{im_path}" all annotations with param "{annotation_format}"')
def step_impl(context, annotation_format, im_path):
    im_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], im_path)
    filters = dl.Filters(resource=dl.FiltersResource.ANNOTATION)
    filters.sort_by(field='label', value=dl.FiltersOrderByDirection.ASCENDING)
    filters.sort_by(field='createdAt', value=dl.FiltersOrderByDirection.DESCENDING)
    annotations_get = context.item.annotations.list(filters=filters)
    context.item = context.dataset.items.get(item_id=context.item.id)

    # make sure we have height and width 
    if context.item.height is None:
        context.item.height = 768
    if context.item.width is None:
        context.item.width = 1536

    # try loading from numpy
    # context.img_arr = np.asarray(Image.open(im_path)))
    context.img_arr = np.load(im_path + '.npy')

    context.img_arr = context.img_arr.copy()
    for ann in annotations_get:
        context.img_arr = ann.show(image=context.img_arr, annotation_format=annotation_format)
    context.mask = context.img_arr


@then(u'Annotations drawn equal numpy in "{should_be_path}"')
def step_impl(context, should_be_path):
    should_be_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], should_be_path)
    if not np.array_equal(context.mask, np.load(should_be_path)):
        np.save(should_be_path.replace('.npy', '_wrong.npy'), context.mask)
        assert False


@given(u'Classes in file: "{labels_path}" are uploaded to test Dataset')
def step_impl(context, labels_path):
    labels_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], labels_path)
    context.recipe = context.dataset.recipes.list()[0]
    context.ontology = context.recipe.ontologies.list()[0]
    with open(labels_path, 'r', encoding="utf8") as f:
        context.labels = json.load(f)
    context.ontology.add_labels(label_list=context.labels)
    context.ontology = context.ontology.update(system_metadata=True)
    for label in context.ontology.labels:
        assert label.to_root() in context.labels
    assert len(context.ontology.labels) == len(context.labels)
