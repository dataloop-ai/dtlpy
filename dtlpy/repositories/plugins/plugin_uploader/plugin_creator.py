import os
import json
import atexit
import dtlpy

from dtlpy.utilities.plugin_bootstraping.util import get_plugin_json, get_state_json
from .package_uploader import PackageUploader

class PluginCreator:
    def __init__(self):
        self.plugin_json = get_plugin_json()

    def dataset_input_template(self, name):
        return {
            "path": name,
            "resource": "dataset",
            "by": "val",
            "constValue": None
        }

    def item_input_template(self, name):
        return {
            "path": name,
            "resource": "item",
            "by": "val",
            "constValue": None
        }

    def annotation_input_template(self, name):
        return {
            "path": name,
            "resource": "annotation",
            "by": "val",
            "constValue": None
        }

    def json_input_template(self, name):
        return {
            "path": name,
            "resource": "json",
            "by": "val",
            "constValue": None
        }

    def dataset_output_template(self, name):
        return {
            "path": name,
            "from": name,
            "by": "dataset",
            "resource": "raw"
        }

    def item_output_template(self, name):
        return {
            "path": name,
            "from": name,
            "by": "item",
            "resource": "raw"
        }

    def annotation_output_template(self, name):
        return {
            "path": name,
            "from": name,
            "by": "annotation",
            "resource": "raw"
        }

    def json_output_template(self, name):
        return {
            "path": name,
            "from": name,
            "by": "json",
            "resource": "raw"
        }

    def create_input_parameters(self, dlp, project_id, package):
        project = dlp.projects.get(project_id=project_id)

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

        for input in self.plugin_json['inputs']:
            input_name = input['name']
            input_type = input['type']
            if (input_type == 'Dataset'):
                base.append(self.dataset_input_template(input_name))
            elif (input_type == 'Item'):
                base.append(self.item_input_template(input_name))
            elif (input_type == 'Annotation'):
                base.append(self.annotation_input_template(input_name))
            elif (input_type == 'Json'):
                base.append(self.json_input_template(input_name))
            else:
                raise Exception('Unknown input type for field {}'.format(input_name))
        return base

    def create_output_parameters(self):
        base = []
        for output in self.plugin_json['outputs']:
            output_name = output['name']
            output_type = output['type']
            if (output_type == 'Dataset'):
                base.append(self.dataset_output_template(output_name))
            elif (output_type == 'Item'):
                base.append(self.item_output_template(output_name))
            elif (output_type == 'Annotation'):
                base.append(self.item_annotation_template(output_name))
            elif (output_type == 'Json'):
                base.append(self.json_output_template(output_name))
            else:
                raise Exception('Unknown output type for field {}'.format(output_name))
        return base

    def save_json_to_file(self, obj, filepath):
        file = os.open(filepath, 'w+')
        file.write(json.dumps(obj))

    def create_plugin(self):
        try:
            state_json = get_state_json()
        except:
            raise Exception('.dataloop/state.json not found, you might have not run dlp plugins init')

        if not 'project' in state_json:
            raise Exception('Please run "dlp checkout project <project_name>" first')

        if not 'package' in state_json:
            raise Exception('Please run "dlp checkout plugin <plugin_name>" first')

        package_uploader = PackageUploader()
        package = package_uploader.upload_package()

        state_json = get_state_json()
        project_id = state_json['project']
        plugin_name = state_json['package']

        input_params = self.create_input_parameters(dtlpy, state_json['project'], package)
        output_params = self.create_output_parameters()

        project = dtlpy.projects.get(project_id=project_id)
        plugin = project.plugins.get(plugin_name=plugin_name)
        if plugin is None:
            project.plugins.create(state_json['package'], package.id, input_params, output_params)
        else:
            plugin.input = input_params
            plugin.output = output_params
            dtlpy.plugins.edit(plugin=plugin, system_metadata=True)