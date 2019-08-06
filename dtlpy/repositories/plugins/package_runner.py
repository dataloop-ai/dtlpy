import os
import sys
import json
from ... import repositories, PlatformException, services


class PackageRunner:
    """
    Package Runner Class
    """
    def __init__(self, client_api):
        self.client_api = client_api
        self.cwd = os.getcwd()
        with open(os.path.join(self.cwd, 'mock.json'), 'r') as f:
            self.mock_json = json.load(f)

    @staticmethod
    def validate_mock(plugin_json, mock_json):
        """
        Validate mock
        :param plugin_json:
        :param mock_json:
        :return:
        """
        if len(plugin_json['inputs']) != len(mock_json['inputs']):
            raise PlatformException('400', 'Parameters in mock, not fit the parameters in plugin.json')
        pass

    @staticmethod
    def get_mainpy_run_function():
        """
        Get mainpy run function
        :return:
        """
        cwd = os.getcwd()
        sys.path.insert(0, cwd)
        import src
        return src.run

    def run_local_project(self):
        assert isinstance(self.client_api, services.ApiClient)
        self.validate_mock(self.client_api.plugin_io.read_json(), self.mock_json)
        run_function = self.get_mainpy_run_function()
        try:
            # project_id = self.client_api.state_io.get('project')
            project_id = self.client_api.state_io.get('project')
        except Exception:
            raise PlatformException('400', "Please checkout to a project")

        try:
            projects = repositories.Projects(client_api=self.client_api)
            project = projects.get(project_id=project_id)
        except Exception:
            raise PlatformException('404', "Project not found")

        # plugin_inputs = self.plugin_json['inputs']
        plugin_inputs = self.client_api.plugin_io.get('inputs')
        kwargs = {}
        for plugin_input in plugin_inputs:
            kwargs[plugin_input['name']] = self.get_field(plugin_input['name'],
                                                        plugin_input['type'],
                                                        project, self.mock_json)

        return run_function(**kwargs)

    def get_dataset(self, project, resource_id):
        """
        Get dataset
        :param project:
        :param resource_id:
        :return: Dataset entity
        """
        if 'dataset_id' in resource_id:
            dataset_id = resource_id['dataset_id']
        else:
            dataset_id = self.client_api.state_io.get('dataset')

        return project.datasets.get(dataset_id=dataset_id)

    def get_item(self, project, resource_id):
        """
        Get item
        :param project:
        :param resource_id:
        :return: Item entity
        """
        dataset = self.get_dataset(project, resource_id)
        return dataset.items.get(item_id=resource_id['item_id'])

    def get_annotation(self, project, resource_id):
        """
        Get annotation
        :param project:
        :param resource_id:
        :return: Annotation entity
        """
        item = self.get_dataset(project, resource_id)
        return item.annotations.get(annotation_id=resource_id['annotation_id'])

    def get_field(self, field_name, field_type, project, mock_json):
        """
        Get field in mock json
        :param field_name:
        :param field_type:
        :param project:
        :param mock_json:
        :return:
        """
        mock_inputs = mock_json['inputs']
        filtered_mock_inputs = list(filter(lambda input_field: input_field['name'] == field_name, mock_inputs))

        if len(filtered_mock_inputs) == 0:
            raise Exception('No entry for field {} found in mock'.format(field_name))
        if len(filtered_mock_inputs) > 1:
            raise Exception('Duplicate entries for field {} found in mock'.format(field_name))

        mock_input = filtered_mock_inputs[0]
        resource_id = mock_input['value']

        if field_type == 'Dataset':
            return self.get_dataset(project, resource_id)

        elif field_type == 'Item':
            return self.get_item(project, resource_id)

        elif field_type == 'Annotation':
            return self.get_annotation(project, resource_id)

        elif field_type == 'Json':
            return mock_input['value']

        else:
            raise PlatformException('400', 'Unknown resource type for field {}'.format(field_name))
