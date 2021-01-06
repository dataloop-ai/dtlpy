import behave


@behave.given(u'I set dataset recipe and ontology to context')
def step_impl(context):
    context.recipe = context.dataset.recipes.list()[0]
    context.ontology = context.dataset.ontologies.list()[0]


@behave.when(u'I add new label "{label_name}" to dataset {dataset_index}')
def step_impl(context, label_name, dataset_index):
    context.datasets[int(dataset_index) - 1].add_label(label_name=label_name)


@behave.when(u'I clone recipe from  dataset {dataset1_index} to dataset {dataset2_index} with ontology')
def step_impl(context, dataset1_index, dataset2_index):
    context.recipe_clone = context.datasets[int(dataset1_index) - 1].recipes.list()[0].clone()
    context.datasets[int(dataset2_index) - 1].switch_recipe(recipe=context.recipe_clone)


@behave.when(u'I clone recipe from  dataset {dataset1_index} to dataset {dataset2_index} without ontology')
def step_impl(context, dataset1_index, dataset2_index):
    context.recipe_clone = context.datasets[int(dataset1_index) - 1].recipes.list()[0].clone(shallow=True)
    context.datasets[int(dataset2_index) - 1].switch_recipe(recipe=context.recipe_clone)


@behave.then(u'I verify that Dataset {dataset_index} has {labels_len} labels')
def step_impl(context, dataset_index, labels_len):
    context.datasets[int(dataset_index) - 1] = context.dl.datasets.get(
        dataset_id=context.datasets[int(dataset_index) - 1].id)

    assert len(context.datasets[int(dataset_index) - 1].labels) == int(labels_len)

