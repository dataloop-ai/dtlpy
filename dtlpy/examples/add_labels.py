

def main(project_name, dataset_name):
    # Imports the SDK package
    import dtlpy as dl

    # prep
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)

    ########################################
    # Copy dataset labels to a new dataset #
    ########################################
    new_dataset = project.datasets.create(dataset_name='new_dataset_with_labels',
                                          labels=dataset.labels)

    ##########################################
    # Copy dataset ontology to a new dataset #
    ##########################################
    new_dataset = project.datasets.create(dataset_name='new_dataset_with_ontology',
                                          ontology_ids=dataset.ontology_ids)

    ##############################################
    # Copy dataset labels to an existing dataset #
    ##############################################
    new_dataset = project.datasets.create(dataset_name='new_dataset_without_labels')

    # Get from a list or recipes
    recipe = new_dataset.recipes.list()[0]
    # Or get recipe by id
    # recipe = new_dataset.recipes.get(recipe_id='recipe_id')

    # Get from the list of ontologies
    ontology = recipe.ontologies.list()[0]
    # Or get ontology by id
    # ontology = recipe.ontologies.get(ontology='ontology_id')

    # Add the labels to the dataset
    ontology.add_labels(label_list=dataset.labels)

    ################################################
    # Copy dataset ontology to an existing dataset #
    ################################################
    new_dataset = project.datasets.create(dataset_name='new_dataset_without_ontology')
    # Copy from a different dataset
    new_dataset.ontology_ids = dataset.ontology_ids
    # Update the new dataset
    new_dataset.update()

    ##########################
    # update existing recipe #
    ##########################
    # Get recipe from list
    recipe = dataset.recipes.list()[0]
    # Or get specific recipe:
    # recipe = dataset.recipes.get(recipe_id='id')

    # Get ontology from list
    ontology = recipe.ontologies.list()[0]
    # Or get specific ontology:
    # ontology = recipe.ontologies.get(ontology_id='id')

    # Add one label
    ontology.add_label(label_name='Lion', color=(35, 234, 123))

    # Add a list of labels
    labels = [{'tag': 'Dog', 'color': (1, 1, 1)}, {'tag': 'Cat', 'color': (34, 56, 7)},
              {'tag': 'Bird', 'color': (100, 14, 150)}]
    ontology.add_labels(label_list=labels)

    # After adding - update ontology
    ontology.update()

    #####################
    # Create new recipe #
    #####################
    # Label list
    labels = [{'tag': 'Dog', 'color': (1, 1, 1)}, {'tag': 'Cat', 'color': (34, 56, 7)},
              {'tag': 'Bird', 'color': (100, 14, 150)}]
    dataset.recipes.create(recipe_name='My Recipe', labels=labels)

    # Update the dataset
    dataset = dataset.update()

