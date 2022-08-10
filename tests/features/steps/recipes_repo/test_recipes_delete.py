import os

import behave


@behave.given(u'Dataset has Recipes')
def step_impl(context):
    context.recipe = context.dataset.recipes.list()[0]
    context.second_recipe = context.dataset.recipes.create(recipe_name="second_recipe")


@behave.then(u'Add instruction "{path}" to Recipe')
def step_impl(context, path):
    try:
        annotation_instruction_file = os.path.join(os.environ['DATALOOP_TEST_ASSETS'], path)
        context.recipe.add_instruction(annotation_instruction_file=annotation_instruction_file)
    except Exception as e:
        context.error = e


@behave.then(u'instruction are exist')
def step_impl(context):
    recipe = context.dataset.recipes.get(context.recipe.id)
    assert 'instructionDocument' in recipe.metadata['system']


@behave.when(u'I delete recipe')
def step_impl(context):
    context.recipe.delete(force=True)


@behave.then(u'Dataset has no recipes')
def step_impl(context):
    recipe_list = context.dataset.recipes.list()
    try:
        context.dataset.recipes.get(context.recipe.id)
        assert False
    except Exception as e:
        assert True
    assert context.dataset.recipes.get(context.second_recipe.id).title == context.second_recipe.title
