

def main(project_name, dataset_name):
    ###########
    # imports #
    ###########
    import dtlpy as dl

    ########
    # prep #
    ########
    project = dl.projects.get(project_name=project_name)
    dataset = project.datasets.get(dataset_name=dataset_name)

    ##########################
    # update existing recipe #
    ##########################

    # get recipe
    recipe = dataset.recipes.list()[0]
    # or get specific recipe:
    # recipe = dataset.recipes.get(recipe_id='id')

    # get ontology
    ontology = recipe.ontologies.list()[0]
    # or get specific ontology:
    # ontology = recipe.ontologies.get(ontology_id='id')

    # add one label
    ontology.add_label(label_name='Lion', color=(35, 234, 123))

    # add a list of labels
    labels = [{'tag': 'Dog', 'color': (1, 1, 1)}, {'tag': 'Cat', 'color': (34, 56, 7)},
              {'tag': 'Bird', 'color': (100, 14, 150)}]
    ontology.add_labels(label_list=labels)

    # after adding - update ontology
    ontology.update()

    #####################
    # create new recipe #
    #####################

    # label list
    labels = [{'tag': 'Dog', 'color': (1, 1, 1)}, {'tag': 'Cat', 'color': (34, 56, 7)},
              {'tag': 'Bird', 'color': (100, 14, 150)}]
    dataset.recipes.create(recipe_name='My Recipe', labels=labels)

    # reclaim the dataset
    dataset = dataset.update()

