import logging
import json
import multiprocessing
import sys
import os
from shutil import copyfile
from multiprocessing.pool import ThreadPool

from .. import entities, repositories, exceptions, utilities, services, miscellaneous
from ..assets import plugin_json_path, main_py_path, mock_json_path, deployment_json_local_path, \
    plugin_default_gitignore


class Plugins:
    """
    Plugin Repository
    """

    def __init__(self, client_api, project=None):
        self.client_api = client_api
        self._project = project
        self.plugin_io = PluginIO()

    @property
    def project(self):
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self.client_api).get()
            except Exception:
                logging.warning('please checkout a project or use project plugins repository for this action')
        return self._project

    def __get_project(self, plugin):
        assert isinstance(plugin, entities.Plugin)
        if plugin.project is None:
            projects = repositories.Projects(client_api=self.client_api)
            self._project = projects.get(project_id=plugin.project_id)
        else:
            self._project = plugin.project

    def get(self, plugin_name=None, plugin_id=None):
        """
        Get Plugin object

        :param plugin_id:
        :param plugin_name:
        :return: Plugin object
        """
        # get bby name
        if plugin_id is None:
            if plugin_name is None:
                try:
                    plugin_name = self.plugin_io.get('name')
                except Exception:
                    try:
                        plugin_name = self.client_api.state_io.get('plugin')
                    except Exception:
                        plugin_name = None
                if plugin_name is None:
                    raise exceptions.PlatformException('400', 'Must provide either plugin id or plugin name')
            plugins = self.list()
            for plugin in plugins:
                if plugin.name == plugin_name:
                    plugin_id = plugin.id

        # get by id
        # request
        success, response = self.client_api.gen_request(
            req_type="get",
            path="/plugins/{}".format(plugin_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Plugin.from_json(client_api=self.client_api,
                                         _json=response.json(),
                                         project=self._project)

    def list(self):
        """
        List project plugins
        :return:
        """
        url_path = '/plugins'

        if self._project is not None:
            url_path += '?projects={}'.format(self.project.id)

        # request
        success, response = self.client_api.gen_request(req_type='get',
                                                        path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        # return plugins list
        plugins = miscellaneous.List()
        for plugin in response.json()['items']:
            plugins.append(entities.Plugin.from_json(client_api=self.client_api,
                                                     _json=plugin,
                                                     project=self._project))
        return plugins

    def pull(self, plugin, version=None, local_path=None):
        """
        :param version:
        :param plugin:
        :param local_path:
        :return:
        """
        assert isinstance(plugin, entities.Plugin)

        if self.project is None:
            self.__get_project(plugin)

        dir_version = version
        if version is None:
            dir_version = plugin.version

        if local_path is None:
            local_path = os.path.join(
                os.path.expanduser("~"),
                ".dataloop",
                "projects",
                self.project.name,
                "plugins",
                plugin.name,
                str(dir_version))

        if version is None or version == plugin.version:
            package_id = plugin.packageId
        else:
            versions = [revision for revision in plugin.revisions if revision['version'] == version]
            if len(versions) <= 0:
                raise exceptions.PlatformException('404', 'Version not found: version={}'.format(version))
            elif len(versions) > 1:
                raise exceptions.PlatformException('404', 'More than one version found: version={}'.format(version))
            package_id = versions[0]['packageId']

        self.project.packages.unpack(package_id=package_id, local_path=local_path)

        return local_path

    def push(self, package_id=None, src_path=None, plugin_name=None, inputs=None, outputs=None):
        """
        Push local plugin

        :param package_id:
        :param src_path:
        :param plugin_name:
        :param inputs:
        :param outputs:
        :return:
        """
        # get project
        if self.project is None:
            raise exceptions.PlatformException('400', 'Repository does not have project. Please checkout a project,'
                                                      'or create plugin from a project plugins repository')
        # source path
        if src_path is None:
            if inputs is None or outputs is None or package_id is None:
                src_path = os.getcwd()
                logging.warning('No src_path is given, getting plugin information from cwd: {}'.format(src_path))

        # get plugin json
        plugin_json = dict()
        if 'plugin.json' in os.listdir(src_path):
            with open(os.path.join(src_path, 'plugin.json'), 'r') as f:
                plugin_json = json.load(f)

        # get name
        if plugin_name is None:
            if 'name' in plugin_json:
                plugin_name = plugin_json['name']
            else:
                plugin_name = 'default_plugin'

        # inputs/outputs
        if inputs is None:
            if 'inputs' in plugin_json:
                inputs = plugin_json['inputs']
            else:
                inputs = list()
        else:
            if not isinstance(inputs, list):
                inputs = [inputs]
            if len(inputs) > 0 and isinstance(inputs[0], entities.PluginInput):
                for i_input, single_input in enumerate(inputs):
                    inputs[i_input] = single_input.to_json(resource='plugin')

        if outputs is None:
            if 'outputs' in plugin_json:
                outputs = plugin_json['outputs']
            else:
                outputs = list()

        # get or create package
        if package_id is None:
            package_id = self.project.packages.pack(directory=src_path, name=plugin_name).id

        # check if exist
        plugins = [plugin for plugin in self.list() if plugin.name == plugin_name]
        if len(plugins) > 0:
            return self._create(package_id=package_id,
                                plugin_name=plugin_name,
                                inputs=inputs,
                                outputs=outputs,
                                push=True,
                                plugin=plugins[0])
        else:
            return self._create(package_id=package_id,
                                plugin_name=plugin_name,
                                inputs=inputs,
                                outputs=outputs,
                                push=False)

    def _create(self,
                package_id=None,
                plugin_name=None,
                inputs=None,
                outputs=None,
                push=False,
                plugin=None):
        """
        Create a plugin in platform

        :param plugin:
        :param push:
        :param package_id: optional - plugin package
        :param plugin_name: optional - default: 'default plugin'
        :param inputs: optional - default: list()
        :param outputs: optional - default: list()
        :return: Plugin Entity
        """
        if push:
            plugin.packageId = package_id
            return self.update(plugin=plugin)

        payload = {'name': plugin_name,
                   'packageId': package_id,
                   'inputs': inputs,
                   'outputs': outputs,
                   'project': self.project.id
                   }

        # request
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/plugins',
                                                        json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Plugin.from_json(_json=response.json(),
                                         client_api=self.client_api,
                                         project=self._project)

    def delete(self, plugin=None, plugin_name=None, plugin_id=None):
        """
        Delete Plugin object

        :param plugin:
        :param plugin_name:
        :param plugin_id:
        :return: True
        """
        # get id and name
        if plugin_name is None or plugin_id is None:
            if plugin is None:
                plugin = self.get(plugin_id=plugin_id, plugin_name=plugin_name)
            plugin_id = plugin.id
            plugin_name = plugin.name

        # check if project exist
        if self.project is None:
            projects = repositories.Projects(client_api=self.client_api)
            self._project = projects.get(project_id=plugin.project_id)

        # create packages repo
        packages = repositories.Packages(client_api=self.client_api, project=self.project)

        # get plugin packages
        packages = packages.list_versions(package_name=plugin_name)
        for packages_page in packages:
            for package in packages_page:
                package.delete()

        # request
        success, response = self.client_api.gen_request(
            req_type="delete",
            path="/plugins/{}".format(plugin_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, plugin):
        """
        Update Plugin changes to platform

        :param plugin:
        :return: Plugin entity
        """
        assert isinstance(plugin, entities.Plugin)

        # payload
        payload = plugin.to_json()

        # request
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path='/plugins/{}'.format(plugin.id),
                                                        json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Plugin.from_json(_json=response.json(),
                                         client_api=self.client_api,
                                         project=self._project)

    def deploy(self,
               plugin_id=None,
               plugin_name=None,
               plugin=None,
               deployment_name=None,
               revision=None,
               config=None,
               runtime=None):
        """
        Deploy plugin

        :param runtime:
        :param config:
        :param revision:
        :param deployment_name:
        :param plugin:
        :param plugin_id:
        :param plugin_name:
        :return:
        """

        if plugin is None:
            plugin = self.get(plugin_id=plugin_id, plugin_name=plugin_name)

        return plugin.deployments.deploy(plugin=plugin,
                                         deployment_name=deployment_name,
                                         revision=revision,
                                         config=config,
                                         runtime=runtime)

    @staticmethod
    def generate(name=None, src_path=None):
        """
        Generate new plugin environment

        :return:
        """
        # name
        if name is None:
            name = 'default_plugin'

        # src path
        if src_path is None:
            src_path = os.getcwd()

        with open(plugin_json_path, 'r') as f:
            plugin_asset = json.load(f)

        plugin_asset['name'] = name

        with open(os.path.join(src_path, 'plugin.json'), 'w+') as f:
            json.dump(plugin_asset, f)

        copyfile(plugin_default_gitignore, os.path.join(src_path, '.gitignore'))
        copyfile(mock_json_path, os.path.join(src_path, 'mock.json'))
        copyfile(main_py_path, os.path.join(src_path, 'main.py'))
        # copyfile(debug_py_path, os.path.join(src_path, 'debug.py'))
        # copyfile(src_init_file_path, os.path.join(src_path, '__init__.py'))

        with open(deployment_json_local_path, 'r') as f:
            deployment_json = json.load(f)
        deployment_json = deployment_json[0]
        with open(os.path.join(src_path, 'deployment.json'), 'w+')as f:
            json.dump(deployment_json, f, indent=2)

        logging.info('Successfully generated plugin')

    def is_multithread(self, inputs):
        is_multi = False
        if isinstance(inputs[0], list):
            is_multi = True

        if is_multi:
            for single_input in inputs:
                if not isinstance(single_input, list):
                    raise exceptions.PlatformException('400', 'mock.json inputs can be either list of dictionaries '
                                                              'or list of lists')

        return is_multi

    def test_local_plugin(self, cwd=None, concurrency=None):
        """
        Test local plugin
        :return:
        """
        if cwd is None:
            cwd = os.getcwd()

        with open(os.path.join(cwd, 'mock.json'), 'r') as f:
            mock_json = json.load(f)
        is_multithread = self.is_multithread(inputs=mock_json['inputs'])

        local_runner = LocalPluginRunner(self.client_api, plugins=self, cwd=cwd, multithreading=is_multithread,
                                         concurrency=concurrency)
        return local_runner.run_local_project()

    def checkout(self, plugin_name):
        """
        Checkout as plugin

        :param plugin_name:
        :return:
        """
        self.plugin_io.put('name', plugin_name)
        self.client_api.state_io.put('plugin', plugin_name)
        logging.info("Checked out to plugin {}".format(plugin_name))


class LocalPluginRunner:
    """
    Package Runner Class
    """

    def __init__(self, client_api, plugins, cwd=None, multithreading=False, concurrency=32):
        if cwd is None:
            self.cwd = os.getcwd()
        else:
            self.cwd = cwd

        self._client_api = client_api
        self._plugins = plugins
        self.plugin_io = PluginIO(cwd=self.cwd)
        self.multithreading = multithreading
        self.concurrency = concurrency

        with open(os.path.join(self.cwd, 'mock.json'), 'r') as f:
            self.mock_json = json.load(f)

    def validate_mock(self, plugin_json, mock_json):
        """
        Validate mock
        :param plugin_json:
        :param mock_json:
        :return:
        """
        inputs = mock_json['inputs']
        if not self.multithreading:
            inputs = [inputs]
        for single_input in inputs:
            if len(plugin_json['inputs']) != len(single_input):
                raise exceptions.PlatformException('400', 'Parameters in mock, not fit the parameters in plugin.json')

    def get_mainpy_run_function(self):
        """
        Get mainpy run function
        :return:
        """
        sys.path.insert(0, self.cwd)
        # noinspection PyUnresolvedReferences
        from main import PluginRunner
        kwargs = self.mock_json.get('config', dict())
        return PluginRunner(**kwargs)

    def run_local_project(self):
        assert isinstance(self._client_api, services.ApiClient)
        self.validate_mock(self.plugin_io.read_json(), self.mock_json)
        plugin_runner = self.get_mainpy_run_function()

        try:
            projects = repositories.Projects(client_api=self._client_api)
            project = projects.get()
        except Exception:
            raise exceptions.PlatformException('400', "Please checkout to a valid project")

        plugin_inputs = self.plugin_io.get('inputs')
        if not self.multithreading:
            kwargs = dict()
            progress = utilities.Progress()
            kwargs['progress'] = progress
            for plugin_input in plugin_inputs:
                kwargs[plugin_input['name']] = self.get_field(plugin_input['name'],
                                                              plugin_input['type'],
                                                              project, self.mock_json)
            results = plugin_runner.run(**kwargs)
        else:
            pool = ThreadPool(processes=self.concurrency)
            inputs = self.mock_json['inputs']
            results = list()
            jobs = list()
            for single_input in inputs:
                kwargs = dict()
                progress = utilities.Progress()
                kwargs['progress'] = progress
                for plugin_input in plugin_inputs:
                    kwargs[plugin_input['name']] = self.get_field(field_name=plugin_input['name'],
                                                                  field_type=plugin_input['type'],
                                                                  project=project,
                                                                  mock_json=self.mock_json,
                                                                  mock_inputs=single_input)
                jobs.append(
                    pool.apply_async(
                        func=plugin_runner.run,
                        kwds=kwargs
                    )
                )
            for job in jobs:
                job.wait()
                results.append(job.get())

        return results

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
            dataset_id = self._client_api.state_io.get('dataset')

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
        item = self.get_item(project, resource_id)
        return item.annotations.get(annotation_id=resource_id['annotation_id'])

    def get_field(self, field_name, field_type, project, mock_json, mock_inputs=None):
        """
        Get field in mock json
        :param field_name:
        :param field_type:
        :param project:
        :param mock_json:
        :param mock_inputs:
        :return:
        """
        if mock_inputs is None:
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
            raise exceptions.PlatformException('400', 'Unknown resource type for field {}'.format(field_name))


class PluginIO:

    def __init__(self, cwd=None):
        if cwd is None:
            cwd = os.getcwd()

        self.plugin_file_path = os.path.join(cwd, 'plugin.json')

    def read_json(self):
        with open(self.plugin_file_path, 'r') as fp:
            cfg = json.load(fp)
        return cfg

    def get(self, key):
        cfg = self.read_json()
        return cfg[key]

    def put(self, key, value):
        cfg = self.read_json()
        cfg[key] = value

        with open(self.plugin_file_path, 'w') as fp:
            json.dump(cfg, fp, indent=4)
