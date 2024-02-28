import time

from behave import fixture
import os
import json
import datetime
import dtlpy as dl
from operator import attrgetter


@fixture
def compare_dir_recursive(dir_a, dir_b):
    equal = True

    dir_a_items = [item for item in os.listdir(dir_a) if item != 'folder_keeper']
    dir_b_items = [item for item in os.listdir(dir_b) if item != 'folder_keeper']
    if '__pycache__' in dir_a_items:
        dir_a_items.remove('__pycache__')
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


def get_value(params, context):
    key = params[0]
    val = params[1]
    if val == 'None':
        val = None
    elif val == 'auto':
        if key == 'due_date':
            val = datetime.datetime.today().timestamp() + 24 * 60 * 60
        elif key == 'assignee_ids':
            val = ['annotator1@dataloop.ai', 'annotator2@dataloop.ai']
        elif key == 'workload':
            val = context.dl.Workload.generate(['annotator1@dataloop.ai', 'annotator2@dataloop.ai'])
        elif key == 'dataset':
            val = context.dataset
        elif key == 'task_owner':
            val = 'owner@dataloop.ai'
        elif key == 'recipe_id':
            val = context.dataset.get_recipe_ids()[0]
        elif key == 'project_id':
            val = context.project.id
        elif key == 'task_id':
            val = context.task.id
        elif key == 'batch_size':
            val = 5
        elif key == 'max_batch_workload':
            val = 7
        elif key == 'allowed_assignees':
            val = ['annotator1@dataloop.ai', 'annotator2@dataloop.ai']
        elif key == 'consensus_task_type':
            val = 'consensus'
        elif key == 'consensus_percentage':
            val = 100
        elif key == 'consensus_assignees':
            val = 2
        elif key == 'scoring':
            val = False

    if key == 'filters' and val is not None and not isinstance(val, dict):
        filters = context.dl.Filters()
        filters.custom_filter = json.loads(val)
        val = filters
    elif key == 'items' and val is not None:
        if len(context.items_in_dataset) >= int(val):
            items = list()
            for _ in range(int(val)):
                items.append(context.items_in_dataset.pop())
            val = items
        else:
            raise Exception('Not enough items in dataset')
    elif key == 'metadata' and val is not None:
        val = json.loads(val)
    elif key == 'due_date':
        if val == 'next_week':
            val = datetime.datetime.today().timestamp() + (7 * 24 * 60 * 60)
    elif key == 'project_id':
        if val == 'second':
            val = context.second_project.id
    elif key == 'recipe_id':
        if val == 'second':
            assert hasattr(context, "second_dataset"), "TEST FAILED: Test should have second_dataset"
            val = context.second_dataset.get_recipe_ids()[0]
    elif key == 'assignee_ids':
        if val and "[" in val:
            val = eval(val)
    elif key == 'available_actions':
        action_status = val.split()
        available_actions_list = list()
        for action in action_status:
            available_actions_list.append(context.dl.ItemAction(action=action, display_name=action, color='#2ef16c'))
        val = available_actions_list
    elif key == 'batch_size':
        val = int(val)
    elif key == 'max_batch_workload':
        val = int(val)
    elif key == 'consensus_task_type':
        val = str(val)
    elif key == 'consensus_percentage':
        val = int(val)
    elif key == 'consensus_assignees':
        val = int(val)
    elif key == 'scoring':
        val = eval(val)

    return val


def get_assignment_value(params, context):
    key = params[0]
    val = params[1]
    if val == 'None':
        val = None
    elif val == 'auto':
        if key == 'assignee_id':
            val = 'annotator2@dataloop.ai'
        elif key == 'dataset':
            val = context.dataset
        elif key == 'project_id':
            val = context.project.id
        elif key == 'task_id':
            val = context.task.id

    if key == 'filters' and val is not None and not isinstance(val, dict):
        filters = context.dl.Filters()
        filters.custom_filter = json.loads(val)
        val = filters
    elif key == 'items' and val is not None:
        if len(context.items_in_dataset) >= int(val):
            items = list()
            for _ in range(int(val)):
                items.append(context.items_in_dataset.pop())
            val = items
        else:
            raise Exception('Not enough items in dataset')
    elif key == 'metadata' and val is not None:
        val = json.loads(val)
    elif key == 'project_id':
        if val == 'second':
            val = context.second_project.id

    return val


def get_package_io(params, context):
    val = list()
    for key in params:
        if key == 'item':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_ITEM, name=key))
        elif key == 'annotation':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_ANNOTATION, name=key))
        elif key == 'dataset':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_DATASET, name=key))
        elif key == 'task':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_TASK, name=key))
        elif key == 'assignment':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_ASSIGNMENT, name=key))
        elif key == 'itemWithDescription':
            val.append(context.dl.FunctionIO(type=context.dl.PACKAGE_INPUT_TYPE_ITEM, name=key, description='item'))

    return val


def access_nested_dictionary_key(dict_input, keys):
    # using for loop to access nested dictionary key safely
    val = dict_input
    for key in keys:
        if key in val:
            if isinstance(val[key], list):
                if val[key]:
                    val = val[key][0]
                else:
                    val = None
                    break
            else:
                val = val[key]
        else:
            val = None
            break
    return val


def update_dtlpy_version(json_obj):
    """
    For DPK
    Check if component attribute from the list 'component_attributes' is contained the keys: 'versions' / 'runtime'.
    if True - Check if the obj keys value is 'dtlpy_version' - if True - update to current sdk version
    if False - Skip to next component attribute
    Return: json_obj
    """
    component_attributes = ["services", "computeConfigs", "modules"]
    for component_att in component_attributes:
        val = access_nested_dictionary_key(json_obj, ['components', component_att, 'versions', 'dtlpy'])
        if val:
            for obj in json_obj['components'][component_att]:
                if obj['versions']['dtlpy'] == "dtlpy_version":
                    obj['versions'].update({"dtlpy": dl.__version__})

        val = access_nested_dictionary_key(json_obj, ['components', component_att, 'runtime', 'runnerImage'])
        if val:
            for obj in json_obj['components'][component_att]:
                if "dtlpy_version" in obj['runtime']["runnerImage"]:
                    obj['runtime'].update({"runnerImage": f"dataloop_runner-cpu/main:{dl.__version__}.latest"})

    return json_obj


def gen_request(context, method=None, req=None, num_try=None, interval=None, expected_response=None):
    if req.get('path', None) and ".id" in req.get('path'):
        replace_field = req.get('path').split("/")[2]
        req['path'] = req['path'].replace(replace_field, attrgetter(replace_field)(context))
    for i in range(num_try):
        success, response = dl.client_api.gen_request(req_type=method,
                                                      path=req.get('path', None),
                                                      data=req.get('data', None),
                                                      json_req=req.get('json_req', None))
        if success:
            if expected_response and expected_response in response.text:
                break
        dl.logger.warning("Number of tries {}".format(i + 1))
        time.sleep(interval)

    if not success:
        raise dl.exceptions.PlatformException(response)
    return response
