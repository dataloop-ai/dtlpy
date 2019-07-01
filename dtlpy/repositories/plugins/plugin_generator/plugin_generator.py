import os
from shutil import copyfile
from dtlpy.repositories.plugins.assets import plugin_json_path, main_py_path, mock_json_path, src_init_file_path


def generate_plugin():
    cwd = os.getcwd()

    src_dir = os.path.join(cwd, 'src')
    os.mkdir(src_dir)

    plugin_asset = open(plugin_json_path, 'r').read()
    manifest_file = open(os.path.join(cwd, 'plugin.json'), 'w+')
    manifest_file.write(plugin_asset)

    copyfile(main_py_path, os.path.join(src_dir, 'main.py'))
    copyfile(mock_json_path, os.path.join(cwd, 'mock.json'))
    copyfile(src_init_file_path, os.path.join(src_dir, '__init__.py'))

    print('Successfully generated plugin')


