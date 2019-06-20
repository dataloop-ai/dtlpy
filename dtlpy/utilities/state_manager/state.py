import os
import json

def load_json_from_file(filepath):
    file_as_str = open(filepath, 'r').read()
    return json.loads(file_as_str)

def save_json_to_file(filepath, target_json):
    file = open(filepath, 'w+')
    file.write(json.dumps(target_json))

def get_state():
    dataloop_dir = os.path.join(os.getcwd(), '.dataloop')
    state_json_path = os.path.join(os.getcwd(), '.dataloop', 'state.json')
    global_json_path = os.path.join(os.path.expanduser('~'), '.dataloop', 'state.json')

    if (os.path.exists(dataloop_dir)):
        return load_json_from_file(state_json_path)
    else:
        return load_json_from_file((global_json_path))

def set_state(state):
    dataloop_dir = os.path.join(os.getcwd(), '.dataloop')
    state_json_path = os.path.join(os.getcwd(), '.dataloop', 'state.json')
    global_json_path = os.path.join(os.path.expanduser('~'), '.dataloop', 'state.json')

    if (os.path.exists(dataloop_dir)):
        save_json_to_file(state_json_path, state)
    else:
        save_json_to_file(global_json_path, state)