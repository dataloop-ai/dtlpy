import dtlpy as dl
import random
import os

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_PATH = os.path.join(TEST_DIR, 'assets')
image_path = os.path.join(ASSETS_PATH, '0000000162.jpg')
annotations_path = os.path.join(ASSETS_PATH, 'annotations_new.json')

project = dl.projects.create('project_examples_tester_{}'.format(random.randrange(1000, 100000)))
dataset = project.datasets.create('dataset_examples_tester_{}'.format(random.randrange(1000, 100000)))
item = dataset.items.upload(local_path=image_path, local_annotations_path=annotations_path)



# add labels
dl.examples.add_labels.main(project_name=project.name, dataset_name=dataset.name)

# add metadata to item
dl.examples.add_metadata_to_item.main(project_name=project.name, dataset_name=dataset.name, item_path=image_path)

# annotation convert to voc
second_project = dl.projects.create('project_examples_tester_{}'.format(random.randrange(1000, 100000)))
second_dataset = second_project.datasets.create('dataset_examples_tester_{}'.format(random.randrange(1000, 100000)))
second_item = second_dataset.items.upload(local_path=image_path)
dl.examples.copy_annotations.main(first_project_name=project.name,
                                  second_project_name=second_project.name,
                                  first_dataset_name=dataset.name,
                                  second_dataset_name=second_dataset.name,
                                  first_remote_filepath=item.filename,
                                  second_remote_filepath=second_item.filename)


# copy folder
dl.examples.copy_folder.main(first_project_name=project.name,
                                  second_project_name=second_project.name,
                                  first_dataset_name=dataset.name,
                                  second_dataset_name=second_dataset.name)

# show item and mask
dl.examples.show_item_and_mask.main(project_name=project.name,
                                  dataset_name=dataset.name,
                                  item_remote_path=item.filename)



project.delete(True, True)
second_project.delete(True, True)