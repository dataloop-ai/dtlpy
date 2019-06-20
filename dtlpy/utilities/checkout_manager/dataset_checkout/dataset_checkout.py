import os
import json
from dtlpy.utilities.state_manager import get_state, set_state

def load_json_from_file(filepath):
    file_as_str = open(filepath, 'r').read()
    return json.loads(file_as_str)

def save_json_to_file(filepath, target_json):
    file = open(filepath, 'w+')
    file.write(json.dumps(target_json))

def get_dataset_by_identifier(datasets, identifier):
    datasets_by_name = [dataset for dataset in datasets if dataset.name == identifier]
    if (len(datasets_by_name) == 1):
        return datasets_by_name[0]
    elif (len(datasets_by_name) > 1):
        print('Multiple datasets with this name exist')
        exit(-1)

    datasets_by_partial_id = [dataset for dataset in datasets if dataset.id.startswith(identifier)]
    if (len(datasets_by_partial_id) == 1):
        return datasets_by_partial_id[0]
    elif (len(datasets_by_partial_id) > 1):
        print("Multiple datasets whose id begins with {} exist".format(identifier))
        exit(-1)

    print("Dataset not found")
    exit(-1)

def checkout_dataset(dlp, dataset_identifier):
    state_json = get_state()

    if ("project" not in state_json):
        print("Please checkout a valid project before trying to checkout a dataset")
        exit(-1)

    project = dlp.projects.get(project_id=state_json['project'])
    datasets = project.datasets.list()
    dataset = get_dataset_by_identifier(datasets, dataset_identifier)

    if ('dataset' in state_json and state_json['dataset'] == dataset.id):
        print('Already checked out to this dataset')
        exit(0)

    state_json['dataset'] = dataset.id

    set_state(state_json)

    print('Checked out to dataset {}'.format(dataset.name))