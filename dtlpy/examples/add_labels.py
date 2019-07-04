def main():
    import dtlpy as dl

    ##########################
    # update existing recipe #
    ##########################

    project = dl.projects.create(project_name='MyProject')
    dataset = project.datasets.create(dataset_name='MyDataset')

    # get recipe
    recipe = dataset.recipes.list()[0]
    # or get specific recipe
    recipe = dataset.recipes.get(recipe_id='id')

    # get ontology
    ontology = recipe.ontologies.list()[0]
    # or get specific ontology
    ontology = recipe.ontologies.get(ontology_id='id')

    # add one label
    ontology.add_label(label_name='Dog', colore=(34, 54, 234))

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
    labels = [{'label': 'Dog', 'color': (1, 1, 1)}, {'label': 'Cat', 'color': (34, 56, 7)},
              {'label': 'Bird', 'color': (100, 14, 150)}]
    dataset.recipes.create(recipe_name='My Recipe', labels=labels)

    # reclaim the dataset
    dataset = dataset.update()
