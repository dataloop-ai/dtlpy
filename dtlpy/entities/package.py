from collections import namedtuple
import logging
import attr
import json

from .. import miscellaneous, repositories, entities, exceptions, services

logger = logging.getLogger(name=__name__)


@attr.s
class Package:
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

    # name change
    project_id = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project):
        """
        Turn platform representation of package into a package entity

        :param _json: platform representation of package
        :param client_api:
        :param project:
        :return: Package entity
        """
        modules = [entities.PackageModule.from_json(_module) for _module in _json.get('modules', list())]
        return cls(
            project_id=_json.get('projectId', None),
            codebase_id=_json.get('codebaseId', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            revisions=_json.get('revisions', None),
            version=_json.get('version', None),
            client_api=client_api,
            modules=modules,
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            id=_json.get('id', None)
        )

    @classmethod
    def dummy(cls, package_id, client_api):
        """
        Turn dummy platform representation of package into a package entity

        :param package_id:
        :param client_api:
        :return: package entity
        """
        return cls(
            project_id=None,
            codebase_id=None,
            modules=None,
            createdAt=None,
            updatedAt=None,
            revisions=None,
            version=None,
            client_api=client_api,
            name=None,
            url=None,
            project=None,
            id=package_id
        )

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
            self.get_project()
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    def get_project(self, dummy=False):
        if self._project is None:
            if dummy:
                self._project = entities.Project.dummy(project_id=self.project_id, client_api=self._client_api)
            else:
                self._project = self.projects.get(project_id=self.project_id)

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['executions', 'services', 'projects', 'packages'])

        r = reps(executions=repositories.Executions(client_api=self._client_api, project=self._project),
                 services=repositories.Services(client_api=self._client_api, package=self, project=self._project),
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
    def print(self):
        """
        Prints Package entity

        :return:
        """
        miscellaneous.List([self]).print()

    def update(self):
        """
        Update Package changes to platform

        :return: Package entity
        """
        return self.packages.update(package=self)

    def deploy(self, service_name=None, revision=None, init_input=None, runtime=None, sdk_version=None,
               agent_versions=None, verify=True, bot=None, pod_type=None, module_name=None):
        """
        Deploy package

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
                                            revision=revision,
                                            init_input=init_input,
                                            runtime=runtime,
                                            sdk_version=sdk_version,
                                            agent_versions=agent_versions,
                                            pod_type=pod_type,
                                            bot=bot,
                                            verify=verify,
                                            module_name=module_name)

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


@attr.s
class PackageInput:
    INPUT_TYPES = ['Json', 'Dataset', 'Item', 'Annotation']
    type = attr.ib(type=str)
    value = attr.ib(default=None)
    name = attr.ib(type=str)

    @name.default
    def set_name(self):
        if self.type == 'Item':
            return 'item'
        elif self.type == 'Dataset':
            return 'dataset'
        elif self.type == 'Annotation':
            return 'annotation'
        else:
            return 'config'

    # noinspection PyUnusedLocal
    @name.validator
    def check_name(self, attribute, value):
        name_ok = True
        expected_name = 'Expected name for type {} is: '.format(self.type)
        if self.type == 'Item' and value != 'item':
            expected_name += 'item'
            name_ok = False
        elif self.type == 'Dataset' and value != 'dataset':
            expected_name += 'dataset'
            name_ok = False
        elif self.type == 'Annotation' and value != 'annotation':
            expected_name += 'dataset'
            name_ok = False

        if not name_ok:
            raise exceptions.PlatformException('400', 'Invalid input name. {}'.format(expected_name))

    # noinspection PyUnusedLocal
    @type.validator
    def check_type(self, attribute, value):
        if value not in self.INPUT_TYPES:
            raise exceptions.PlatformException('400',
                                               'Invalid input type please select from: {}'.format(self.INPUT_TYPES))

    @staticmethod
    def is_json_serializable(val):
        try:
            json.dumps(val)
            is_json_serializable = True
        except Exception:
            is_json_serializable = False
        return is_json_serializable

    # noinspection PyUnusedLocal
    @value.validator
    def check_value(self, attribute, value):
        value_ok = True
        expected_value = 'Expected value should be:'
        if self.type == 'Json':
            expected_value = '{} json serializable'.format(expected_value)
            if not self.is_json_serializable(value):
                value_ok = False
        elif self.type == 'Dataset':
            expected_value = '{} {{"dataset_id": <dataset id>}}'.format(expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'dataset_id' not in value:
                    value_ok = False
        elif self.type == 'Item':
            expected_value = '{} {{"dataset_id": <dataset id>, "item_id": <item id>}}'.format(expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'item_id' not in value:
                    value_ok = False
                if 'dataset_id' not in value:
                    value_ok = False
        elif self.type == 'Annotation':
            expected_value = '{} {{"dataset_id": <dataset id>, "item_id": <item id>, "annotation_id": <annotation id>}}'.format(
                expected_value)
            if not isinstance(value, dict):
                value_ok = False
            else:
                if 'item_id' not in value:
                    value_ok = False
                if 'dataset_id' not in value:
                    value_ok = False
                if 'annotation_id' not in value:
                    value_ok = False

        if not value_ok and value is not None:
            raise exceptions.PlatformException('400', 'Illegal value. {}'.format(expected_value))

    def to_json(self, resource='package'):
        if resource == 'package':
            _json = attr.asdict(self)
        elif resource == 'execution':
            _json = {
                self.name: self.value
            }
        else:
            raise exceptions.PlatformException('400', 'Please select resource from: package, execution')

        return _json

    @classmethod
    def from_json(cls, _json):
        return cls(
            type=_json.get('type', None),
            value=_json.get('value', None),
            name=_json.get('name', None)
        )
