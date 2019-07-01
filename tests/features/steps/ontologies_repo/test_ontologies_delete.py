import behave


@behave.when(u'I delete ontology by id')
def step_impl(context):
    context.recipe.ontologies.delete(ontology_id=context.ontology.id)


@behave.then(u'Ontology does not exist in dataset')
def step_impl(context):
    try:
        context.recipe.ontologies.get(ontology_id=context.ontology.id)
        assert False
    except Exception as e:
        assert "InternalServerError" in str(type(e))


@behave.when(u'I try to delete ontology by "{some_id}"')
def step_impl(context, some_id):
    try:
        context.recipe.ontologies.delete(ontology_id=some_id)
        context.error = None
    except Exception as e:
        context.error = e
