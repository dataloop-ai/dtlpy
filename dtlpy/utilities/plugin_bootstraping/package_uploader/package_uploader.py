import os
import shutil
import json
import pystache
from ..util import get_plugin_json, get_state_json
from .task_creator import TaskCreator

class PackageUploader:
    def __init__(self):
        self.state_json = get_state_json()
        self.project_id = self.state_json['project']
        self.task_name = self.state_json['package']
        self.plugin_json = get_plugin_json()
        self.assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')

    def create_wrapper_py_file(self, dest_dir):
        raw_inputs_arr = ['platform_interface']
        resource_resolution_arr = []
        resolved_resources_arr = []

        for input in self.plugin_json['inputs']:
            input_name = input['name']
            input_type = input['type']
            resolved_resources_arr.append(input_name)

            if (input_type == 'Dataset'):
                raw_inputs_arr.append(input_name + '_44_dataset_id')
                resource_resolution_arr.append('{} = Wrapper.get_dataset(platform_interface, {}_44_dataset_id)'
                                               .format(input_name, input_name))
            elif (input_type == 'Item'):
                raw_inputs_arr.append(input_name + '_44_dataset_id')
                raw_inputs_arr.append(input_name + '_44_item_id')
                resource_resolution_arr.append('{} = Wrapper.get_item(platform_interface, {}_44_dataset_id, {}_44_item_id)'
                                               .format(input_name, input_name, input_name))
            elif (input_type == 'Annotation'):
                raw_inputs_arr.append(input_name + '_44_dataset_id')
                raw_inputs_arr.append(input_name + '_44_item_id')
                raw_inputs_arr.append(input_name + '_44_annotation_id')
                resource_resolution_arr.append('{} = Wrapper.get_annotation(platform_interface, {}_44_ataset_id, {}_44_item_id, {}_44_annotation_id)'
                                               .format(input_name, input_name, input_name, input_name))
            else:
                raw_inputs_arr.append(input_name)

        raw_inputs = ",".join(raw_inputs_arr)
        resource_resolution = ';'.join(resource_resolution_arr)
        resolved_resources = ','.join(resolved_resources_arr)

        output_resolution_arr = []

        for output in self.plugin_json['outputs']:
            output_name = output['name']
            output_type = output['type']

            if (output_type == 'Dataset'):
                output_resolution_arr.append('outputs[{}_44_dataset_id] = ret_val[{}].id'
                                             .format(output_name, output_name))
            elif (output_type == 'Item'):
                output_resolution_arr.append('outputs[{}_44_dataset_id] = ret_val[{}].dataset.id'
                                             .format(output_name, output_name))
                output_resolution_arr.append('outputs[{}_44_item_id] = ret_val[{}].id'
                                             .format(output_name, output_name))
            elif (output_type == 'Annotation'):
                output_resolution_arr.append('outputs[{}_44_dataset_id] = ret_val[{}].item.dataset.id'
                                             .format(output_name, output_name))
                output_resolution_arr.append('outputs[{}_44_item_id] = ret_val[{}].item.id'
                                             .format(output_name, output_name))
                output_resolution_arr.append('outputs[{}_44_annotation_id] = ret_val[{}].id'
                                             .format(output_name, output_name))
            else:
                output_resolution_arr.append('outputs[{}] = ret_val[{}]'
                                             .format(output_name, output_name))

        output_resolution = ';'.join(output_resolution_arr)

        wrapper_py_mustache = open(os.path.join(self.assets_dir, 'wrapper.py.mustache'), 'r').read()
        rendered_wrapper_py_file = pystache.render(wrapper_py_mustache, {
            "RAW_INPUTS": raw_inputs,
            "RESOURCE_RESOLUTION": resource_resolution,
            "RESOLVED_RESOURCES": resolved_resources,
            "OUTPUT_RESOLUTION": output_resolution
        })

        wrapper_file = open(os.path.join(dest_dir, 'wrapper.py'), 'w+')
        wrapper_file.write(rendered_wrapper_py_file)

    def upload_package(self, dlp):
        cwd = os.getcwd()
        dataloop_path = os.path.join(cwd, '.dataloop')

        if not os.path.exists(dataloop_path):
            print('Package not found')
            exit(-1)

        src_path = os.path.join(cwd, 'src')
        dist_path = os.path.join(dataloop_path, 'dist')
        if (os.path.exists(dist_path)):
            shutil.rmtree(dist_path)
        shutil.copytree(src_path, dist_path)

        try:
            self.create_wrapper_py_file(dist_path)

            project = dlp.projects.get(project_id=self.project_id)
            package = project.packages.pack(directory=dist_path, name=self.task_name)
        finally:
            shutil.rmtree(dist_path)

        task_creator = TaskCreator()
        task_creator.create_task(dlp, package)