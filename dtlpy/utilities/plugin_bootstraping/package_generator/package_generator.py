import pystache
import os
import shutil
from shutil import copyfile


def generate_package():
    cwd = os.getcwd()

    src_dir = os.path.join(cwd, 'src')
    os.mkdir(src_dir)

    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')

    params_mustache = open(os.path.join(assets_dir, 'plugin.json'), 'r').read()
    rendered_params_file = pystache.render(params_mustache, {})
    manifest_file = open(os.path.join(cwd, 'plugin.json'), 'w+')
    manifest_file.write(rendered_params_file)

    copyfile(os.path.join(assets_dir, 'main.py'), os.path.join(src_dir, 'main.py'))
    copyfile(os.path.join(assets_dir, 'mock.json'), os.path.join(cwd, 'mock.json'))

    print('Successfully generated plugin')


