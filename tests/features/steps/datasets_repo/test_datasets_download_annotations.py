import behave
import os
import json
import shutil
import time


@behave.given(u'Item in path "{item_path}" is uploaded to "Dataset"')
def step_impl(context, item_path):
    item_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], item_path)
    context.item = context.dataset.items.upload(local_path=item_path)
    # wait for platform attributes
    time.sleep(6)
    context.item = context.dataset.items.get(item_id=context.item.id)
    if context.item.name.endswith('.mp4') and context.item.fps is None:
        context.item.fps = 25
    if context.item.name.endswith('.jpg') or context.item.name.endswith('.png'):
        if context.item.height is None:
            context.item.height = 768
        if context.item.width is None:
            context.item.width = 1536



@behave.given(u'There are a few annotations in the item')
def step_impl(context):
    labels = [
        {
            "value": {
                "tag": "dog",
                "displayLabel": "Dog",
                "color": "#0305da",
                "attributes": list(),
            },
            "children": list(),
        },
        {
            "value": {
                "tag": "cat",
                "displayLabel": "Cat",
                "color": "#018f67",
                "attributes": list(),
            },
            "children": list(),
        },
    ]
    labels = [context.dl.Label.from_root(root) for root in labels]
    recipe_id = context.dataset.metadata["system"]["recipes"][0]
    recipe = context.dataset.recipes.get(recipe_id)
    ont_id = recipe.ontologyIds[0]
    ontology = recipe.ontologies.get(ont_id)
    ontology.labels = labels
    recipe.ontologies.update(ontology)
    context.dataset.attributes = ['attr1', 'attr2']
    context.project.datasets.update(dataset=context.dataset, system_metadata=True)
    annotation1 = {'attributes': ['attr1'],
                   'coordinates': [[{'x': 100, 'y': 100},
                                    {'x': 320, 'y': 100},
                                    {'x': 320, 'y': 250},
                                    {'x': 100, 'y': 250}]],
                   'label': 'dog',
                   'type': 'box'}
    annotation2 = {'attributes': ['attr2'],
                   'coordinates': [[{'x': 400, 'y': 300},
                                    {'x': 700, 'y': 300},
                                    {'x': 700, 'y': 400},
                                    {'x': 400, 'y': 400}]],
                   'label': 'cat',
                   'type': 'box'}
    context.annotations = [annotation1, annotation2]
    context.item.annotations.upload(context.annotations)


@behave.when(u'I download dataset annotations')
def step_impl(context):
    context.dataset.download_annotations(local_path=os.environ['DATALOOP_TEST_ASSETS'])


@behave.then(u'I get a folder named "{folder_name}" in assets folder')
def step_impl(context, folder_name):
    folder_path = os.environ['DATALOOP_TEST_ASSETS']
    dirs = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    assert folder_name in dirs


@behave.then(u'Annotations downloaded equal to the annotations uploaded')
def step_impl(context):
    file_path = 'json/0000000162.json'
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as json_file:
        annotations_downloaded = json.load(json_file)
    annotations_downloaded = annotations_downloaded['annotations']
    assert len(annotations_downloaded) == len(context.annotations)
    for annotation in annotations_downloaded:
        ann = {'attributes': annotation['attributes'],
               'coordinates': annotation['coordinates'],
               'label': annotation['label'],
               'type': annotation['type']}
        assert ann in context.annotations


@behave.given(u'There is no folder by the name of "{folder_name}" in assets folder')
def step_impl(context, folder_name):
    folder_path = os.environ['DATALOOP_TEST_ASSETS']
    dirs = [name for name in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, name))]
    if folder_name in dirs:
        path = os.path.join(folder_path, folder_name)
        shutil.rmtree(path)


@behave.then(u'The folder named "{folder_name}" in folder assets is empty')
def step_impl(context, folder_name):
    folder_path = os.environ['DATALOOP_TEST_ASSETS']
    assert os.listdir(os.path.join(folder_path, folder_name)) == list()
