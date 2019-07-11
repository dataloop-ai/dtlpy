import os
import json
import dtlpy
from dtlpy.utilities.plugin_bootstraping.util import get_state_json


class PluginInvoker:
    def __init__(self, input_path):
        self.input_path = os.path.abspath(input_path)

    def invoke_plugin(self):
        file_as_str = open(self.input_path, 'r').read()
        file_as_obj = json.loads(file_as_str)
        inputs = file_as_obj['inputs']
        parsed_inputs = {}

        assert isinstance(inputs, list)
        for input in inputs:
            parsed_inputs[input['name']] = input['value']

        state_json = get_state_json()
        project_id = state_json['project']
        task_name = state_json['package']

        project = dtlpy.projects.get(project_id=project_id)
        task = project.tasks.get(task_name=task_name)
        session = task.sessions.create(parsed_inputs, True)

        return session.output