import os

assets_path = os.path.dirname(__file__)
main_py_path = os.path.join(assets_path, 'main.py')
mock_json_path = os.path.join(assets_path, 'mock.json')
plugin_json_path = os.path.join(assets_path, 'plugin.json')
task_init_json_path = os.path.join(assets_path, 'task-init.json')
task_main_json_path = os.path.join(assets_path, 'task-main.json')
wrapper_mustache_path = os.path.join(assets_path, 'wrapper.py.mustache')