import behave
import dtlpy as dl
import os


@behave.when(u'Get Recipe from List')
def step_impl(context):
    context.recipe = context.dataset.recipes.list()[0]

@behave.then(u'Get Recipe by ID')
def step_impl(context):
    context.recipe = context.dataset.recipes.get(recipe_id=context.recipe.id)


@behave.then(u'Recipe Clone')
def step_impl(context):
    context.recipe = context.dataset.recipes.get(recipe_id=context.recipe.id)
    context.recipe2 = context.recipe.clone(shallow=False)  # dataset or dataset id, if the function is given dataset or dataset id parameters, the recipe will be linked to the given dataset

@behave.then(u'Delete Recipe')
def step_impl(context):
    context.dataset.recipes.get(recipe_id=context.recipe.id).delete()

@behave.then(u'Recipe Switch')
def step_impl(context):
    context.dataset.switch_recipe(recipe=context.recipe2)  # or use recipe Id


@behave.when(u'View Datasets Labels')
def step_impl(context):
    # as objects
    context.labels = context.dataset.labels
    # as instance map
    context.labels = context.dataset.instance_map


@behave.then(u'Add one Label "{label_name}"')
def step_impl(context,label_name):
    # Add one label
    context.dataset.add_label(label_name=label_name)


@behave.then(u'Add Multiple Labels "{label_1}", "{label_2}", "{label_3}"')
def step_impl(context,label_1,label_2,label_3):
    # Add multiple
    context.dataset.add_labels(label_list=[label_1,label_2,label_3])


@behave.then(u'Add a single label "{label_name}" with a specific color ({num1:d}, {num2:d}, {num3:d})')
def step_impl(context,label_name,num1,num2,num3):
    # Add single label with specific color
    context.dataset.add_label(label_name=label_name, color=(num1,num2,num3))


@behave.then(u'Add a single label "{label_name}" with a specific color ({num1:d}, {num2:d}, {num3:d}) and attributes ["{att1}", "{att2}"]')
def step_impl(context,label_name,num1,num2,num3,att1,att2):
    # Add single label with specific color and attributes
    context.dataset.add_label(label_name=label_name, color=(num1,num2,num3), attributes=[att1,att2])


@behave.then(u'Add a single label "{label_name}" with an image "{image}" and attributes ["{att1}","{att2}"]')
def step_impl(context,label_name,image,att1,att2):
    # Add single label with an icon and attributes
    item_local_path = os.path.join(os.environ["DATALOOP_TEST_ASSETS"], image)
    context.dataset.add_label(label_name=label_name, icon_path=item_local_path, attributes=[att1, att2])


@behave.then(u'Add Labels using Label object')
def step_impl(context):
    # Create Labels list using Label object
    context.labels = [
        dl.Label(tag='Donkey', color=(1, 1, 1)),
        dl.Label(tag='Mammoth', color=(34, 56, 7)),
        dl.Label(tag='Bird', color=(100, 14, 150))
    ]
    # Add Labels to Dataset
    context.dataset.add_labels(label_list=context.labels)
    # or you can also create a recipe from the label list
    context.temp_recipe = context.dataset.recipes.list()[0]
    context.recipe = context.dataset.recipes.create(recipe_name=context.temp_recipe.title, labels=context.labels)


@behave.then(u'Add a Label with children and attributes')
def step_impl(context):
    # Add label with children and attributes
    label = [dl.Label(
        tag='Fish',
        attributes=['carnivore', 'herbivores'],
        color=(34, 6, 231),
        children=[
            dl.Label(
                tag='Shark',
                color=(34, 6, 231),
                attributes=['baby', 'old'],
            ),
            dl.Label(
                tag='Salmon',
                color=(34, 6, 231),
                attributes=['pink', 'norwegian'],
            )
        ]
    )]
    context.dataset.add_labels(label_list=label)


@behave.then(u'Add multiple Labels with children and attributes "{recipe_name}"')
def step_impl(context,recipe_name):
    # Add multiple labels with children and attributes
    # Create Labels list
    labels = [dl.Label(
        tag='Fish',
        attributes=['carnivore', 'herbivores'],
        color=(34, 6, 231),
        children=[
            dl.Label(
                tag='Shark',
                color=(34, 6, 231),
                attributes=['baby', 'old'],
            ),
            dl.Label(
                tag='Salmon',
                color=(34, 6, 231),
                attributes=['pink', 'norwegian'],
            )
        ]
    ),
        dl.Label(
            tag='Meat',
            attributes=['carnivore', 'herbivores'],
            color=(34, 6, 231),
            children=[
                dl.Label(
                    tag='Beef',
                    color=(34, 6, 231),
                    attributes=['Rib', 'Brisket'],
                ),
                dl.Label(
                    tag='Lamb',
                    color=(34, 6, 231),
                    attributes=['baby', 'old'],
                )
            ]
        )
    ]
    # Add Labels to Dataset
    context.dataset.add_labels(label_list=labels)
    # or you can also create a recipe from the label list
    context.recipe = context.dataset.recipes.create(recipe_name=recipe_name, labels=labels)

@behave.when(u'Option A')
def step_impl(context):
    # Option A
    # add father label
    context.labels = context.dataset.add_label(label_name="animal", color=(123, 134, 64), attributes=["Farm", "Home"])
    # add child label
    context.labels = context.dataset.add_label(label_name="animal.Dog", color=(45, 34, 164), attributes=["Big", "Small"])
    # add grandchild label
    context.labels = context.dataset.add_label(label_name="animal.Dog.poodle", attributes=["Black", "White"])

@behave.when(u'Option B')
def step_impl(context):
    # Option B:only if you dont have attributes
    # parent and grandparent (animal and dog) will be generate automaticly
    context.labels = context.dataset.add_label(label_name="animal.Dog.poodle")

@behave.when(u'Option C')
def step_impl(context):
    # Option C: with the Big Dict
    nested_labels = [
        {'label_name': 'animal.Dog',
         'color': '#220605',
         'children': [{'label_name': 'poodle',
                       'color': '#298345'},
                      {'label_name': 'labrador',
                       'color': '#298651'}]},
        {'label_name': 'animal.cat',
         'color': '#287605',
         'children': [{'label_name': 'Persian',
                       'color': '#298345'},
                      {'label_name': 'Balinese',
                       'color': '#298651'}]}
    ]
    # Add Labels to the dataset:
    context.labels = context.dataset.add_labels(label_list=nested_labels)

@behave.then(u'Create a Recipe From from a Label list "{recipe_name}"')
def step_impl(context,recipe_name):
    # dont forget to create labels list using different scripts
    context.recipe = context.dataset.recipes.create(recipe_name=recipe_name, labels=context.labels)

@behave.then(u'Update Label Features')
def step_impl(context):
    context.dataset.delete_labels(label_names=['Cat', 'Dog'])

@behave.then(u'Delete Labels by Dataset')
def step_impl(context):
    context.dataset.update_label(label_name='Cat', color="#fcba03", upsert=True)  # update label, if not exist add it
    context.dataset.update_label(label_name='Cat', color="#000080")  # update existing label , if not exist fails
