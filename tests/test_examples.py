import dtlpy as dl
import time
import jwt
import random
import logging
import os
from dtlpy import examples
try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

try:
    # for local import
    from tests.env_from_git_branch import get_env_from_git_branch
except ImportError:
    # for remote import
    from env_from_git_branch import get_env_from_git_branch

logging.basicConfig(level='DEBUG')


def wait():
    time.sleep(20)


dl.setenv(get_env_from_git_branch())
# check token
payload = jwt.decode(dl.token(), algorithms=['HS256'], verify=False)
if payload['email'] not in ['oa-test-4@dataloop.ai', 'oa-test-1@dataloop.ai', 'oa-test-2@dataloop.ai', 'oa-test-3@dataloop.ai']:
    assert False, 'Cannot run test on user: "{}". only test users'.format(payload['email'])

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ASSETS_PATH = os.path.join(TEST_DIR, 'assets')
image_path = os.path.join(ASSETS_PATH, '0000000162.jpg')
annotations_path = os.path.join(ASSETS_PATH, 'annotations_new.json')

project = dl.projects.create('project_examples_tester_{}'.format(random.randrange(1000, 100000)))
wait()
dataset = project.datasets.create('dataset_examples_tester_{}'.format(random.randrange(1000, 100000)))
item = dataset.items.upload(local_path=image_path, local_annotations_path=annotations_path)

# add labels
examples.add_labels.main(project_name=project.name, dataset_name=dataset.name)

# add metadata to item
examples.add_metadata_to_item.main(project_name=project.name, dataset_name=dataset.name, item_path=image_path)

# annotation convert to voc
second_project = dl.projects.create('project_examples_tester_{}'.format(random.randrange(1000, 100000)))
wait()
second_dataset = second_project.datasets.create('dataset_examples_tester_{}'.format(random.randrange(1000, 100000)))
time.sleep(1)
second_item = second_dataset.items.upload(local_path=image_path)
examples.copy_annotations.main(first_project_name=project.name,
                               second_project_name=second_project.name,
                               first_dataset_name=dataset.name,
                               second_dataset_name=second_dataset.name,
                               first_remote_filepath=item.filename,
                               second_remote_filepath=second_item.filename)

# copy folder
examples.copy_folder.main(first_project_name=project.name,
                          second_project_name=second_project.name,
                          first_dataset_name=dataset.name,
                          second_dataset_name=second_dataset.name)

# show item and mask
examples.show_item_and_mask.main(project_name=project.name,
                                 dataset_name=dataset.name,
                                 item_remote_path=item.filename)

# show item and mask
examples.upload_items_with_modalities.main(project_name=project.name,
                                           dataset_name=dataset.name)
project.delete(True, True)
second_project.delete(True, True)
