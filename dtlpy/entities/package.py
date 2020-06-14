import os
from collections import namedtuple
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
    codebase_id = attr.ib()
    revisions = attr.ib(repr=False)
    modules = attr.ib()
    creator = attr.ib()

    # name change
    project_id = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param dataset:
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
        :param client_api:
        :param project:
        :param is_fetched: is Entity fetched from Platform
        :return: Package entity
        """
        modules = [entities.PackageModule.from_json(_module) for _module in _json.get('modules', list())]
        inst = cls(
            project_id=_json.get('projectId', None),
            codebase_id=_json.get('codebaseId', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            revisions=_json.get('revisions', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            client_api=client_api,
            modules=modules,
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            id=_json.get('id', None)
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
                                                        attr.fields(Package)._client_api,
                                                        attr.fields(Package).codebase_id,
                                                        attr.fields(Package).project_id,
                                                        attr.fields(Package).modules,
                                                        ))

        modules = self.modules
        # check in inputs is a list
        if not isinstance(modules, list):
            modules = [modules]
        # if is dtlpy entity convert to dict
        if modules and isinstance(modules[0], entities.PackageModule):
            modules = [module.to_json() for module in modules]

        _json['projectId'] = self.project_id
        _json['codebaseId'] = self.codebase_id
        _json['modules'] = modules
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

    ##############
    # properties #
    ##############
    @property
    def git_status(self):
        status = 'Git status unavailable'
        try:
            codebase = self.project.codebases.get(codebase_id=self.codebase_id, version=self.version - 1)
            if 'git' in codebase.metadata:
                status = codebase.metadata['git'].get('status', status)
        except Exception:
            logging.debug('Error getting codebase')
        return status

    @property
    def git_log(self):
        log = 'Git log unavailable'
        try:
            codebase = self.project.codebases.get(codebase_id=self.codebase_id, version=self.version - 1)
            if 'git' in codebase.metadata:
                log = codebase.metadata['git'].get('log', log)
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

    def deploy(self, service_name=None,
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
               **kwargs):
        """
        Deploy package

        :param on_reset:
        :param drain_time:
        :param execution_timeout:
        :param run_execution_as_process:
        :param module_name:
        :param pod_type:
        :param bot:
        :param verify:
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
        return self.project.packages.push(package_name=package_name if package_name is not None else self.name,
                                          codebase_id=codebase_id,
                                          src_path=src_path,
                                          modules=modules,
                                          checkout=checkout)

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
        self.packages.open_in_web(package=self)

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
            mock['config'] = {inpt.name: self._mockify_input(input_type=inpt.type) for inpt in module.init_inputs}
            mock['inputs'] = [{'name': inpt.name, 'value': self._mockify_input(input_type=inpt.type)} for inpt in
                              func.inputs]

        with open(os.path.join(local_path, 'mock.json'), 'w') as f:
            json.dump(mock, f)
