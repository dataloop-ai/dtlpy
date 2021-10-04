import os
from collections import namedtuple
from typing import Union
import logging
import traceback
import attr
import json

from .. import repositories, entities, exceptions, services

logger = logging.getLogger(name=__name__)


@attr.s
class Package(entities.BaseEntity):
    """
    Package object
    """
    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    version = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    name = attr.ib()
    codebase = attr.ib()
    _modules = attr.ib()
    slots = attr.ib(type=list)
    ui_hooks = attr.ib()
    creator = attr.ib()
    is_global = attr.ib()
    type = attr.ib()
    service_config = attr.ib()
    # name change
    project_id = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _revisions = attr.ib(default=None, repr=False)
    _repositories = attr.ib(repr=False)
    _artifacts = attr.ib(default=None)
    _codebases = attr.ib(default=None)

    @property
    def modules(self):
        return self._modules

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

    @modules.setter
    def modules(self, modules: list):
        if not self.unique_modules(modules):
            raise Exception('Cannot have 2 modules by the same name in one package.')
        if not isinstance(modules, list):
            raise Exception('Package modules must be a list.')
        self._modules = modules

    @staticmethod
    def unique_modules(modules: list):
        return len(modules) == len(set([module.name for module in modules]))

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
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
    def from_json(cls, _json, client_api, project, is_fetched=True):
        """
        Turn platform representation of package into a package entity

        :param _json: platform representation of package
        :param client_api: ApiClient entity
        :param project: project entity
        :param is_fetched: is Entity fetched from Platform
        :return: Package entity
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Package has been fetched from a project that is not belong to it')
                project = None

        modules = [entities.PackageModule.from_json(_module) for _module in _json.get('modules', list())]
        slots = [entities.PackageSlot.from_json(_slot) for _slot in _json.get('slots', list())]
        if 'codebase' in _json:
            codebase = entities.Codebase.from_json(_json=_json['codebase'],
                                                   client_api=client_api)
        else:
            codebase = None

        inst = cls(
            project_id=_json.get('projectId', None),
            codebase=codebase,
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            is_global=_json.get('global', None),
            client_api=client_api,
            modules=modules,
            slots=slots,
            ui_hooks=_json.get('uiHooks', None),
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            id=_json.get('id', None),
            service_config=_json.get('serviceConfig', None),
            type=_json.get('type', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Package entity into a platform representation of Package

        :return: platform json of package
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Package)._project,
                                                        attr.fields(Package)._repositories,
                                                        attr.fields(Package)._artifacts,
                                                        attr.fields(Package)._codebases,
                                                        attr.fields(Package)._client_api,
                                                        attr.fields(Package)._revisions,
                                                        attr.fields(Package).project_id,
                                                        attr.fields(Package)._modules,
                                                        attr.fields(Package).slots,
                                                        attr.fields(Package).is_global,
                                                        attr.fields(Package).ui_hooks,
                                                        attr.fields(Package).codebase,
                                                        attr.fields(Package).service_config,
                                                        ))

        modules = self.modules
        # check in inputs is a list
        if not isinstance(modules, list):
            modules = [modules]
        # if is dtlpy entity convert to dict
        if modules and isinstance(modules[0], entities.PackageModule):
            modules = [module.to_json() for module in modules]
        _json['modules'] = modules

        slot = [slot.to_json() for slot in self.slots]
        if len(slot) > 0:
            _json['slots'] = slot
        _json['projectId'] = self.project_id
        if self.is_global is not None:
            _json['global'] = self.is_global
        if self.codebase is not None:
            _json['codebase'] = self.codebase.to_json()
        if self.ui_hooks is not None:
            _json['uiHooks'] = self.ui_hooks
        if self.service_config is not None:
            _json['serviceConfig '] = self.service_config

        return _json

    ############
    # entities #
    ############
    @property
    def revisions(self):
        if self._revisions is None:
            self._revisions = self.packages.revisions(package=self)
        return self._revisions

    @property
    def project(self):
        if self._project is None:
            self._project = self.projects.get(project_id=self.project_id, fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['executions', 'services', 'projects', 'packages'])

        r = reps(executions=repositories.Executions(client_api=self._client_api, project=self._project),
                 services=repositories.Services(client_api=self._client_api, package=self, project=self._project,
                                                project_id=self.project_id),
                 projects=repositories.Projects(client_api=self._client_api),
                 packages=repositories.Packages(client_api=self._client_api, project=self._project))
        return r

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
        if self._codebases is None:
            self._codebases = repositories.Codebases(
                client_api=self._client_api,
                project=self._project,
                project_id=self.project_id
            )
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    @property
    def artifacts(self):
        if self._artifacts is None:
            self._artifacts = repositories.Artifacts(
                client_api=self._client_api,
                project=self._project,
                project_id=self.project_id
            )
        assert isinstance(self._artifacts, repositories.Artifacts)
        return self._artifacts

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
               **kwargs):
        """
        Deploy package

        :param max_attempts: Maximum execution retries in-case of a service reset
        :param on_reset:
        :param drain_time:
        :param execution_timeout:
        :param run_execution_as_process:
        :param module_name:
        :param pod_type:
        :param bot:
        :param verify:
        :param force: optional - terminate old replicas immediately
        :param agent_versions:
        :param sdk_version:
        :param runtime:
        :param init_input:
        :param revision:
        :param service_name:
        :return:
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
                                            is_global=kwargs.get('is_global', None))

    def checkout(self):
        """
        Checkout as package

        :return:
        """
        return self.packages.checkout(package=self)

    def delete(self):
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
             ):
        """
         Push local package

        :param codebase: PackageCode object - defines how to store the package code
        :param checkout: save package to local checkout
        :param src_path: location of pacjage codebase folder to zip
        :param package_name: name of package
        :param modules: list of PackageModule
        :param revision_increment: optional - str - version bumping method - major/minor/patch - default = None
        :param  service_update: optional - bool - update the service
        :param  service_config: optional - json of service - a service that have config from the main service if wanted

        :return:
        """
        return self.project.packages.push(
            package_name=package_name if package_name is not None else self.name,
            modules=modules if modules is not None else self.modules,
            revision_increment=revision_increment,
            codebase=codebase,
            src_path=src_path,
            checkout=checkout,
            service_update=service_update,
            service_config=service_config

        )

    def pull(self, version=None, local_path=None):
        """
        Push local package

        :param version:
        :param local_path:
        :return:
        """
        return self.packages.pull(package=self,
                                  version=version,
                                  local_path=local_path)

    def open_in_web(self):
        """
        Open the package in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def test(self,
             cwd=None,
             concurrency=None,
             module_name=entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME,
             function_name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
             class_name=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME,
             entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT
             ):
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
