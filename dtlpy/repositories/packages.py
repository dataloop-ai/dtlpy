import importlib
import logging
import json
import os
from shutil import copyfile
from urllib.parse import urlencode
from multiprocessing.pool import ThreadPool

from .. import entities, repositories, exceptions, utilities, miscellaneous, assets

logger = logging.getLogger(name=__name__)


class Packages:
    """
    Packages Repository
    """

    def __init__(self, client_api, project=None):
        self._client_api = client_api
        self._project = project
        self.package_io = PackageIO()

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self._client_api).get()
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "project". need to set a Project entity or use project.packages repository')
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def open_in_web(self, package=None, package_id=None, package_name=None):
        if package is None:
            package = self.get(package_name=package_name, package_id=package_id)
        self._client_api._open_in_web(resource_type='package', project_id=package.project_id, package_id=package.id)

    def get(self, package_name=None, package_id=None, checkout=False, fetch=None):
        """
        Get Package object

        :param checkout:
        :param package_id:
        :param package_name:
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Package object
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if package_name is None and package_id is None:
            package = self.__get_from_cache()
            if package is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Checked out not found, must provide either package id or package name')
        elif fetch:
            if package_id is not None:
                success, response = self._client_api.gen_request(
                    req_type="get",
                    path="/packages/{}".format(package_id))
                if not success:
                    raise exceptions.PlatformException(response)
                package = entities.Package.from_json(client_api=self._client_api,
                                                     _json=response.json(),
                                                     project=self._project)
            elif package_name is not None:
                packages = self.list(name=package_name)
                if len(packages) == 0:
                    raise exceptions.PlatformException(
                        error='404',
                        message='Package not found. Name: {}'.format(package_name))
                elif len(packages) > 1:
                    raise exceptions.PlatformException(
                        error='400',
                        message='More than one file found by the name of: {}'.format(package_name))
                package = packages[0]
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='Checked out not found, must provide either package id or package name')
        else:
            package = entities.Package.from_json(_json={'id': package_id,
                                                        'name': package_name},
                                                 client_api=self._client_api,
                                                 project=self._project,
                                                 is_fetched=False)

        if checkout:
            self.checkout(package=package)
        return package

    def list(self, name=None, creator=None):
        """
        List project packages
        :return:
        """
        url = '/packages'
        query_params = {
            'name': name,
            'creator': creator
        }

        if self._project is not None:
            query_params['projects'] = self._project.id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        # return packages list
        packages = miscellaneous.List()
        for package in response.json()['items']:
            packages.append(entities.Package.from_json(client_api=self._client_api,
                                                       _json=package,
                                                       project=self._project))
        return packages

    def pull(self, package, version=None, local_path=None, project_id=None):
        """
        :param project_id:
        :param version:
        :param package:
        :param local_path:
        :return:
        """
        if self._project is None:
            if package is not None and package.project is not None:
                self._project = package.project
            else:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=project_id,
                                                                                       fetch=None)
        dir_version = version
        if version is None:
            dir_version = package.version

        if local_path is None:
            local_path = os.path.join(
                os.path.expanduser("~"),
                ".dataloop",
                "projects",
                self._project.name,
                "packages",
                package.name,
                str(dir_version))

        if version is None or version == package.version:
            codebase_id = package.codebase_id
        else:
            versions = [revision for revision in package.revisions if revision['version'] == version]
            if len(versions) <= 0:
                raise exceptions.PlatformException('404', 'Version not found: version={}'.format(version))
            elif len(versions) > 1:
                raise exceptions.PlatformException('404', 'More than one version found: version={}'.format(version))
            codebase_id = versions[0]['codebaseId']

        self._project.codebases.unpack(codebase_id=codebase_id, local_path=local_path)

        return local_path

    def push(self, codebase_id=None, src_path=None, package_name=None, modules=None, checkout=False):
        """
        Push local package

        :param checkout:
        :param codebase_id:
        :param src_path:
        :param package_name:
        :param modules:
        :return:
        """
        # get project
        if self._project is None:
            raise exceptions.PlatformException('400', 'Repository does not have project. Please checkout a project,'
                                                      'or create package from a project packages repository')

        # source path
        if src_path is None:
            if codebase_id is None:
                src_path = os.getcwd()
                logger.warning('No src_path is given, getting package information from cwd: {}'.format(src_path))

        # get package json
        package_from_json = dict()
        if assets.paths.PACKAGE_FILENAME in os.listdir(src_path):
            with open(os.path.join(src_path, assets.paths.PACKAGE_FILENAME), 'r') as f:
                package_from_json = json.load(f)

        # get name
        if package_name is None:
            package_name = package_from_json.get('name', 'default_package')

        if modules is None and 'modules' in package_from_json:
            modules = package_from_json['modules']

        # get or create codebase
        if codebase_id is None:
            codebase_id = self._project.codebases.pack(directory=src_path, name=package_name).id

        # check if exist
        packages = [package for package in self.list() if package.name == package_name]
        if len(packages) > 0:
            package = self._create(codebase_id=codebase_id,
                                   package_name=package_name,
                                   modules=modules,
                                   push=True,
                                   package=packages[0])
        else:
            package = self._create(codebase_id=codebase_id,
                                   package_name=package_name,
                                   modules=modules,
                                   push=False)
        if checkout:
            self.checkout(package=package)
        return package

    def _create(self,
                codebase_id=None,
                package_name=entities.DEFAULT_PACKAGE_NAME,
                modules=None,
                push=False,
                package=None):
        """
        Create a package in platform

        :param package:
        :param push:
        :param codebase_id: optional - package codebase
        :param package_name: optional - default: 'default package'
        :param modules: optional - PackageModules Entity
        :return: Package Entity
        """
        if push:
            package.codebase_id = codebase_id
            package.modules = modules
            return self.update(package=package)
        if modules is None:
            modules = [entities.DEFAULT_PACKAGE_MODULE]

        if not isinstance(modules, list):
            modules = [modules]

        if isinstance(modules[0], entities.PackageModule):
            modules = [module.to_json() for module in modules]

        payload = {'name': package_name,
                   'codebaseId': codebase_id,
                   'modules': modules}

        if self._project is not None:
            payload['projectId'] = self._project.id
        else:
            raise exceptions.PlatformException('400', 'Repository must have a project to perform this action')

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/packages',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Package.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self._project)

    def delete(self, package=None, package_name=None, package_id=None):
        """
        Delete Package object

        :param package:
        :param package_name:
        :param package_id:
        :return: True
        """
        # get id and name
        if package_name is None or package_id is None:
            if package is None:
                package = self.get(package_id=package_id, package_name=package_name)
            package_id = package.id
            package_name = package.name

        # check if project exist
        project_exists = True
        if self._project is None:
            try:
                if package is not None and package.project is not None:
                    self._project = package.project
                else:
                    self._project = repositories.Projects(client_api=self._client_api).get(
                        project_id=package.project_id)
            except exceptions.NotFound:
                project_exists = False

        if project_exists:
            try:
                # create codebases repo
                codebases = repositories.Codebases(client_api=self._client_api, project=self._project)
                # get package codebases
                codebase_pages = codebases.list_versions(codebase_name=package_name)
                for codebase_page in codebase_pages:
                    for codebase in codebase_page:
                        codebase.delete()
            except exceptions.Forbidden:
                logger.debug('Failed to delete code-bases. Continue without')

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/packages/{}".format(package_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, package):
        """
        Update Package changes to platform

        :param package:
        :return: Package entity
        """
        assert isinstance(package, entities.Package)

        # payload
        payload = package.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/packages/{}'.format(package.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Package.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self._project)

    def deploy(self,
               package_id=None,
               package_name=None,
               package=None,
               service_name=None,
               revision=None,
               init_input=None,
               runtime=None,
               sdk_version=None,
               agent_versions=None,
               bot=None,
               pod_type=None,
               verify=True,
               checkout=False,
               module_name=None,
               **kwargs):
        """
        Deploy package

        :param module_name:
        :param checkout:
        :param pod_type:
        :param bot:
        :param init_input:
        :param verify:
        :param agent_versions: - dictionary - - optional -versions of sdk, agent runner and agent proxy
        :param sdk_version:  - optional - string - sdk version
        :param runtime:
        :param revision:
        :param service_name:
        :param package:
        :param package_id:
        :param package_name:
        :return:
        """

        if package is None:
            package = self.get(package_id=package_id, package_name=package_name)

        return package.services.deploy(package=package,
                                       service_name=service_name,
                                       revision=revision,
                                       init_input=init_input,
                                       runtime=runtime,
                                       sdk_version=sdk_version,
                                       agent_versions=agent_versions,
                                       pod_type=pod_type,
                                       bot=bot,
                                       verify=verify,
                                       module_name=module_name,
                                       checkout=checkout,
                                       jwt_forward=kwargs.get('jwt_forward', None),
                                       is_global=kwargs.get('is_global', None))

    @staticmethod
    def generate(name=None, src_path=None):
        """
        Generate new package environment

        :return:
        """
        # name
        if name is None:
            name = 'default_package'

        # src path
        if src_path is None:
            src_path = os.getcwd()

        with open(assets.paths.ASSETS_PACKAGE_FILEPATH, 'r') as f:
            package_asset = json.load(f)

        package_asset['name'] = name

        with open(os.path.join(src_path, assets.paths.PACKAGE_FILENAME), 'w') as f:
            json.dump(package_asset, f, indent=2)

        copyfile(assets.paths.ASSETS_GITIGNORE_FILEPATH, os.path.join(src_path, '.gitignore'))
        copyfile(assets.paths.ASSETS_MOCK_FILEPATH, os.path.join(src_path, assets.paths.MOCK_FILENAME))
        copyfile(assets.paths.ASSETS_MAIN_FILEPATH, os.path.join(src_path, assets.paths.MAIN_FILENAME))

        with open(assets.paths.ASSETS_SERVICE_FILEPATH, 'r') as f:
            service_json = json.load(f)
        service_json = service_json[0]
        service_json['packageName'] = name
        with open(os.path.join(src_path, assets.paths.SERVICE_FILENAME), 'w')as f:
            json.dump(service_json, f, indent=2)

        logger.info('Successfully generated package')

    @staticmethod
    def is_multithread(inputs):
        is_multi = False
        if len(inputs) > 0 and isinstance(inputs[0], list):
            is_multi = True

        if is_multi:
            for single_input in inputs:
                if not isinstance(single_input, list):
                    raise exceptions.PlatformException('400', 'mock.json inputs can be either list of dictionaries '
                                                              'or list of lists')

        return is_multi

    def test_local_package(self, cwd=None, concurrency=None, module_name='default_module', function_name='run',
                           entry_point='main.py'):
        """
        Test local package
        :return:
        """
        if cwd is None:
            cwd = os.getcwd()

        with open(os.path.join(cwd, assets.paths.MOCK_FILENAME), 'r') as f:
            mock_json = json.load(f)
        is_multithread = self.is_multithread(inputs=mock_json['inputs'])

        local_runner = LocalServiceRunner(self._client_api,
                                          packages=self,
                                          cwd=cwd,
                                          multithreading=is_multithread,
                                          concurrency=concurrency,
                                          module_name=module_name,
                                          function_name=function_name,
                                          entry_point=entry_point)

        if self._project is None:
            try:
                project = repositories.Projects(client_api=self._client_api).get()
            except Exception:
                project = None
        else:
            project = self.project

        return local_runner.run_local_project(project=project)

    def __get_from_cache(self):
        package = self._client_api.state_io.get('package')
        if package is not None:
            package = entities.Package.from_json(_json=package, client_api=self._client_api, project=self._project)
        return package

    def checkout(self, package=None, package_id=None, package_name=None):
        """
        Checkout as package

        :param package_id:
        :param package:
        :param package_name:
        :return:
        """
        if package is None:
            package = self.get(package_id=package_id, package_name=package_name)
        self._client_api.state_io.put('package', package.to_json())
        logger.info("Checked out to package {}".format(package.name))


class LocalServiceRunner:
    """
    Service Runner Class
    """

    def __init__(self, client_api, packages, cwd=None, multithreading=False, concurrency=32, module_name=None,
                 function_name='run', entry_point='main.py'):
        if cwd is None:
            self.cwd = os.getcwd()
        else:
            self.cwd = cwd

        self._client_api = client_api
        self._packages = packages
        self.package_io = PackageIO(cwd=self.cwd)
        self.multithreading = multithreading
        self.concurrency = concurrency
        self.module_name = module_name
        self.function_name = function_name
        self.entry_point = entry_point

        with open(os.path.join(self.cwd, 'mock.json'), 'r') as f:
            self.mock_json = json.load(f)

    def validate_mock(self, mock_json):
        """
        Validate mock
        :param mock_json:
        :return:
        """
        self.function_name = mock_json.get('function_name', self.function_name)
        self.module_name = mock_json.get('module_name', self.module_name)

    # noinspection PyUnresolvedReferences
    def get_mainpy_run_service(self):
        """
        Get mainpy run service
        :return:
        """
        # noinspection PyUnresolvedReferences
        entry_point = self.mock_json.get('entry_point', self.entry_point)
        entry_point = os.path.join(self.cwd, entry_point)
        spec = importlib.util.spec_from_file_location("ServiceRunner", entry_point)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        service_runner = foo.ServiceRunner
        kwargs = self.mock_json.get('init_params', dict())
        return service_runner(**kwargs)

    def run_local_project(self, project=None):
        self.validate_mock(mock_json=self.package_io.read_json())
        package_runner = self.get_mainpy_run_service()

        modules = self.package_io.get('modules')
        if isinstance(modules, list) and len(modules) > 0:
            module = [module for module in modules if module['name'] == self.module_name][0]
        else:
            module = entities.DEFAULT_PACKAGE_MODULE.to_json()
        if isinstance(module['functions'], list) and len(module['functions']) > 0:
            func = [func for func in module['functions'] if func['name'] == self.function_name][0]
        else:
            func = entities.PackageFunction(None, list(), list(), None).to_json()
        package_inputs = func['input']
        if not self.multithreading:
            kwargs = dict()
            progress = utilities.Progress()
            kwargs['progress'] = progress
            for package_input in package_inputs:
                kwargs[package_input['name']] = self.get_field(field_name=package_input['name'],
                                                               field_type=package_input['type'],
                                                               project=project, mock_json=self.mock_json)

            results = getattr(package_runner, self.function_name)(**kwargs)
        else:
            pool = ThreadPool(processes=self.concurrency)
            inputs = self.mock_json['inputs']
            results = list()
            jobs = list()
            for single_input in inputs:
                kwargs = dict()
                progress = utilities.Progress()
                kwargs['progress'] = progress
                for package_input in package_inputs:
                    kwargs[package_input['name']] = self.get_field(field_name=package_input['name'],
                                                                   field_type=package_input['type'],
                                                                   project=project,
                                                                   mock_json=self.mock_json,
                                                                   mock_inputs=single_input)
                jobs.append(
                    pool.apply_async(
                        func=getattr(package_runner, self.function_name),
                        kwds=kwargs
                    )
                )
            for job in jobs:
                job.wait()
                results.append(job.get())

        return results

    def get_dataset(self, resource_id, project=None):
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

        if project is not None:
            datasets = project.datasets
        else:
            datasets = repositories.Datasets(client_api=self._client_api)

        return datasets.get(dataset_id=dataset_id)

    def get_item(self, resource_id, project=None):
        """
        Get item
        :param project:
        :param resource_id:
        :return: Item entity
        """
        if project is not None:
            items = project.items
        else:
            items = repositories.Items(client_api=self._client_api)

        return items.get(item_id=resource_id['item_id'])

    def get_annotation(self, resource_id, project=None):
        """
        Get annotation
        :param project:
        :param resource_id:
        :return: Annotation entity
        """
        item = self.get_item(project=project, resource_id=resource_id)
        return item.annotations.get(annotation_id=resource_id['annotation_id'])

    def get_field(self, field_name, field_type, mock_json, project=None, mock_inputs=None):
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
            return self.get_dataset(project=project, resource_id=resource_id)

        elif field_type == 'Item':
            return self.get_item(project=project, resource_id=resource_id)

        elif field_type == 'Annotation':
            return self.get_annotation(project=project, resource_id=resource_id)

        elif field_type == 'Json':
            return mock_input['value']

        else:
            raise exceptions.PlatformException('400', 'Unknown resource type for field {}'.format(field_name))


class PackageIO:

    def __init__(self, cwd=None):
        if cwd is None:
            cwd = os.getcwd()

        self.package_file_path = os.path.join(cwd, assets.paths.PACKAGE_FILENAME)
        self.service_file_path = os.path.join(cwd, assets.paths.SERVICE_FILENAME)

    def read_json(self, resource='packages'):
        if resource == 'package':
            file_path = self.package_file_path
        else:
            file_path = self.service_file_path

        with open(file_path, 'r') as fp:
            cfg = json.load(fp)
        return cfg

    def get(self, key, resource='package'):
        cfg = self.read_json(resource=resource)
        return cfg[key]

    def put(self, key, value, resource='package'):
        try:
            cfg = self.read_json(resource=resource)
            cfg[key] = value

            if resource == 'package':
                file_path = self.package_file_path
            else:
                file_path = self.service_file_path

            with open(file_path, 'w') as fp:
                json.dump(cfg, fp, indent=2)
        except Exception:
            pass
