import os
import sys
import importlib.util
import dtlpy
from dtlpy.utilities.plugin_bootstraping.util import load_json_from_file
from dtlpy.utilities.checkout_manager.state_manager import get_state

class PackageRunner:
    def __init__(self):
        self.cwd = os.getcwd()
        self.plugin_json = load_json_from_file(os.path.join(self.cwd, 'plugin.json'))
        self.mock_json = load_json_from_file(os.path.join(self.cwd, 'mock.json'))
        self.state_json = get_state()

    def run_local_project(self):
        cwd = os.getcwd()
        dataloop_path = os.path.join(cwd, '.dataloop')

        if not os.path.exists(dataloop_path):
            raise Exception('Package not found')

        PackageRunner.validate_mock(self.plugin_json, self.mock_json)

        run_function = PackageRunner.get_mainpy_run_function()

        try:
            project_id = self.state_json['project']
        except:
            raise Exception("Please checkout to a project")

        try:
            project = dtlpy.projects.get(project_id=project_id)
        except:
            raise Exception("Project not found")

        plugin_inputs = self.plugin_json['inputs']
        kwargs = {}
        for input in plugin_inputs:
            kwargs[input['name']] = self.get_field(input['name'], input['type'], project, self.mock_json)

        run_function(**kwargs)

    def get_dataset(self, project, resource_id):
        if ('dataset_id' in resource_id):
            dataset_id = resource_id['dataset_id']
        else:
            dataset_id = self.state_json['dataset']

        return project.datasets.get(dataset_id = dataset_id)

    def get_item(self, project, resource_id):
        dataset = self.get_dataset(project, resource_id)
        return dataset.items.get(item_id=resource_id['item_id'])

    def get_annotation(self, project, resource_id):
        item = self.get_dataset(project, resource_id)
        return item.annotations.get(annotation_id = resource_id['annotation_id'])

    def get_field(self, field_name, field_type, project, mock_json):
        mock_inputs = mock_json['inputs']
        filtered_mock_inputs = list(filter(lambda input: input['name'] == field_name, mock_inputs))

        if (len(filtered_mock_inputs) == 0):
            raise Exception('No entry for field {} found in mock'.format(field_name))
        if (len(filtered_mock_inputs) > 1):
            raise Exception('Duplicate entries for field {} found in mock'.format(field_name))

        mock_input = filtered_mock_inputs[0]
        resource_id = mock_input['value']

        if (field_type == 'Dataset'):
            return self.get_dataset(project, resource_id)

        elif (field_type == 'Item'):
            return self.get_item(project, resource_id)

        elif (field_type == 'Annotation'):
            return self.get_annotation(project, resource_id)

        elif (field_type == 'Json'):
            return mock_input['value']

        else:
            raise Exception('Unknown resource type for field {}'.format(field_name))

    @staticmethod
    def validate_mock(plugin_json, mock_json):
        def on_error():
            raise Exception('Parameters in mock, not fit the parameters in plugin.json')

        if(len(plugin_json['inputs']) != len(mock_json['inputs'])):
            on_error()


    @staticmethod
    def get_mainpy_run_function():
        cwd = os.getcwd()
        sys.path.insert(0, cwd)
        import src
        return src.run





