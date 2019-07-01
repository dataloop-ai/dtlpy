import behave, os, json

@behave.when(u'I update ontology entity with labels from file "{file_path}"')
def step_impl(context, file_path):
    file_path = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], file_path)
    with open(file_path) as f:
        context.labels = json.load(f)
    context.ontology.add_labels(context.labels)
    context.ontology.update()

@behave.then(u'Dataset ontology in host has labels uploaded from "{file_path}')
def step_impl(context, file_path):
    context.ontology = context.recipe.ontologies.get(ontology_id=context.ontology.id)
    assert len(context.ontology.labels) == len(context.labels)
    for label in context.ontology.labels:
        assert label.to_root() in context.labels


@behave.when(u'I update ontology entity system metadata')
def step_impl(context):
    context.ontology.metadata['system']['something'] = 'value'
    context.ontology.update(system_metadata=True)

@behave.when(u'I delete ontology entity')
def step_impl(context):
    context.ontology.delete()

@behave.when(u'I add label to ontology')
def step_impl(context):
    context.ontology.add_label(label_name='label', color='#DC143C', children=None, attributes='attr1')
    context.label = {'name':'label', 'color':'#DC143C', 'attributes':['attr1'], 'display_label':'Label'}

@behave.when(u'I update ontology entity')
def step_impl(context):
    context.ontology.update()

@behave.then(u'Ontology in host has label')
def step_impl(context):
    context.ontology = context.recipe.ontologies.get(ontology_id=context.ontology.id)
    label = context.ontology.labels[0]
    assert label.tag == context.label['name']
    assert label.color == context.label['color']
    assert label.attributes == context.label['attributes']
    assert label.display_label == context.label['display_label']