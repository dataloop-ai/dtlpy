from enum import Enum
import json
import os

def load_json_from_file(filepath):
    file_as_str = open(filepath, 'r').read()
    return json.loads(file_as_str)

def get_state_json():
    return load_json_from_file(os.path.join(os.getcwd(), '.dataloop', 'state.json'))

def get_plugin_json():
    return load_json_from_file(os.path.join(os.getcwd(), 'plugin.json'))
