import logging
import os
from shutil import copyfile
import json

from ... import entities, utilities, PlatformException, repositories, services
from .assets import plugin_json_path, main_py_path, mock_json_path, src_init_file_path, debug_py_path
from .package_runner import PackageRunner
from .plugin_creator import PluginCreator


class Plugins:
    """
    Plugins repository
    """

    def __init__(self, client_api, project=None):
        self.logger = logging.getLogger('dataloop.plugins')
        self.client_api = client_api
        self._project = project

    @property
    def project(self):
        if self._project is None:
            projects = repositories.Projects(client_api=self.client_api)
            try:
                self._project = projects.get()
            except Exception:
                logging.warning('Please checkout project')

        return self._project

    @project.setter
    def project(self, project):
        self._project = project

    @staticmethod
    def generate_local_plugin(name='defaul_plugin'):
        """
        Generate new plugin environment
        :return:
        """
        cwd = os.getcwd()

        src_dir = os.path.join(cwd, 'src')
        if not os.path.isdir(src_dir):
            os.mkdir(src_dir)

        with open(plugin_json_path, 'r') as f:
            plugin_asset = json.load(f)
        plugin_asset['name'] = name

        with open(os.path.join(cwd, 'plugin.json'), 'w+') as f:
            json.dump(plugin_asset, f)

        copyfile(main_py_path, os.path.join(src_dir, 'main.py'))
        copyfile(debug_py_path, os.path.join(src_dir, 'debug.py'))
        copyfile(mock_json_path, os.path.join(cwd, 'mock.json'))
        copyfile(src_init_file_path, os.path.join(src_dir, '__init__.py'))

        print('Successfully generated plugin')

    def test_local_plugin(self):
        """
        Test local plugin
        :return:
        """
        package_runner = PackageRunner(self.client_api)
        package_runner.run_local_project()

    def checkout(self, plugin_name):
        assert isinstance(self.client_api, services.ApiClient)
        try:
            self.client_api.plugin_io.put('name', plugin_name)
            self.logger.info("Checked out to plugin {}".format(plugin_name))
        except Exception:
            self.logger.error('Cant checkout to different plugin name before generating a plugin')

    def create(self, name, package=None, input_parameters=None, output_parameters=None, from_creator=False):

        """
        Create a new plugin
        :param name: plugin name
        :param input_parameters: inputs for the plugin's sessions
        :param output_parameters: outputs for the plugin's sessions
        :param package: packageId:version
        :param from_creator: optional - called from plugin creator function
        :return: plugin entity
        """
        if not from_creator and (input_parameters is None or output_parameters is None or package is None):
            plugin_creator = PluginCreator(client_api=self.client_api)
            return plugin_creator.create_plugin()

        if isinstance(input_parameters, entities.PluginInput):
            input_parameters = [input_parameters]

        if not isinstance(input_parameters, list):
            raise TypeError('must be a list of PluginInput')

        input_parameters.append({'path': 'package',
                                 'resource': 'package',
                                 'by': 'ref',
                                 'constValue': package})
        payload = {'name': name,
                   'pipeline': dict(),
                   'input': input_parameters,
                   'output': output_parameters,
                   'metadata': {'system': {
                       "projects": [self.project.id]
                   }}
                   }

        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/tasks',
                                                        json_req=payload)
        if success:
            plugin = entities.Plugin.from_json(client_api=self.client_api,
                                               _json=response.json())
        else:
            self.logger.exception('Platform error creating new plugin:')
            raise PlatformException(response)

        return plugin

    def list(self):
        """
        List all plugin.
        :return: List of Plugin objects
        """
        if self.project is None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks')
        else:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks?projects=%s' % self.project.id)

        if success:
            plugins = utilities.List(
                [entities.Plugin.from_json(client_api=self.client_api,
                                           _json=_json)
                 for _json in response.json()['items']])
            return plugins
        else:
            self.logger.exception('Platform error getting plugins')
            raise PlatformException(response)

    def get(self, plugin_id=None, plugin_name=None):
        """
        Get a Pipeline object
        :param plugin_id: optional - search by id
        :param plugin_name: optional - search by name
        :return: Pipeline object
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/tasks/%s' % plugin_id)
            if success:
                res = response.json()
                if len(res) > 0:
                    plugin = entities.Plugin.from_json(client_api=self.client_api, _json=res)
                else:
                    plugin = None
            else:
                self.logger.exception('Platform error getting the plugin. id: %s' % plugin_id)
                raise PlatformException(response)
        elif plugin_name is not None:
            plugins = self.list()
            plugin = [plugin for plugin in plugins if plugin.name == plugin_name]
            if len(plugin) == 0:
                self.logger.info('Pipeline not found. plugin id : %s' % plugin_name)
                plugin = None
            elif len(plugin) > 1:
                self.logger.warning('More than one plugin with same name. Please "get" by id')
                raise PlatformException('404', 'More than one plugin with same name. Please "get" by id')
            else:
                plugin = plugin[0]
        else:
            assert isinstance(self.client_api, services.ApiClient)
            plugin_name = self.client_api.plugin_io.get(value='name')
            if plugin_name is not None:
                plugin = self.get(plugin_name=plugin_name)
            else:
                self.logger.exception('Must input one search parameter or checkout a plugin!')
                raise PlatformException('Must input one search parameter or checkout a plugin!')
        return plugin

    def delete(self, plugin_name=None, plugin_id=None):
        """
        Delete remote item
        :param plugin_name: optional - search item by remote path
        :param plugin_id: optional - search item by id
        :return: True
        """
        if plugin_id is not None:
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin_id)
        elif plugin_name is not None:
            plugin = self.get(plugin_name=plugin_name)
            if plugin is None:
                self.logger.warning('plugin name was not found: name: %s' % plugin_name)
                raise PlatformException('400', 'plugin name was not found: name: %s' % plugin_name)
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/tasks/%s' % plugin.id)
        else:
            raise PlatformException('400', 'must provide either plugin name or plugin id')
        return success

    def edit(self, plugin, system_metadata=False):
        """
        Edit an existing plugin
        :param plugin: Plugin entity
        :param system_metadata: bool
        :return: Plugin entity
        """
        url_path = '/tasks/%s' % plugin.id
        if system_metadata:
            url_path += '?system=true'

        plugin_json = plugin.to_json()
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=plugin_json)
        if success:
            return entities.Plugin.from_json(client_api=self.client_api,
                                             _json=response.json())
        else:
            self.logger.exception('Platform error editing plugin. id: %s' % plugin.id)
            raise PlatformException(response)

    def deploy(self, plugin_id, revision=None):
        """
        Deploy an existing plugin
        :param revision: optional - revision
        :param plugin_id: Id of plugin to deploy
        :return:
        """
        url_path = '/plugins/%s/deploy?' % plugin_id

        if revision is not None:
            url_path += 'revision=%s' % revision

        success, response = self.client_api.gen_request(req_type='post',
                                                        path=url_path)
        if success:
            logging.info("Successfully deployed the plugin, deployment id is: %s" % response.text)
            return response.text
        else:
            self.logger.exception('Platform error deploying plugin. id: %s' % plugin_id)
            raise PlatformException(response)

    def status(self, plugin_id):
        """
        Return plugin's status
        :param plugin_id:
        :return:
        """
        url_path = '/plugins/%s/status' % plugin_id
        success, response = self.client_api.gen_request(req_type='get',
                                                        path=url_path)

        if success:
            return response.text
        else:
            self.logger.exception('Platform error getting plugin status. id: %s' % plugin_id)
            raise PlatformException(response)

    def push_local_plugin(self, deploy=False, revision=None):
        """
        Push local plugin to platform
        :param deploy: optional - True/False - deploy after pushing
        :param revision: optional - revision
        :return:
        """
        plugin_creator = PluginCreator(client_api=self.client_api)
        plugin = plugin_creator.create_plugin()
        if deploy:
            if self.project is None:
                projects = repositories.Projects(client_api=self.client_api)
                self._project = projects.get()
            self.project.plugins.deploy(plugin_id=plugin.id, revision=revision)

    def invoke_plugin(self, input_file_path='./mock.json'):
        """
        Invoke local plugin
        :param input_file_path:
        :return:
        """
        input_path = os.path.abspath(input_file_path)
        file_as_str = open(input_path, 'r').read()
        file_as_obj = json.loads(file_as_str)
        inputs = file_as_obj['inputs']
        parsed_inputs = {}

        assert isinstance(inputs, list)
        for input_field in inputs:
            parsed_inputs[input_field['name']] = input_field['value']

        project_id = self.client_api.state_io.get('project')
        # task_name = self.client_api.state_io.get('plugin')
        assert isinstance(self.client_api, services.ApiClient)
        plugin_name = self.client_api.plugin_io.get('name')

        projects = repositories.Projects(client_api=self.client_api)
        project = projects.get(project_id=project_id)
        task = project.tasks.get(task_name=plugin_name)
        session = task.sessions.create(parsed_inputs, True)

        if session.latestStatus['status'] == 'success':
            return session.output
        else:
            raise PlatformException('400', session.latestStatus['error'])

    def deploy_plugin_from_folder(self, revision):
        """
        Deploy plugin from folder
        :param revision: revision
        :return:
        """
        assert isinstance(self.client_api, services.ApiClient)
        # plugin_name = self.client_api.state_io.get('plugin')
        plugin_name = self.client_api.plugin_io.get('name')
        if plugin_name is None:
            raise Exception('Please run "dlp checkout plugin <plugin_name>" first')

        try:
            tasks = repositories.Tasks(client_api=self.client_api, project=self.project)
            plugin = tasks.get(task_name=plugin_name)
        except Exception:
            raise PlatformException('404', 'Plugin not found, you should run dlp plugins push first')

        return self.deploy(plugin.id, revision)

    def get_status_from_folder(self):
        """
        Get status from folder
        :return:
        """
        assert isinstance(self.client_api, services.ApiClient)
        plugin_name = self.client_api.plugin_io.get('name')
        if plugin_name is None:
            raise PlatformException('400', 'Please run "dlp checkout plugin <plugin_name>" first')
        try:
            tasks = repositories.Tasks(client_api=self.client_api, project=self.project)
            plugin = tasks.get(task_name=plugin_name)
        except Exception:
            raise PlatformException('400', 'Plugin not found, you should run dlp plugins push first')

        print(self.status(plugin.id))
