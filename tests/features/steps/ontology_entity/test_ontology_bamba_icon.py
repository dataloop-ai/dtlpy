import behave
import os
import time


@behave.when(u'I add label "{label_tag}" to ontology with "{icon_path}"')
def step_impl(context, label_tag, icon_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], icon_path)
    context.ontology.add_label(label_name="label-{}".format(label_tag), icon_path=file_path, update_ontology=True)


@behave.then(u'I validate dataset labels images are different')
def step_impl(context):
    context.dataset = context.project.datasets.get(dataset_name=context.dataset.name)
    items_filename = []
    for label in context.dataset.labels:
        item = context.project.items.get(item_id=label.display_data['displayImage']['itemId'])
        items_filename.append(item.name)

    assert len(tuple(items_filename)) == len(context.dataset.labels), "TEST FAILED: Items created with the same name" \
                                                                      "\nItems name list:{}".format(items_filename)
