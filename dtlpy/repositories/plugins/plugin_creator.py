import os
import json
from ... import repositories, PlatformException, services


class PluginCreator:
    """
    Plugin Creator Class
    """
    def __init__(self, client_api=None):
        self.client_api = client_api
        assert isinstance(self.client_api, services.ApiClient)
        with open(os.path.join(os.getcwd(), 'plugin.json'), 'r') as f:
            self.plugin_json = json.load(f)

    @staticmethod
    def input_template(name, entity):
        """
        Create input template
        :param name:
        :param entity:
        :return:
        """
        if entity.lower() not in ['dataset', 'item', 'annotation', 'json']:
            raise PlatformException('400', 'Unknown input type for field {}'.format(entity))
        return {
            "path": name,
            "resource": entity.lower(),
            "by": "val",
            "constValue": None
        }

    @staticmethod
    def output_template(name, entity):
        """
        Create output template
        :param name:
        :param entity:
        :return:
        """
        if entity.lower() not in ['dataset', 'item', 'annotation', 'json']:
            raise PlatformException('400', 'Unknown output type for field {}'.format(entity))
        return {
            "path": name,
            "from": name,
            "by": entity.lower(),
            "resource": "raw"
        }

    def create_input_parameters(self, project_id, package):
        """
        Create input parameters
        :param project_id:
        :param package:
        :return:
        """
        projects = repositories.Projects(client_api=self.client_api)
        project = projects.get(project_id=project_id)

        base = [
            {
                'path': 'package_id',
                'resource': 'package',
                'by': 'ref',
                'constValue': package.id
            },
            {
                'path': 'package_version',
                'resource': 'package',
                'by': 'ref',
                'constValue': str(package.version)
            },
            {
                'path': 'project_id',
                'resource': 'project',
                'by': 'ref',
                'constValue': project.id
            }
        ]

        for input_filed in self.plugin_json['inputs']:
            input_name = input_filed['name']
            input_type = input_filed['type']
            base.append(self.input_template(name=input_name, entity=input_type))

        return base

    def create_output_parameters(self):
        """
        Create output parameters
        :return:
        """
        base = []
        for output in self.plugin_json['outputs']:
            output_name = output['name']
            output_type = output['type']
            base.append(self.output_template(name=output_name, entity=output_type))

        return base

    def create_plugin(self):
        """
        Create plugin
        :return: plugin entity
        """
        project_id = self.client_api.state_io.get('project')
        # plugin_name = self.client_api.state_io.get('plugin')
        plugin_name = self.plugin_json['name']

        if project_id is None:
            raise PlatformException('400', 'Please run "dlp checkout project <project_name>" first')

        if plugin_name is None:
            raise PlatformException('400', 'Please run "dlp checkout plugin <plugin_name>" first')

        package = self.upload_package()

        input_params = self.create_input_parameters(project_id=project_id,
                                                    package=package)
        output_params = self.create_output_parameters()

        projects = repositories.Projects(client_api=self.client_api)
        project = projects.get(project_id=project_id)
        plugin = project.plugins.get(plugin_name=plugin_name)
        if plugin is None:
            plugin = project.plugins.create(name=plugin_name,
                                            package=package.id,
                                            input_parameters=input_params,
                                            output_parameters=output_params)
        else:
            plugin.input = input_params
            plugin.output = output_params
            plugin = project.plugins.edit(plugin=plugin, system_metadata=True)

        return plugin

    def upload_package(self):
        """
        Upload plugin source code
        :return:
        """
        project_id = self.client_api.state_io.get('project')
        plugin_name = self.client_api.state_io.get('plugin')
        cwd = os.getcwd()
        dataloop_path = os.path.join(cwd, '.dataloop')

        if not os.path.exists(dataloop_path):
            print('No .dataloop folder found, please run "dlp init"')
            exit(-1)

        src_path = os.path.join(cwd, 'src')

        projects = repositories.Projects(client_api=self.client_api)
        project = projects.get(project_id=project_id)
        package = project.packages.pack(directory=src_path, name=plugin_name)
        return package
