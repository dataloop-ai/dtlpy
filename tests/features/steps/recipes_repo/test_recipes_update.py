import behave


@behave.when(u'I update recipe')
def step_impl(context):
    context.recipe = context.dataset.recipes.list()[0]
    context.recipe.title = "new_name"
    context.recipe.update(system_metadata=True)


@behave.then(u'Recipe in host equals recipe eddited')
def step_impl(context):
    context.recipe_get = context.dataset.recipes.get(recipe_id=context.recipe.id)
    assert context.recipe_get.title == context.recipe.title
