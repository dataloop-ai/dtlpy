import behave


@behave.given(u'Dataset has ontology')
def step_impl(context):
    context.recipe = context.dataset.recipes.get(recipe_id=context.dataset.metadata['system']['recipes'][0])
    context.ontology = context.recipe.ontologies.get(ontology_id=context.recipe.ontologyIds[0])


@behave.when(u'I get a ontology by id')
def step_impl(context):
    context.ontology = context.recipe.ontologies.get(ontology_id=context.ontology.id)


@behave.then(u'I get an Ontology object')
def step_impl(context):
    assert type(context.ontology) == context.dl.Ontology


@behave.when(u'I try to get Ontology by "{some_id}"')
def step_impl(context, some_id):
    try:
        context.ontology = context.recipe.ontologies.get(ontology_id=some_id)
        context.error = None
    except Exception as e:
        context.error = e
