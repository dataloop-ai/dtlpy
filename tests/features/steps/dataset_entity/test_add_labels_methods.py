import behave
import dtlpy as dl


def compare_labels(input_labels, ontology_labels):
    for input_label in input_labels:
        label_exist = False
        nested_label = input_label['label_name'].split(".", 1)
        for ontology_label in ontology_labels:
            if nested_label[0] == ontology_label['tag']:
                label_exist = True
                if len(nested_label) == 1:
                    if 'color' in input_label:
                        assert input_label['color'] == ontology_label['color']
                    if 'display_label' in input_label:
                        assert input_label['display_label'] == ontology_label['display_label']
                    if 'attributes' in input_label:
                        assert input_label['attributes'] == ontology_label['attributes']
                    if 'children' in input_label:
                        if input_label['children']:
                            if ontology_label['children']:
                                compare_labels(input_label['children'], ontology_label['children'])
                                break
                    break
                if ontology_label['children']:
                    input_label['label_name'] = nested_label[1]
                    compare_labels([input_label], ontology_label['children'])
    return label_exist


@behave.given(u'There is no label with the same label I plan to add')
def step_impl(context):
    context.dataset.delete_labels(label_names=['aaa', 'bbb'])


@behave.when(u'I add new single label with all parameters')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'attributes': ['Name', 'Age'],
         'display_label': 'display aaa'}]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.when(u'I add single root Label')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'attributes': ['Name', 'Age'],
         'display_label': 'display aaa'}]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.when(u'I add single root Label "{name}"')
def step_impl(context, name):
    context.nested_labels = [
        {'label_name': name,
         'color': '#220605'}]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.then(u'I add single root Label')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'attributes': ['Name', 'Age'],
         'display_label': 'display aaa'}]
    try:
        context.dataset.add_labels(label_list=context.nested_labels)
    except dl.exceptions.InternalServerError:
        assert False
    assert True


@behave.then(u'Label has been added')
def step_impl(context):
    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    labels_json_from_ontology = ontology.to_json()['labels']

    assert compare_labels(context.nested_labels, labels_json_from_ontology)


@behave.when(u'I add single root Label with Label name only')
def step_impl(context):
    context.nested_labels = [{'label_name': 'aaa'}]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.when(u'I add single nested root Label with all parameters')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa.bbb',
         'color': '#220605',
         'attributes': ['Name', 'Age'],
         'display_label': 'display aaa'}]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.when(u'I add new single label with all parameters with no update_ontology parameter')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'attributes': ['Name', 'Age'],
         'display_label': 'display aaa'}]

    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    ontology.add_labels(label_list=context.nested_labels)
    ontology.update(system_metadata=True)


@behave.when(u'I add single nested Label with Label name only')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa.bbb'
         }]

    context.dataset.add_labels(label_list=context.nested_labels)


@behave.when(u'I add labels of string type')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'X.Y.Z',
         'children': [{'label_name': 'ab'},
                      {'label_name': 'bb'}]}]

    context.dataset.add_labels(label_list=["X.Y.Z.ab", "X.Y.Z.bb"])


@behave.when(u'I add labels of string type using ontology.add_labels when update_ontology is false')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'X.Y.Z',
         'children': [{'label_name': 'ab'},
                      {'label_name': 'bb'}]}]

    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    ontology.add_labels(label_list=["X", "Y"])
    ontology.update(system_metadata=True)


@behave.when(u'I add single nested label using ontology.add_label when update_ontology is true')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'X.Y.Z'}]

    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    ontology.add_label(label_name="X.Y.Z", update_ontology=True)
    ontology.update(system_metadata=True)


@behave.when(u'I add single not nested label using ontology.add_label when update_ontology is false')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'X'}]

    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    ontology.add_label(label_name="X", update_ontology=False)
    ontology.update(system_metadata=True)


@behave.then(u'I add single nested label using ontology.add_label when update_ontology is false')
def step_impl(context):
    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    try:
        ontology.add_label(label_name="X.Y.Z", update_ontology=False)
    except dl.exceptions.BadRequest:
        # to verify that Label can't be added twice
        # dtlpy.exceptions.InternalServerError: ('500', 'There is already a label with identifier "aaa"')
        return
    assert False


@behave.when(u'I add labels of ontology.label type')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'a',
         'color': '#227301',
         'children': [{'label_name': 'aa',
                       'color': '#227302',
                       'children': [{'label_name': 'aaa',
                                     'color': '#227303',
                                     },
                                    {'label_name': 'aab',
                                     'color': '#227304'}]},
                      {'label_name': 'ab',
                       'color': '#227305'}]},
        {'label_name': 'b',
         'color': '#227306',
         'children': [{'label_name': 'ba',
                       'color': '#227307'},
                      {'label_name': 'bb',
                       'color': '#227308'}]}]

    recipe = context.dataset.recipes.list()[0]
    ontology = recipe.ontologies.list()[0]

    labels = ontology.add_labels(label_list=context.nested_labels)

    ontology.labels = context.dataset.add_labels(label_list=labels)


@behave.when(u'I add many labels')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'children': [{'label_name': 'XY',
                       'color': '#227305',
                       'children': [{'label_name': 'aaa',
                                     'color': '#224705',
                                     'display_label': 'display aaa',
                                     'attributes': ['Name', 'Age'],
                                     },
                                    {'label_name': 'aab',
                                     'color': '#842367'}]},
                      {'label_name': 'XZ'}]},
        {'label_name': 'bbb',
         'color': '#287605',
         'children': [{'label_name': 'ba',
                       'color': '#298345'},
                      {'label_name': 'bb',
                       'color': '#298565'}]}]
    context.dataset.add_labels(label_list=context.nested_labels)


@behave.then(u'I update many labels')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'children': [{'label_name': 'XY',
                       'color': '#227305',
                       'children': [{'label_name': 'aaa',
                                     'color': '#224705',
                                     'display_label': 'display AAA',
                                     'attributes': ['Name1', 'Age1'],
                                     },
                                    {'label_name': 'aab',
                                     'color': '#842367'}]},
                      {'label_name': 'XZ'}]},
        {'label_name': 'bbb',
         'color': '#287605',
         'children': [{'label_name': 'ba',
                       'color': '#298345'},
                      {'label_name': 'bb',
                       'color': '#298565'}]}]
    context.dataset.update_labels(label_list=context.nested_labels)


@behave.then(u'I upsert many labels')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'aaa',
         'color': '#220605',
         'children': [{'label_name': 'XY',
                       'color': '#227305',
                       'children': [{'label_name': 'aaa',
                                     'color': '#224705',
                                     'display_label': 'display AAA',
                                     'attributes': ['Name1', 'Age2'],
                                     },
                                    {'label_name': 'aabcd',
                                     'color': '#842367'}]},
                      {'label_name': 'XZ'}]},
        {'label_name': 'bbb',
         'color': '#287605',
         'children': [{'label_name': 'ba',
                       'color': '#298345'},
                      {'label_name': 'bb',
                       'color': '#298565'}]}]
    context.dataset.update_labels(label_list=context.nested_labels, upsert=True)


@behave.when(u'I add many nested labels')
def step_impl(context):
    context.nested_labels = [
        {'label_name': 'X.Y.a',
         'color': '#220605',
         'children': [{'label_name': 'T.R.X',
                       'color': '#227305',
                       'children': [{'label_name': 'aaa',
                                     'color': '#224705',
                                     'display_label': 'display aaa',
                                     'attributes': ['Name', 'Age'],
                                     },
                                    {'label_name': 'aab',
                                     'color': '#842367'}]},
                      {'label_name': 'ab'}]},
        {'label_name': 'M.I.C',
         'color': '#287605',
         'children': [{'label_name': 'ba',
                       'color': '#298345'},
                      {'label_name': 'bb',
                       'color': '#298651'}]}
    ]
    context.dataset.add_labels(label_list=context.nested_labels)
