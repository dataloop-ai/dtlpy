import behave


@behave.given(u'Dataset has Recipes')
def step_impl(context):
    context.recipe = context.dataset.recipes.list()[0]
    context.second_recipe = context.dataset.recipes.create(recipe_name="second_recipe")


@behave.when(u'I delete recipe')
def step_impl(context):
    context.recipe.delete()


@behave.then(u'Dataset has no recipes')
def step_impl(context):
    recipe_list = context.dataset.recipes.list()
    try:
        context.dataset.recipes.get(context.recipe.id)
        assert False
    except Exception as e:
        assert True
    assert context.dataset.recipes.get(context.second_recipe.id).title == context.second_recipe.title
