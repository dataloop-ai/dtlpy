from behave import fixture
import os
import json


@fixture
def compare_dir_recursive(dir_a, dir_b):
    equal = True

    dir_a_items = [item for item in os.listdir(dir_a) if item != 'folder_keeper']
    dir_b_items = [item for item in os.listdir(dir_b) if item != 'folder_keeper']
    if len(dir_a_items) != len(dir_b_items):
        return False

    for item in dir_a_items:
        if os.path.isdir(os.path.join(dir_a, item)):
            equal = compare_dir_recursive(os.path.join(dir_a, item), os.path.join(dir_b, item))
        else:
            if item.lower().endswith('.json'):
                with open(os.path.join(dir_a, item), 'r') as f:
                    data_a = json.load(f)
                with open(os.path.join(dir_a, item), 'w') as f:
                    json.dump(data_a, f, indent=2, sort_keys=True)
                with open(os.path.join(dir_b, item), 'r') as f:
                    data_b = json.load(f)
                with open(os.path.join(dir_b, item), 'w') as f:
                    json.dump(data_b, f, indent=2, sort_keys=True)
            equal = compare_files(os.path.join(dir_a, item), os.path.join(dir_b, item))
        if not equal:
            return False

    return equal


def compare_files(fpath1, fpath2):
    with open(fpath1, 'r') as file1:
        with open(fpath2, 'r') as file2:
            same = set(file1).difference(file2)

    if same:
        return False
    else:
        return True

