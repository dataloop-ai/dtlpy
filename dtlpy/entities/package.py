from collections import namedtuple
from typing import Union
from enum import Enum
import traceback
import logging
import inspect
import typing
import json
import os

from .package_module import PackageModule
from .package_slot import PackageSlot
from .. import repositories, entities, exceptions
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class RequirementOperator(str, Enum):
    EQUAL = '==',
    GREATER_THAN = '>',
    LESS_THAN = '<',
    EQUAL_OR_LESS_THAN = '<=',
    EQUAL_OR_GREATER_THAN = '>='

    @staticmethod
    def keys():
        return [key.value for key in list(RequirementOperator)]


class PackageRequirement:

    def __init__(self, name: str, version: str = None, operator: str = None):
        self.name = name
        self.version = version

        valid_operators = RequirementOperator.keys()
        if operator is not None and operator not in valid_operators:
            raise Exception('Illegal operator: {}. Please select from: {}'.format(operator, valid_operators))

        self.operator = operator

    def to_json(self):
        _json = {'name': self.name}
        if self.version is not None:
            _json['version'] = self.version
        if self.operator is not None:
            _json['operator'] = self.operator
        return _json

    @classmethod
    def from_json(cls, _json: dict):
        return cls(**_json)


class Package(entities.DlEntity):
    """
    Package object
    """
    # platform
    id: str = entities.DlProperty(location=['id'], _type=str)
    url: str = entities.DlProperty(location=['url'], _type=str)
    name: str = entities.DlProperty(location=['name'], _type=str)
    version: str = entities.DlProperty(location=['version'], _type=str)
    created_at: str = entities.DlProperty(location=['createdAt'], _type=str)
    updated_at: str = entities.DlProperty(location=['updatedAt'], _type=str)
    project_id: str = entities.DlProperty(location=['projectId'], _type=str)
    creator: str = entities.DlProperty(location=['creator'], _type=str)
    type: str = entities.DlProperty(location=['type'], _type=str)
    metadata: dict = entities.DlProperty(location=['metadata'], _type=dict)
    ui_hooks: list = entities.DlProperty(location=['uiHooks'], _type=str)
    service_config: dict = entities.DlProperty(location=['serviceConfig'], _type=str)
    is_global: bool = entities.DlProperty(location=['global'], _type=str)

    codebase: typing.Any = entities.DlProperty(location=['codebase'], _kls='Codebase')
    modules: typing.List[PackageModule] = entities.DlProperty(location=['modules'], _kls='PackageModule')
    slots: typing.Union[typing.List[PackageSlot], None] = entities.DlProperty(location=['slots'],
                                                                              _kls='PackageSlot')
    requirements: typing.Union[typing.List[PackageRequirement], None] = entities.DlProperty(location=['requirements'],
                                                                                            _kls='PackageRequirement')

    # sdk
    _client_api: ApiClient
    _revisions = None
    __repositories = None
    _project = None

    def __repr__(self):
        # TODO need to move to DlEntity
        return "Package(id={id}, name={name}, creator={creator}, project_id={project_id}, type={type}, version={version})".format(
            id=self.id,
            name=self.name,
            version=self.version,
            type=self.type,
            project_id=self.project_id,
            creator=self.creator)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def revisions(self):
        if self._revisions is None:
            self._revisions = self.packages.revisions(package=self)
        return self._revisions

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/packages/{}/main".format(self.project.id, self.id))

    @property
    def codebase_id(self):
        if self.codebase is not None and self.codebase.type == entities.PackageCodebaseType.ITEM:
            return self.codebase.item_id
        return None

    @codebase_id.setter
    def codebase_id(self, item_id: str):
        self.codebase = entities.ItemCodebase(item_id=item_id)

    @staticmethod
    def _protected_from_json(_json, client_api, project=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json:  platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            package = Package.from_json(_json=_json,
                                        client_api=client_api,
                                        project=project,
                                        is_fetched=is_fetched)
            status = True
        except Exception:
            package = traceback.format_exc()
            status = False
        return status, package

    @classmethod
    def from_json(cls, _json, client_api, project=None, is_fetched=True):
        """
        Turn platform representation of package into a package entity

        :param dict _json: platform representation of package
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.project.Project project: project entity
        :param is_fetched: is Entity fetched from Platform
        :return: Package entity
        :rtype: dtlpy.entities.package.Package
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Package has been fetched from a project that is not belong to it')
                project = None
        # Entity
        inst = cls(_dict=_json)
        # Platform
        inst._project = project
        inst._client_api = client_api
        inst.is_fetched = is_fetched

        return inst

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
        :rtype: dict
        """
        _json = self._dict.copy()
        return _json

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self._project = self.projects.get(project_id=self.project_id, fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        assert isinstance(self._project, entities.Project), "Unknwon 'project' type: {}".format(type(project))
        self._project = project

    ################
    # repositories #
    ################
    @property
    def _repositories(self):
        if self.__repositories is None:
            reps = namedtuple('repositories',
                              field_names=['executions', 'services', 'projects', 'packages', 'artifacts', 'codebases',
                                           'models'])

            self.__repositories = reps(
                executions=repositories.Executions(client_api=self._client_api,
                                                   project=self._project),
                services=repositories.Services(client_api=self._client_api,
                                               package=self,
                                               project=self._project,
                                               project_id=self.project_id),
                projects=repositories.Projects(client_api=self._client_api),
                packages=repositories.Packages(client_api=self._client_api,
                                               project=self._project),
                artifacts=repositories.Artifacts(client_api=self._client_api,
                                                 project=self._project,
                                                 project_id=self.project_id,
                                                 package=self),
                codebases=repositories.Codebases(client_api=self._client_api, project=self._project,
                                                 project_id=self.project_id),
                models=repositories.Models(client_api=self._client_api,
                                           project=self._project,
                                           package=self,
                                           project_id=self.project_id)
            )
        return self.__repositories

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def packages(self):
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    @property
    def codebases(self):
        assert isinstance(self._repositories.codebases, repositories.Codebases)
        return self._repositories.codebases

    @property
    def artifacts(self):
        assert isinstance(self._repositories.artifacts, repositories.Artifacts)
        return self._repositories.artifacts

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    ##############
    # properties #
    ##############
    @property
    def git_status(self):
        status = 'Git status unavailable'
        try:
            if self.codebase.type == entities.PackageCodebaseType.ITEM:
                if 'git' in self.codebase.item.metadata:
                    status = self.codebase.item.metadata['git'].get('status', status)
        except Exception:
            logging.debug('Error getting codebase')
        return status

    @property
    def git_log(self):
        log = 'Git log unavailable'
        try:
            if self.codebase.type == entities.PackageCodebaseType.ITEM:
                if 'git' in self.codebase.item.metadata:
                    log = self.codebase.item.metadata['git'].get('log', log)
        except Exception:
            logging.debug('Error getting codebase')
        return log

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Package changes to platform

        :return: Package entity
        """
        return self.packages.update(package=self)

    def deploy(self,
               service_name=None,
               revision=None,
               init_input=None,
               runtime=None,
               sdk_version=None,
               agent_versions=None,
               verify=True,
               bot=None,
               pod_type=None,
               module_name=None,
               run_execution_as_process=None,
               execution_timeout=None,
               drain_time=None,
               on_reset=None,
               max_attempts=None,
               force=False,
               secrets: list = None,
               **kwargs):
        """
        Deploy package

        :param str service_name: service name
        :param str revision: package revision - default=latest
        :param init_input: config to run at startup
        :param dict runtime: runtime resources
        :param str sdk_version:  - optional - string - sdk version
        :param dict agent_versions: - dictionary - - optional -versions of sdk, agent runner and agent proxy
        :param str bot: bot email
        :param str pod_type: pod type dl.InstanceCatalog
        :param bool verify: verify the inputs
        :param str module_name: module name
        :param bool run_execution_as_process: run execution as process
        :param int execution_timeout: execution timeout
        :param int drain_time: drain time
        :param str on_reset: on reset
        :param int max_attempts: Maximum execution retries in-case of a service reset
        :param bool force: optional - terminate old replicas immediately
        :param list secrets: list of the integrations ids
        :return: Service object
        :rtype: dtlpy.entities.service.Service

        **Example**:

        .. code-block:: python
        service: dl.Service = package.deploy(service_name=package_name,
                                             execution_timeout=3 * 60 * 60,
                                             module_name=module.name,
                                             runtime=dl.KubernetesRuntime(
                                                 concurrency=10,
                                                 pod_type=dl.InstanceCatalog.REGULAR_S,
                                                 autoscaler=dl.KubernetesRabbitmqAutoscaler(
                                                     min_replicas=1,
                                                     max_replicas=20,
                                                     queue_length=20
                                                 )
                                             )
                                             )

        """
        return self.project.packages.deploy(package=self,
                                            service_name=service_name,
                                            project_id=self.project_id,
                                            revision=revision,
                                            init_input=init_input,
                                            runtime=runtime,
                                            sdk_version=sdk_version,
                                            agent_versions=agent_versions,
                                            pod_type=pod_type,
                                            bot=bot,
                                            verify=verify,
                                            module_name=module_name,
                                            run_execution_as_process=run_execution_as_process,
                                            execution_timeout=execution_timeout,
                                            drain_time=drain_time,
                                            on_reset=on_reset,
                                            max_attempts=max_attempts,
                                            force=force,
                                            jwt_forward=kwargs.get('jwt_forward', None),
                                            is_global=kwargs.get('is_global', None),
                                            secrets=secrets)

    def checkout(self):
        """
        Checkout as package

        :return:
        """
        return self.packages.checkout(package=self)

    def delete(self) -> bool:
        """
        Delete Package object

        :return: True
        """
        return self.packages.delete(package=self)

    def push(self,
             codebase: Union[entities.GitCodebase, entities.ItemCodebase] = None,
             src_path: str = None,
             package_name: str = None,
             modules: list = None,
             checkout: bool = False,
             revision_increment: str = None,
             service_update: bool = False,
             service_config: dict = None,
             package_type='faas'
             ):
        """
        Push local package

        :param dtlpy.entities.codebase.Codebase codebase: PackageCode object - defines how to store the package code
        :param bool checkout: save package to local checkout
        :param str src_path: location of pacjage codebase folder to zip
        :param str package_name: name of package
        :param list modules: list of PackageModule
        :param str revision_increment: optional - str - version bumping method - major/minor/patch - default = None
        :param  bool service_update: optional - bool - update the service
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :param  str package_type: default is "faas", one of "app", "ml"
        :return: package entity
        :rtype: dtlpy.entities.package.Package
        
        **Example**:

        .. code-block:: python

            package = packages.push(package_name='package_name',
                                    modules=[module],
                                    version='1.0.0',
                                    src_path=os.getcwd())
        """
        return self.project.packages.push(
            package_name=package_name if package_name is not None else self.name,
            modules=modules if modules is not None else self.modules,
            revision_increment=revision_increment,
            codebase=codebase,
            src_path=src_path,
            checkout=checkout,
            service_update=service_update,
            service_config=service_config,
            package_type=package_type
        )

    def pull(self, version=None, local_path=None) -> str:
        """
        Pull local package

        :param str version: version
        :param str local_path: local path

        **Example**:

        .. code-block:: python

            path = package.pull(local_path='local_path')
        """
        return self.packages.pull(package=self,
                                  version=version,
                                  local_path=local_path)

    def build(self, module_name=None, init_inputs=None, local_path=None, from_local=None):
        """
        Instantiate a module from the package code. Returns a loaded instance of the runner class

        :param module_name: Name of the module to build the runner class
        :param str init_inputs: dictionary of the class init variables (if exists). will be used to init the module class
        :param str local_path: local path of the package (if from_local=False - codebase will be downloaded)
        :param bool from_local: bool. if true - codebase will not be downloaded (only use local files)
        :return: dl.BaseServiceRunner
        """
        return self.packages.build(package=self,
                                   module_name=module_name,
                                   local_path=local_path,
                                   init_inputs=init_inputs,
                                   from_local=from_local)

    def open_in_web(self):
        """
        Open the package in web platform

        """
        url = self._client_api._get_resource_url(
            f"projects/{self.project.id}/faas?byCreator=false&byProject=true&byDataloop=false&tab=library&name={self.name}")
        self._client_api._open_in_web(url=url)

    def test(self,
             cwd=None,
             concurrency=None,
             module_name=entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME,
             function_name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
             class_name=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME,
             entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT
             ):
        """
        Test local package in local environment.

        :param str cwd: path to the file
        :param int concurrency: the concurrency of the test
        :param str module_name: module name
        :param str function_name: function name
        :param str class_name: class name
        :param str entry_point: the file to run like main.py
        :return: list created by the function that tested the output
        :rtype: list

        **Example**:

        .. code-block:: python

            package.test(cwd='path_to_package',
                        function_name='run')
        """
        return self.project.packages.test_local_package(
            cwd=cwd,
            concurrency=concurrency,
            package=self,
            module_name=module_name,
            function_name=function_name,
            class_name=class_name,
            entry_point=entry_point
        )

    @staticmethod
    def _mockify_input(input_type):
        _json = dict()
        if input_type == 'Dataset':
            _json.update({'dataset_id': 'id'})
        if input_type == 'Item':
            _json.update({'item_id': 'id', 'dataset_id': 'id'})
        if input_type == 'Annotation':
            _json.update({'annotation_id': 'id', 'item_id': 'id', 'dataset_id': 'id'})
        return _json

    def mockify(self, local_path=None, module_name=None, function_name=None):
        if local_path is None:
            local_path = os.getcwd()

        if module_name is None:
            if self.modules:
                module_name = self.modules[0].name
            else:
                raise exceptions.PlatformException('400', 'Package has no modules')

        modules = [module for module in self.modules if module.name == module_name]
        if not modules:
            raise exceptions.PlatformException('404', 'Module not found: {}'.format(module_name))
        module = modules[0]

        if function_name is None:
            funcs = [func for func in module.functions]
            if funcs:
                func = funcs[0]
            else:
                raise exceptions.PlatformException('400', 'Module: {} has no functions'.format(module_name))
        else:
            funcs = [func for func in module.functions if func.name == function_name]
            if not funcs:
                raise exceptions.PlatformException('404', 'Function not found: {}'.format(function_name))
            func = funcs[0]

        mock = dict()
        for module in self.modules:
            mock['module_name'] = module.name
            mock['function_name'] = func.name
            mock['init_params'] = {inpt.name: self._mockify_input(input_type=inpt.type) for inpt in module.init_inputs}
            mock['inputs'] = [{'name': inpt.name, 'value': self._mockify_input(input_type=inpt.type)} for inpt in
                              func.inputs]

        with open(os.path.join(local_path, 'mock.json'), 'w') as f:
            json.dump(mock, f)

    @staticmethod
    def get_ml_metadata(cls=None,
                        available_methods=None,
                        output_type=entities.AnnotationType.CLASSIFICATION,
                        input_type='image',
                        default_configuration: dict = None):
        """
        Create ML metadata for the package
        :param cls: ModelAdapter class, to get the list of available_methods
        :param available_methods: available user function on the adapter.  ['load', 'save', 'predict', 'train']
        :param output_type: annotation type the model create, e.g. dl.AnnotationType.CLASSIFICATION
        :param input_type: input file type the model gets, one of ['image', 'video', 'txt']
        :param default_configuration: default service configuration for the deployed services
        :return:
        """
        user_implemented_methods = ['load', 'save', 'predict', 'train']
        if available_methods is None:
            # default
            available_methods = user_implemented_methods

        if cls is not None:
            # TODO dont check if function is on the adapter - check if the functions is implemented (not raise NotImplemented)
            available_methods = [
                {name: 'BaseModelAdapter' not in getattr(cls, name).__qualname__}
                for name in user_implemented_methods
            ]
        if default_configuration is None:
            default_configuration = dict()
        metadata = {
            'system': {'ml': {'defaultConfiguration': default_configuration,
                              'outputType': output_type,
                              'inputType': input_type,
                              'supportedMethods': available_methods
                              }}}
        return metadata

    class decorators:
        @staticmethod
        def module(name='default-module', description='', init_inputs=None):
            def wrapper(cls: typing.Callable):
                # package_module_dict = package_module.to_json()
                package_module_dict = {"name": name,
                                       "description": description,
                                       "functions": list(),
                                       "className": cls.__name__}
                if init_inputs is not None:
                    package_module_dict.update(initInputs=Package.decorators.parse_io(io_list=init_inputs))
                for member_name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
                    spec = getattr(member, '__dtlpy__', None)
                    if spec is not None:
                        package_module_dict["functions"].append(spec)
                cls.__dtlpy__ = package_module_dict
                return cls

            return wrapper

        @staticmethod
        def function(display_name=None, inputs=None, outputs=None):
            def wrapper(func: typing.Callable):
                if display_name is None:
                    d_name = func.__name__
                else:
                    d_name = display_name
                func.__dtlpy__ = {"name": func.__name__,
                                  "displayName": d_name,
                                  "input": Package.decorators.parse_io(io_list=inputs),
                                  "output": Package.decorators.parse_io(io_list=outputs)}
                return func

            return wrapper

        @staticmethod
        def parse_io(io_list: dict):
            output = list()
            if io_list is not None:
                for io_name, io_type in io_list.items():
                    if isinstance(io_type, Enum):
                        io_type = io_type.name
                    if isinstance(io_type, type):
                        io_type = io_type.__name__
                    else:
                        io_type = str(io_type)
                    output.append({"name": io_name,
                                   "type": str(io_type)})
            return output
