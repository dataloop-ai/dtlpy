def main(project_name, dataset_name):
    # Imports the SDK package
    import dtlpy as dl

    """
    Label dictionary format:
    
    {
        'label_name': 'dog',
        'displayLabel': 'Dog',
        'attributes': ['list of attributes'],
        'color': (34, 6, 231),
        'children': ['list of label dictionaries']
    }

    """

    # prep
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)

    ###############################
    # add label to dataset entity #
    ###############################
    dataset.add_label(label_name='Horse', color=(2, 43, 123))

    #############################
    # add label with sub-labels #
    #############################
    dataset.add_label(label_name='CEO', color=(2, 43, 123),
                      children=[{'label_name': 'Manager',
                                 'children': [{'label_name': 'Employee'}]}])

    ################################
    # add labels to dataset entity #
    ################################
    labels = [
        {'label_name': 'Dog',
         'color': (34, 6, 231),
         'children': [{'label_name': 'Puppy',
                       'color': (24, 16, 130)}]},
        {'label_name': 'Cat',
         'color': (24, 25, 31),
         'children': [{'label_name': 'Kitten',
                       'color': (124, 116, 140)}]}
    ]
    dataset.add_labels(label_list=labels)

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
    ontology.update()

    #########################################################
    # Copy dataset ontology to an existing dataset's recipe #
    #########################################################
    new_dataset = project.datasets.create(dataset_name='new_dataset_without_ontology')
    # get recipe
    new_dataset_recipe = new_dataset.recipes.list()[0]
    # Copy from a different dataset
    new_dataset_recipe.ontologyIds = dataset.ontology_ids
    # Update the new dataset
    new_dataset_recipe.update()

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
    labels = [{'label_name': 'Shark', 'color': (1, 1, 1)}, {'label_name': 'Whale', 'color': (34, 56, 7)},
              {'label_name': 'Dolphin', 'color': (100, 14, 150)}]
    ontology.add_labels(label_list=labels)

    # After adding - update ontology
    ontology.update()

    #####################
    # Create new recipe #
    #####################
    # Label list
    labels = [{'tag': 'Donkey', 'color': (1, 1, 1)}, {'tag': 'Mammoth', 'color': (34, 56, 7)},
              {'tag': 'Bird', 'color': (100, 14, 150)}]
    recipe = dataset.recipes.create(recipe_name='My Recipe', labels=labels)
