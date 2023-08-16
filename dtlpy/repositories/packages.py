import collections.abc
import importlib.util
import inspect
import logging
import hashlib
import typing
import json
import sys
import os
import re
from copy import deepcopy
from shutil import copyfile
from concurrent.futures import ThreadPoolExecutor

from .. import entities, repositories, exceptions, utilities, miscellaneous, assets, services, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')

DEFAULT_PACKAGE_METHOD = entities.PackageFunction(name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
                                                  description='',
                                                  inputs=[],
                                                  outputs=[])
DEFAULT_PACKAGE_MODULE = entities.PackageModule(init_inputs=list(),
                                                entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT,
                                                class_name=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME,
                                                name=entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME,
                                                functions=[DEFAULT_PACKAGE_METHOD])


class PackageCatalog:
    DEFAULT_PACKAGE_TYPE = 'default_package_type'
    MULTI_MODULE = 'multi_module'
    MULTI_MODULE_WITH_TRIGGER = 'multi_module_with_trigger'
    SINGLE_FUNCTION_ITEM = 'single_function_item'
    SINGLE_FUNCTION_JSON = 'single_function_json'
    SINGLE_FUNCTION_DATASET = 'single_function_dataset'
    SINGLE_FUNCTION_ANNOTATION = 'single_function_annotation'
    SINGLE_FUNCTION_NO_INPUT = 'single_function_no_input'
    SINGLE_FUNCTION_MULTI_INPUT = 'single_function_multi_input'
    MULTI_FUNCTION_ITEM = 'multi_function_item'
    MULTI_FUNCTION_DATASET = 'multi_function_dataset'
    MULTI_FUNCTION_ANNOTATION = 'multi_function_annotation'
    MULTI_FUNCTION_NO_INPUT = 'multi_function_no_input'
    MULTI_FUNCTION_JSON = 'multi_function_json'
    SINGLE_FUNCTION_ITEM_WITH_TRIGGER = 'single_function_item_with_trigger'
    SINGLE_FUNCTION_DATASET_WITH_TRIGGER = 'single_function_dataset_with_trigger'
    SINGLE_FUNCTION_ANNOTATION_WITH_TRIGGER = 'single_function_annotation_with_trigger'
    MULTI_FUNCTION_ITEM_WITH_TRIGGERS = 'multi_function_item_with_triggers'
    MULTI_FUNCTION_DATASET_WITH_TRIGGERS = 'multi_function_dataset_with_triggers'
    MULTI_FUNCTION_ANNOTATION_WITH_TRIGGERS = 'multi_function_annotation_with_triggers'
    CONVERTER_FUNCTION = 'converter'


class Packages:
    """
    Packages Repository

    The Packages class allows users to manage packages (code used for running in Dataloop's FaaS) and their properties.
    Read more about `Packages <https://developers.dataloop.ai/tutorials/faas/introduction/chapter/>`_.
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project
        self.package_io = PackageIO()

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self._client_api).get()
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "project". need to set a Project entity or use project.packages repository')
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/packages".format(self.project.id))

    def open_in_web(self,
                    package: entities.Package = None,
                    package_id: str = None,
                    package_name: str = None):
        """
        Open the package in the web platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package: package entity
        :param str package_id: package id
        :param str package_name: package name

        **Example**:

        .. code-block:: python

            project.packages.open_in_web(package_id='package_id')
        """
        if package_name is not None:
            package = self.get(package_name=package_name)
        if package is not None:
            package.open_in_web()
        elif package_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(package_id) + '/main')
        else:
            self._client_api._open_in_web(url=self.platform_url)

    @_api_reference.add(path='/packages/{id}/revisions', method='get')
    def revisions(self, package: entities.Package = None, package_id: str = None):
        """
        Get the package revision history.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package: package entity
        :param str package_id: package id

        **Example**:

        .. code-block:: python

            project.packages.revisions(package='package_entity')
        """
        if package is None and package_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='must provide an identifier in inputs: "package" or "package_id"')
        if package is not None:
            package_id = package.id

        success, response = self._client_api.gen_request(
            req_type="get",
            path="/packages/{}/revisions".format(package_id))
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/packages/{id}', method='get')
    def get(self,
            package_name: str = None,
            package_id: str = None,
            checkout: bool = False,
            fetch=None) -> entities.Package:
        """
        Get Package object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str package_id: package id
        :param str package_name: package name
        :param bool checkout: set the package as a default package object (cookies)
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Package object
        :rtype: dtlpy.entities.package.Package

        **Example**:

        .. code-block:: python

            project.packages.get(package_id='package_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if package_name is None and package_id is None:
            package = self.__get_from_cache()
            if package is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Package was found, must checkout or provide an identifier in inputs')
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
                # verify input package name is same as the given id
                if package_name is not None and package.name != package_name:
                    logger.warning(
                        "Mismatch found in packages.get: package_name is different then package.name:"
                        " {!r} != {!r}".format(
                            package_name,
                            package.name))
            elif package_name is not None:
                filters = entities.Filters(field='name', values=package_name, resource=entities.FiltersResource.PACKAGE,
                                           use_defaults=False)
                if self._project is not None:
                    filters.add(field='projectId', values=self._project.id)
                packages = self.list(filters=filters)
                if packages.items_count == 0:
                    raise exceptions.PlatformException(
                        error='404',
                        message='Package not found. Name: {}'.format(package_name))
                elif packages.items_count > 1:
                    raise exceptions.PlatformException(
                        error='400',
                        message='More than one package found by the name of: {} '
                                'Please get package from a project entity'.format(package_name))
                package = packages.items[0]
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Package was found, must checkout or provide an identifier in inputs')
        else:
            package = entities.Package.from_json(_json={'id': package_id,
                                                        'name': package_name},
                                                 client_api=self._client_api,
                                                 project=self._project,
                                                 is_fetched=False)

        if checkout:
            self.checkout(package=package)
        return package

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Package]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_package, package in enumerate(response_items):
            jobs[i_package] = pool.submit(entities.Package._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': package,
                                             'project': self._project})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        packages = miscellaneous.List([r[1] for r in results if r[0] is True])
        return packages

    def _list(self, filters: entities.Filters):
        url = '/query/faas'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/query/faas', method='post')
    def list(self, filters: entities.Filters = None, project_id: str = None) -> entities.PagedEntities:
        """
        List project packages.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param str project_id: project id
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            project.packages.list()
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.PACKAGE)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.PACKAGE:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.PACKAGE. Got: {!r}'.format(filters.resource))

        if project_id is None and self._project is not None:
            project_id = self._project.id

        if project_id is not None:
            filters.add(field='projectId', values=project_id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       project_id=project_id,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def pull(self, package: entities.Package, version=None, local_path=None, project_id=None):
        """
        Pull (download) the package to a local path.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package: package entity
        :param str version: the package version to pull
        :param local_path: the path of where to save the package
        :param project_id: the project id that include the package
        :return: local path where the package pull
        :rtype: str

        **Example**:

        .. code-block:: python

            project.packages.pull(package='package_entity', local_path='local_path')
        """
        if isinstance(version, int):
            logger.warning('Deprecation Warning - Package/service versions have been refactored'
                           'The version you provided has type: int, it will be converted to: 1.0.{}'
                           'Next time use a 3-level semver for package/service versions'.format(version))

        dir_version = version
        if version is None:
            dir_version = package.version

        if local_path is None:
            local_path = os.path.join(
                services.service_defaults.DATALOOP_PATH,
                "packages",
                "{}-{}".format(package.name, package.id),
                str(dir_version))

        if version is None or version == package.version:
            package_revision = package
        else:
            versions = [revision for revision in package.revisions if revision['version'] == version]
            if len(versions) <= 0:
                raise exceptions.PlatformException('404', 'Version not found: version={}'.format(version))
            elif len(versions) > 1:
                raise exceptions.PlatformException('404', 'More than one version found: version={}'.format(version))
            package_revision = entities.Package.from_json(
                _json=versions[0],
                project=package.project,
                client_api=package._client_api
            )
        if package_revision.codebase.type == entities.PackageCodebaseType.ITEM:
            local_path = package_revision.codebases.unpack(codebase_id=package_revision.codebase.item_id,
                                                           local_path=local_path)
        elif package_revision.codebase.type == entities.PackageCodebaseType.GIT:
            local_path = package_revision.codebases.unpack(codebase=package_revision.codebase,
                                                           local_path=local_path)
        else:
            raise Exception(
                'Pull can only be performed on packages with Item or Git codebase. Codebase type: {!r}'.format(
                    package_revision.codebase.type))

        return local_path

    def _name_validation(self, name: str):
        url = '/piper-misc/naming/packages/{}'.format(name)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

    @staticmethod
    def _validate_slots(slots, modules):
        for slot in slots:
            matched_module = [module for module in modules if slot.module_name == module.name]
            if len(matched_module) != 1:
                raise ValueError('Module {!r} in slots is not defined in modules.'.format(slot.module_name))
            matched_func = [func for func in matched_module[0].functions if slot.function_name == func.name]
            if len(matched_func) != 1:
                raise ValueError('Function {!r} in slots is not defined in module {!r}.'.format(slot.function_name,
                                                                                                slot.module_name))

    def build_requirements(self, filepath) -> list:
        """
        Build a requirement list (list of packages your code requires to run) from a file path. **The file listing the requirements MUST BE a txt file**.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param filepath: path of the requirements file
        :return: a list of dl.PackageRequirement
        :rtype: list
        """
        requirements_list = []
        if not os.path.exists(filepath):
            raise exceptions.PlatformException('400', 'requirements file {} does not exist'.format(filepath))
        with open(filepath) as requirements_txt:
            for requirement in requirements_txt:
                requirement = requirement.strip()
                if '\n' in requirement:
                    requirement.replace('\n', '')
                if requirement.startswith('#'):
                    continue
                elif ' #' in requirement:
                    requirement = requirement[:requirement.find(' #')]
                if 'install -r' in requirement:
                    requirements_list.extend(self.build_requirements(requirement[requirement.find('-r ') + 3:]))
                    continue
                requirement_spit = requirement.split(',')
                for req in requirement_spit:
                    name_version = re.split('<=|>=|==|<|>', req)
                    req_name = name_version[0]
                    req_version, op = None, None
                    if len(name_version) > 1:
                        op = re.findall('<=|>=|==|<|>', req)[0]
                        req_version = name_version[1]
                        if req_name == '':
                            req_name = last_req_name
                        last_req_name = req_name
                    requirements_list.append(
                        entities.PackageRequirement(name=req_name, version=req_version, operator=op))
        return requirements_list

    @_api_reference.add(path='/packages', method='post')
    def push(self,
             project: entities.Project = None,
             project_id: str = None,
             package_name: str = None,
             src_path: str = None,
             codebase: typing.Union[entities.GitCodebase, entities.ItemCodebase, entities.FilesystemCodebase] = None,
             modules: typing.List[entities.PackageModule] = None,
             is_global: bool = None,
             checkout: bool = False,
             revision_increment: str = None,
             version: str = None,
             ignore_sanity_check: bool = False,
             service_update: bool = False,
             service_config: dict = None,
             slots: typing.List[entities.PackageSlot] = None,
             requirements: typing.List[entities.PackageRequirement] = None,
             package_type=None,
             metadata=None
             ) -> entities.Package:
        """
        Push your local package to the UI.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        Project will be taken in the following hierarchy:
        project(input) -> project_id(input) -> self.project(context) -> checked out

        :param dtlpy.entities.project.Project project: optional - project entity to deploy to. default from context or checked-out
        :param str project_id: optional - project id to deploy to. default from context or checked-out
        :param str package_name: package name
        :param str src_path: path to package codebase
        :param dtlpy.entities.codebase.Codebase codebase: codebase object
        :param list modules: list of modules PackageModules of the package
        :param bool is_global: is package is global or local
        :param bool checkout: checkout package to local dir
        :param str revision_increment: optional - str - version bumping method - major/minor/patch - default = None
        :param str version: semver version f the package
        :param bool ignore_sanity_check: NOT RECOMMENDED - skip code sanity check before pushing
        :param bool service_update: optional - bool - update the service
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :param list slots: optional - list of slots PackageSlot of the package
        :param list requirements: requirements - list of package requirements
        :param str package_type: default 'faas', options: 'app', 'ml
        :param dict metadata: dictionary of system and user metadata

        :return: Package object
        :rtype: dtlpy.entities.package.Package

        **Example**:

        .. code-block:: python

            project.packages.push(package_name='package_name',
                                    modules=[module],
                                    version='1.0.0',
                                    src_path=os.getcwd()
                                )
        """
        # get project
        project_to_deploy = None
        if project is not None:
            project_to_deploy = project
        elif project_id is not None:
            project_to_deploy = repositories.Projects(client_api=self._client_api).get(project_id=project_id)
        elif self._project is not None:
            project_to_deploy = self._project
        else:
            try:
                project_to_deploy = repositories.Projects(client_api=self._client_api).get()
            except Exception:
                pass

        if project_to_deploy is None:
            raise exceptions.PlatformException(
                error='400',
                message='Missing project from "packages.push" function. '
                        'Please provide project or id, use Packages from a '
                        'project.packages repository or checkout a project')

        # source path
        if src_path is None:
            if codebase is None:
                src_path = os.getcwd()
                logger.warning('No src_path is given, getting package information from cwd: {}'.format(src_path))

        # get package json
        package_from_json = dict()
        if assets.paths.PACKAGE_FILENAME in os.listdir(src_path):
            with open(os.path.join(src_path, assets.paths.PACKAGE_FILENAME), 'r') as f:
                package_from_json = json.load(f)

        if requirements is not None and not isinstance(requirements, list):
            requirements = [requirements]

        if requirements and assets.paths.REQUIREMENTS_FILENAME in os.listdir(src_path):
            logger.warning('Have both requirements param and requirements file will overwrite the requirements file')

        if not requirements and assets.paths.REQUIREMENTS_FILENAME in os.listdir(src_path):
            req_path = os.path.join(src_path, assets.paths.REQUIREMENTS_FILENAME)
            req_from_file = self.build_requirements(filepath=req_path)
            requirements = req_from_file

        # get name
        if package_name is None:
            package_name = package_from_json.get('name', 'default-package')

        if modules is None and 'modules' in package_from_json:
            modules = package_from_json['modules']

        if slots is None and 'slots' in package_from_json:
            slots = package_from_json['slots']

        if ignore_sanity_check:
            logger.warning(
                'Pushing a package without sanity check can cause errors when trying to deploy, '
                'trigger and execute functions.\n'
                'We highly recommend to not use the ignore_sanity_check flag')
        elif codebase is None:
            modules = self._sanity_before_push(src_path=src_path, modules=modules)

        self._name_validation(name=package_name)

        if slots is not None:
            if modules is None:
                raise ValueError('Cannot add slots when modules is empty.')
            if not isinstance(slots[0], entities.PackageSlot):
                slots = [entities.PackageSlot.from_json(_json=slot) for slot in slots]
            self._validate_slots(slots, modules)

        delete_codebase = False
        if codebase is None:
            codebase = project_to_deploy.codebases.pack(directory=src_path, name=package_name)
            delete_codebase = True

        try:
            # check if exist
            filters = entities.Filters(resource=entities.FiltersResource.PACKAGE, use_defaults=False)
            filters.add(field='projectId', values=project_to_deploy.id)
            filters.add(field='name', values=package_name)
            packages = self.list(filters=filters)
            if packages.items_count > 0:
                # package exists - need to update
                package = packages.items[0]

                if modules is not None:
                    package.modules = modules

                if slots is not None:
                    package.slots = slots

                if is_global is not None:
                    package.is_global = is_global

                if codebase is not None:
                    package.codebase = codebase

                if version is not None:
                    package.version = version

                if requirements is not None:
                    package.requirements = requirements

                if service_config is not None:
                    package.service_config = service_config

                if metadata is not None:
                    package.metadata = metadata

                if package_type is not None:
                    package.package_type = package_type
                package = self.update(package=package, revision_increment=revision_increment)
            else:
                package = self._create(
                    project_to_deploy=project_to_deploy,
                    package_name=package_name,
                    modules=modules,
                    slots=slots,
                    codebase=codebase,
                    is_global=is_global,
                    version=version,
                    service_config=service_config,
                    requirements=requirements,
                    package_type=package_type,
                    metadata=metadata
                )
            if checkout:
                self.checkout(package=package)
        except Exception:
            if delete_codebase:
                project_to_deploy.items.delete(item_id=codebase.item_id)
            raise

        logger.info("Package name: {!r}, id: {!r} has been added to project name: {!r}, id: {!r}".format(
            package.name,
            package.id,
            package.project.name,
            package.project.id))

        if service_update:
            service = package.services.get(service_name=package.name)
            service.package_revision = package.version
            service.update()
        return package

    def _create(self,
                project_to_deploy: entities.Project = None,
                codebase: typing.Union[entities.GitCodebase, entities.ItemCodebase, entities.FilesystemCodebase] = None,
                is_global: bool = None,
                package_name: str = entities.package_defaults.DEFAULT_PACKAGE_NAME,
                modules: typing.List[entities.PackageModule] = None,
                version: str = None,
                service_config: dict = None,
                slots: typing.List[entities.PackageSlot] = None,
                requirements: typing.List[entities.PackageRequirement] = None,
                package_type='faas',
                metadata=None
                ) -> entities.Package:
        """
        Create a package in platform.

        :param project_to_deploy:
        :param dtlpy.entities.codebase.Codebase codebase: codebase object
        :param bool is_global: is package is global or local
        :param str package_name: optional - default: 'default package'
        :param list modules: optional - PackageModules Entity
        :param str version: semver version of the package
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :param list slots: optional - list of slots PackageSlot of the package
        :param list requirements: requirements - list of package requirements
        :param str package_type: default 'faas', options: 'app', 'ml
        :param dict metadata: dictionary of system and user metadata
        :return: Package object
        :rtype: dtlpy.entities.package.Package
        """
        # if is dtlpy entity convert to dict
        if modules and isinstance(modules[0], entities.PackageModule):
            modules = [module.to_json() for module in modules]

        if slots and isinstance(slots[0], entities.PackageSlot):
            slots = [slot.to_json() for slot in slots]

        if is_global is None:
            is_global = False

        payload = {'name': package_name,
                   'global': is_global,
                   'modules': modules,
                   'slots': slots,
                   'serviceConfig': service_config,
                   'type': package_type
                   }

        if codebase is not None:
            payload['codebase'] = codebase.to_json()

        if requirements is not None:
            payload['requirements'] = [r.to_json() for r in requirements]

        if version is not None:
            payload['version'] = version

        if metadata is not None:
            payload['metadata'] = metadata

        if project_to_deploy is not None:
            payload['projectId'] = project_to_deploy.id
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
                                          project=project_to_deploy)

    @_api_reference.add(path='/packages/{ids}', method='delete')
    def delete(self, package: entities.Package = None, package_name=None, package_id=None):
        """
        Delete a Package object.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package: package entity
        :param str package_id: package id
        :param str package_name: package name
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            project.packages.delete(package_name='package_name')
        """
        # get id and name
        if package_name is None or package_id is None:
            if package is None:
                package = self.get(package_id=package_id, package_name=package_name)
            package_id = package.id

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
            # TODO can remove? in transactor?
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

    @_api_reference.add(path='/packages/{id}', method='patch')
    def update(self, package: entities.Package, revision_increment: str = None) -> entities.Package:
        """
        Update Package changes to the platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package:
        :param revision_increment: optional - str - version bumping method - major/minor/patch - default = None
        :return: Package object
        :rtype: dtlpy.entities.package.Package

        **Example**:

        .. code-block:: python

            project.packages.delete(package='package_entity')
        """

        if revision_increment is not None and isinstance(package.version, str) and len(package.version.split('.')) == 3:
            major, minor, patch = package.version.split('.')
            if revision_increment == 'patch':
                patch = int(patch) + 1
            elif revision_increment == 'minor':
                minor = int(minor) + 1
            elif revision_increment == 'major':
                major = int(major) + 1
            package.version = '{}.{}.{}'.format(major, minor, patch)

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
               package_id: str = None,
               package_name: str = None,
               package: entities.Package = None,
               service_name: str = None,
               project_id: str = None,
               revision: str or int = None,
               init_input: typing.Union[typing.List[entities.FunctionIO], entities.FunctionIO, dict] = None,
               runtime: typing.Union[entities.KubernetesRuntime, dict] = None,
               sdk_version: str = None,
               agent_versions: dict = None,
               bot: typing.Union[entities.Bot, str] = None,
               pod_type: entities.InstanceCatalog = None,
               verify: bool = True,
               checkout: bool = False,
               module_name: str = None,
               run_execution_as_process: bool = None,
               execution_timeout: int = None,
               drain_time: int = None,
               on_reset: str = None,
               max_attempts: int = None,
               force: bool = False,
               secrets: list = None,
               **kwargs) -> entities.Service:
        """
        Deploy a package. A service is required to run the code in your package.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str package_id: package id
        :param str package_name: package name
        :param dtlpy.entities.package.Package package: package entity
        :param str service_name: service name
        :param str project_id: project id
        :param str revision: package revision - default=latest
        :param init_input: config to run at startup
        :param dict runtime: runtime resources
        :param str sdk_version:  - optional - string - sdk version
        :param dict agent_versions: - dictionary - - optional -versions of sdk, agent runner and agent proxy
        :param str bot: bot email
        :param str pod_type: pod type dl.InstanceCatalog
        :param bool verify: verify the inputs
        :param bool checkout: checkout
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

            project.packages.deploy(service_name=package_name,
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

        if package is None:
            package = self.get(package_id=package_id, package_name=package_name)

        return package.services.deploy(package=package,
                                       service_name=service_name,
                                       revision=revision,
                                       init_input=init_input,
                                       runtime=runtime,
                                       sdk_version=sdk_version,
                                       agent_versions=agent_versions,
                                       project_id=project_id,
                                       pod_type=pod_type,
                                       bot=bot,
                                       verify=verify,
                                       module_name=module_name,
                                       checkout=checkout,
                                       jwt_forward=kwargs.get('jwt_forward', None),
                                       is_global=kwargs.get('is_global', None),
                                       run_execution_as_process=run_execution_as_process,
                                       execution_timeout=execution_timeout,
                                       drain_time=drain_time,
                                       on_reset=on_reset,
                                       max_attempts=max_attempts,
                                       force=force,
                                       secrets=secrets
                                       )

    def deploy_from_file(self, project, json_filepath):
        """
        Deploy package and service from a JSON file.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.project.Project project: project entity
        :param str json_filepath: path of the file to deploy
        :return: the package and the services

        **Example**:

        .. code-block:: python

            project.packages.deploy_from_file(project='project_entity', json_filepath='json_filepath')
        """
        with open(json_filepath, 'r') as f:
            data = json.load(f)

        package = project.packages.push(
            package_name=data['name'],
            modules=data['modules'],
            src_path=os.path.split(json_filepath)[0]
        )
        deployed_services = list()
        if 'services' in data:
            for service_json in data['services']:
                try:
                    # update
                    service_old = project.services.get(service_name=service_json['name'])
                except exceptions.NotFound:
                    # create
                    service_old = package.services.deploy(service_name=service_json['name'],
                                                          module_name=data['modules'][0]['name'])
                triggers = service_json.pop('triggers', None)
                artifacts = service_json.pop('artifacts', None)
                to_update, service = self.__compare_and_update_service_configurations(service=service_old,
                                                                                      service_json=service_json)
                if to_update:
                    service.package_revision = package.version
                    service.update()
                if triggers:
                    self.__compare_and_update_trigger_configurations(service, triggers)
                if artifacts:
                    self.__compare_and_upload_artifacts(artifacts, package)
                deployed_services.append(service)
        else:
            logger.warning(msg='Package JSON does not have services.')
        return deployed_services, package

    def __update_dict_recursive(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                inner_dict = d.get(k, {})
                if inner_dict is None:
                    inner_dict = {}
                d[k] = self.__update_dict_recursive(inner_dict, v)
            else:
                d[k] = v
        return d

    def __compare_and_update_trigger_configurations(self, service, trigger_list):
        """
        :param service:
        :param trigger_list:
        """
        service_triggers = service.triggers.list().all()
        triggers_dict = dict()
        for trigger in service_triggers:
            triggers_dict[trigger.name] = trigger

        for trigger_json in trigger_list:
            trigger_name = trigger_json['name']
            trigger_spec = trigger_json['spec']
            if trigger_name not in triggers_dict:
                # create
                service.triggers.create(
                    # general
                    name=trigger_name,
                    function_name=trigger_spec['operation']['functionName'],
                    trigger_type=trigger_json['type'],
                    # event
                    scope=trigger_json.get('scope', None),
                    is_global=trigger_json.get('global', None),
                    filters=trigger_spec.get('filter', None),
                    resource=trigger_spec.get('resource', None),
                    execution_mode=trigger_spec.get('executionMode', None),
                    actions=trigger_spec.get('actions', None),
                    # cron
                    start_at=trigger_spec.get('startAt', None),
                    end_at=trigger_spec.get('endAt', None),
                    cron=trigger_spec.get('cron', None),
                )
            else:
                existing_trigger = triggers_dict[trigger_name]
                # check diff
                _json = existing_trigger.to_json()
                # pop unmatched fields
                _ = _json['spec']['operation'].pop('serviceId')
                _new_json = _json.copy()
                # update fields from infra configurations
                self.__update_dict_recursive(_new_json, trigger_json)
                # check diffs
                diffs = miscellaneous.DictDiffer.diff(_json, _new_json)
                if diffs:
                    updated_trigger = existing_trigger.from_json(_json=_new_json,
                                                                 client_api=service._client_api,
                                                                 service=service,
                                                                 project=service._project)
                    updated_trigger.update()

    def __compare_and_update_service_configurations(self, service, service_json):
        """
        :param service:
        :param service_json:
        """
        # take json configuration from service
        _json = service.to_json()
        _new_json = _json.copy()
        # update fields from infra configurations
        self.__update_dict_recursive(_new_json, service_json)
        # check diffs
        diffs = miscellaneous.DictDiffer.diff(_json, _new_json)
        to_update = False
        if diffs:
            # build back service from json
            to_update = True
            service = service.from_json(_json=_new_json,
                                        client_api=service._client_api,
                                        package=service._package,
                                        project=service._project)
        return to_update, service

    def __compare_and_upload_artifacts(self, artifacts, package):
        """
        :param artifacts:
        :param package:
        """
        for artifact in artifacts:
            # create/get .dataloop dir
            cwd = os.getcwd()
            dl_dir = os.path.join(cwd, '.dataloop')
            if not os.path.isdir(dl_dir):
                os.mkdir(dl_dir)

            directory = os.path.abspath(artifact)
            m = hashlib.md5()
            with open(directory, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    m.update(chunk)
            zip_md = m.hexdigest()
            artifacts_list = package.artifacts.list()
            for art in artifacts_list:
                if art.metadata['system']['md5'] == zip_md:
                    return

            artifact_item = package.artifacts.upload(filepath=directory,
                                                     package_name=package.name,
                                                     package=package,
                                                     overwrite=True, )

            artifact_item.metadata['system']['md5'] = zip_md
            artifact_item.update(True)

    @staticmethod
    def _package_json_generator(package_catalog, package_name):
        """
        :param package_catalog:
        :param package_name:
        """
        if package_catalog == PackageCatalog.DEFAULT_PACKAGE_TYPE:
            with open(assets.paths.ASSETS_PACKAGE_FILEPATH, 'r') as f:
                package_asset = json.load(f)
            package_asset['name'] = package_name
            return package_asset

        item_input = entities.FunctionIO(name='item', type='Item')
        annotation_input = entities.FunctionIO(name='annotation', type='Annotation')
        dataset_input = entities.FunctionIO(name='dataset', type='Dataset')
        json_input = entities.FunctionIO(name='config', type='Json')
        query_input = entities.FunctionIO(name='query', type='Json')

        func = entities.PackageFunction(name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME)
        if package_catalog in [PackageCatalog.SINGLE_FUNCTION_ITEM, PackageCatalog.SINGLE_FUNCTION_ITEM_WITH_TRIGGER]:
            func.inputs = [item_input]
            modules = entities.PackageModule(functions=[func])
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_ANNOTATION,
                                 PackageCatalog.SINGLE_FUNCTION_ANNOTATION_WITH_TRIGGER]:
            func.inputs = [annotation_input]
            modules = entities.PackageModule(functions=[func])
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_DATASET,
                                 PackageCatalog.SINGLE_FUNCTION_DATASET_WITH_TRIGGER]:
            func.inputs = [dataset_input]
            modules = entities.PackageModule(functions=[func])
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_NO_INPUT]:
            modules = entities.PackageModule(functions=[func])
        elif package_catalog == PackageCatalog.SINGLE_FUNCTION_JSON:
            func.inputs = json_input
            modules = entities.PackageModule(functions=[func])
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_ITEM, PackageCatalog.MULTI_FUNCTION_ITEM_WITH_TRIGGERS]:
            func.inputs = [item_input]
            func.name = 'first_method'
            second_func = deepcopy(func)
            second_func.name = 'second_method'
            modules = entities.PackageModule(functions=[func, second_func])
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_ANNOTATION,
                                 PackageCatalog.MULTI_FUNCTION_ANNOTATION_WITH_TRIGGERS]:
            func.inputs = [annotation_input]
            func.name = 'first_method'
            second_func = deepcopy(func)
            second_func.name = 'second_method'
            modules = entities.PackageModule(functions=[func, second_func])
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_DATASET,
                                 PackageCatalog.MULTI_FUNCTION_DATASET_WITH_TRIGGERS]:
            func.inputs = [dataset_input]
            func.name = 'first_method'
            second_func = deepcopy(func)
            second_func.name = 'second_method'
            modules = entities.PackageModule(functions=[func, second_func])
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_JSON]:
            func.inputs = [json_input]
            func.name = 'first_method'
            second_func = deepcopy(func)
            second_func.name = 'second_method'
            modules = entities.PackageModule(functions=[func, second_func])
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_NO_INPUT]:
            func.name = 'first_method'
            second_func = deepcopy(func)
            second_func.name = 'second_method'
            modules = entities.PackageModule(functions=[func, second_func])
        elif package_catalog in [PackageCatalog.MULTI_MODULE, PackageCatalog.MULTI_MODULE_WITH_TRIGGER]:
            func.inputs = [item_input]
            module_a = entities.PackageModule(functions=[func],
                                              name='first_module',
                                              entry_point='first_module_class.py')
            module_b = entities.PackageModule(functions=[func],
                                              name='second_module',
                                              entry_point='second_module_class.py')
            modules = [module_a, module_b]
        elif package_catalog == PackageCatalog.SINGLE_FUNCTION_MULTI_INPUT:
            func.inputs = [item_input, dataset_input, json_input, annotation_input]
            modules = entities.PackageModule(functions=[func])
        elif package_catalog == PackageCatalog.CONVERTER_FUNCTION:
            func.inputs = [dataset_input, query_input]
            modules = entities.PackageModule(functions=[func])
        else:
            raise exceptions.PlatformException('404', 'Unknown package catalog type: {}'.format(package_catalog))

        if not isinstance(modules, list):
            modules = [modules]

        _json = {'name': package_name,
                 'modules': [module.to_json() for module in modules]}

        return _json

    @staticmethod
    def build_trigger_dict(actions,
                           name='default_module',
                           filters=None,
                           function='run',
                           execution_mode: entities.TriggerExecutionMode = 'Once',
                           type_t: entities.TriggerType = "Event"):
        """
        Build a trigger dictionary to trigger FaaS.
        Read more about `FaaS Triggers <https://developers.dataloop.ai/tutorials/faas/auto_annotate/chapter/#trigger-the-service>`_.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param actions: list of dl.TriggerAction
        :param str name: trigger name
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param str function: function name
        :param str execution_mode: execution mode dl.TriggerExecutionMode
        :param str type_t: trigger type dl.TriggerType
        :return: trigger dict
        :rtype: dict

        **Example**:

        .. code-block:: python

            project.packages.build_trigger_dict(actions=dl.TriggerAction.CREATED,
                                              function='run',
                                              execution_mode=dl.TriggerExecutionMode.ONCE)
        """
        if not isinstance(actions, list):
            actions = [actions]

        if not filters:
            filters = dict()

        trigger_dict = {
            "name": name,
            "type": type_t,
            "spec": {
                "filter": filters,
                "executionMode": execution_mode,
                "resource": "Item",
                "actions": actions,
                "input": {},
                "operation": {
                    "type": "function",
                    "functionName": function
                }
            }
        }
        return trigger_dict

    @staticmethod
    def _service_json_generator(package_catalog, service_name):
        """
        :param package_catalog:
        :param service_name:
        """
        triggers = list()
        with open(assets.paths.ASSETS_PACKAGE_FILEPATH, 'r') as f:
            service_json = json.load(f)["services"][0]
        if package_catalog == PackageCatalog.DEFAULT_PACKAGE_TYPE:
            triggers = service_json['triggers']
        elif 'triggers' in package_catalog:
            trigger_a = Packages.build_trigger_dict(name='first_trigger',
                                                    filters=dict(),
                                                    actions=['Created'],
                                                    function='first_method',
                                                    execution_mode=entities.TriggerExecutionMode.ONCE)
            trigger_b = Packages.build_trigger_dict(name='second_trigger',
                                                    filters=dict(),
                                                    actions=['Created'],
                                                    function='second_method',
                                                    execution_mode=entities.TriggerExecutionMode.ONCE)
            if 'item' in package_catalog:
                trigger_a['spec']['resource'] = trigger_b['spec']['resource'] = 'Item'
            if 'dataset' in package_catalog:
                trigger_a['spec']['resource'] = trigger_b['spec']['resource'] = 'Dataset'
            if 'annotation' in package_catalog:
                trigger_a['spec']['resource'] = trigger_b['spec']['resource'] = 'Annotation'
            triggers += [trigger_a, trigger_b]
        elif 'trigger' in package_catalog:
            trigger = Packages.build_trigger_dict(name='triggername',
                                                  filters=dict(),
                                                  actions=[],
                                                  function=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
                                                  execution_mode=entities.TriggerExecutionMode.ONCE)
            if 'item' in package_catalog:
                trigger['spec']['resource'] = 'Item'
            if 'dataset' in package_catalog:
                trigger['spec']['resource'] = 'Dataset'
            if 'annotation' in package_catalog:
                trigger['spec']['resource'] = 'Annotation'
            triggers += [trigger]

        if service_name is not None:
            service_json['name'] = service_name
        if 'multi_module' in package_catalog:
            service_json['moduleName'] = 'first_module'

        service_json['triggers'] = triggers

        return service_json

    @staticmethod
    def generate(name=None,
                 src_path: str = None,
                 service_name: str = None,
                 package_type=PackageCatalog.DEFAULT_PACKAGE_TYPE):
        """
        Generate a new package. Provide a file path to a JSON file with all the details of the package and service to generate the package. 

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str name: name
        :param str src_path: source file path
        :param str service_name: service name
        :param str package_type: package type from PackageCatalog

        **Example**:

        .. code-block:: python

            project.packages.generate(name='package_name',
                                      src_path='src_path')

        """
        # name
        if name is None:
            name = 'default-package'
        if service_name is None:
            service_name = 'default-service'

        # src path
        if src_path is None:
            src_path = os.getcwd()

        package_asset = Packages._package_json_generator(package_name=name,
                                                         package_catalog=package_type)
        services_asset = Packages._service_json_generator(package_catalog=package_type,
                                                          service_name=service_name)
        package_asset["services"] = [services_asset]
        to_generate = [
            {'src': assets.paths.ASSETS_GITIGNORE_FILEPATH, 'dst': os.path.join(src_path, '.gitignore'),
             'type': 'copy'},
            {'src': package_asset,
             'dst': os.path.join(src_path, assets.paths.PACKAGE_FILENAME), 'type': 'json'}
        ]

        if package_type == PackageCatalog.DEFAULT_PACKAGE_TYPE:
            to_generate.append({'src': assets.paths.ASSETS_MOCK_FILEPATH,
                                'dst': os.path.join(src_path, assets.paths.MOCK_FILENAME), 'type': 'copy'})
        else:
            module = entities.PackageModule.from_json(package_asset['modules'][0])
            function_name = module.functions[0].name

            to_generate.append({'src': Packages._mock_json_generator(module=module, function_name=function_name),
                                'dst': os.path.join(src_path, assets.paths.MOCK_FILENAME), 'type': 'json'})

        main_file_paths = Packages._entry_point_generator(package_catalog=package_type)
        if len(main_file_paths) == 1:
            to_generate.append({'src': main_file_paths[0],
                                'dst': os.path.join(src_path, assets.paths.MAIN_FILENAME),
                                'type': 'copy'})
        else:
            to_generate += [{'src': main_file_paths[0],
                             'dst': os.path.join(src_path, assets.paths.MODULE_A_FILENAME),
                             'type': 'copy'},
                            {'src': main_file_paths[1],
                             'dst': os.path.join(src_path, assets.paths.MODULE_B_FILENAME),
                             'type': 'copy'}
                            ]

        for job in to_generate:
            if not os.path.isfile(job['dst']):
                if job['type'] == 'copy':
                    copyfile(job['src'], job['dst'])
                elif job['type'] == 'json':
                    with open(job['dst'], 'w') as f:
                        json.dump(job['src'], f, indent=2)

        logger.info('Successfully generated package')

    def build(self, package: entities.Package, module_name=None, init_inputs=None, local_path=None, from_local=None):
        """
        Instantiate a module from the package code. Returns a loaded instance of the runner class

        :param package: Package entity
        :param module_name: Name of the module to build the runner class
        :param str init_inputs: dictionary of the class init variables (if exists). will be used to init the module class
        :param str local_path: local path of the package (if from_local=False - codebase will be downloaded)
        :param bool from_local: bool. if true - codebase will not be downloaded (only use local files)
        :return: dl.BaseServiceRunner
        """
        if module_name is None:
            module_name = entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME
        if init_inputs is None:
            init_inputs = dict()
        if package.codebase is None:
            raise exceptions.PlatformException(error='2001',
                                               message="Package {!r} has no codebase. unable to build a module".format(
                                                   package.name))

        if from_local is None:
            from_local = package.codebase.is_local

        if not from_local:
            # Not local => download codebase
            if package.codebase.is_local:
                raise RuntimeError("using local codebase: {}. Cannot use from_local=False".
                                   format(package.codebase.to_json()))
            local_path = self.pull(package=package, local_path=local_path)

        sys.path.append(local_path)  # TODO: is it the best way to use the imports?
        # load module from path
        module = [module for module in package.modules if module.name == module_name]
        if len(module) != 1:
            raise ValueError('Cannot find module from package. trying to load: {!r}, available modules: {}'.format(
                module_name,
                [module.name for module in package.modules]
            ))
        module = module[0]
        entry_point = os.path.join(local_path, module.entry_point)
        class_name = module.class_name
        if not os.path.isfile(entry_point):
            raise ValueError('Module entry point file is missing: {}'.format(entry_point))
        spec = importlib.util.spec_from_file_location(class_name, entry_point)
        if spec is None:
            raise ValueError('Cant load class ModelAdapter from entry point: {}'.format(entry_point))
        package_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package_module)
        package_module_cls = getattr(package_module, class_name)
        package_module = package_module_cls(**init_inputs)
        logger.info('Model adapter loaded successfully!')
        return package_module

    @staticmethod
    def _mock_json_generator(module: entities.PackageModule, function_name):
        """
        :param module:
        :param function_name:
        """
        _json = dict(function_name=function_name, module_name=module.name)
        funcs = [func for func in module.functions if func.name == function_name]
        if len(funcs) == 1:
            func = funcs[0]
        else:
            raise exceptions.PlatformException('400', 'Other than 1 functions by the name of: {}'.format(function_name))
        _json['config'] = {inpt.name: entities.Package._mockify_input(input_type=inpt.type)
                           for inpt in module.init_inputs}
        _json['inputs'] = [{'name': inpt.name, 'value': entities.Package._mockify_input(input_type=inpt.type)}
                           for inpt in func.inputs]
        return _json

    @staticmethod
    def _entry_point_generator(package_catalog):
        """
        :param package_catalog:
        """
        if package_catalog == PackageCatalog.DEFAULT_PACKAGE_TYPE:
            paths_to_service_runner = assets.paths.ASSETS_MAIN_FILEPATH
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_ITEM, PackageCatalog.SINGLE_FUNCTION_ITEM_WITH_TRIGGER]:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_ITEM_SR_PATH
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_ANNOTATION,
                                 PackageCatalog.SINGLE_FUNCTION_ANNOTATION_WITH_TRIGGER]:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_ANNOTATION_SR_PATH
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_DATASET,
                                 PackageCatalog.SINGLE_FUNCTION_DATASET_WITH_TRIGGER]:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_DATASET_SR_PATH
        elif package_catalog in [PackageCatalog.SINGLE_FUNCTION_NO_INPUT]:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_SR_PATH
        elif package_catalog == PackageCatalog.SINGLE_FUNCTION_JSON:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_JSON_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_ITEM, PackageCatalog.MULTI_FUNCTION_ITEM_WITH_TRIGGERS]:
            paths_to_service_runner = assets.service_runner_paths.MULTI_METHOD_ITEM_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_ANNOTATION,
                                 PackageCatalog.MULTI_FUNCTION_ANNOTATION_WITH_TRIGGERS]:
            paths_to_service_runner = assets.service_runner_paths.MULTI_METHOD_ANNOTATION_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_DATASET,
                                 PackageCatalog.MULTI_FUNCTION_DATASET_WITH_TRIGGERS]:
            paths_to_service_runner = assets.service_runner_paths.MULTI_METHOD_DATASET_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_JSON]:
            paths_to_service_runner = assets.service_runner_paths.MULTI_METHOD_JSON_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_FUNCTION_NO_INPUT]:
            paths_to_service_runner = assets.service_runner_paths.MULTI_METHOD_SR_PATH
        elif package_catalog in [PackageCatalog.MULTI_MODULE, PackageCatalog.MULTI_MODULE_WITH_TRIGGER]:
            paths_to_service_runner = [assets.service_runner_paths.SINGLE_METHOD_ITEM_SR_PATH,
                                       assets.service_runner_paths.SINGLE_METHOD_ITEM_SR_PATH]
        elif package_catalog == PackageCatalog.SINGLE_FUNCTION_MULTI_INPUT:
            paths_to_service_runner = assets.service_runner_paths.SINGLE_METHOD_MULTI_INPUT_SR_PATH
        elif package_catalog == PackageCatalog.CONVERTER_FUNCTION:
            paths_to_service_runner = assets.service_runner_paths.CONVERTER_SR_PATH
        else:
            raise exceptions.PlatformException('404', 'Unknown package catalog type: {}'.format(package_catalog))

        if not isinstance(paths_to_service_runner, list):
            paths_to_service_runner = [paths_to_service_runner]

        return paths_to_service_runner

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

    def test_local_package(self,
                           cwd: str = None,
                           concurrency: int = None,
                           package: entities.Package = None,
                           module_name: str = entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME,
                           function_name: str = entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
                           class_name: str = entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME,
                           entry_point: str = entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT,
                           mock_file_path: str = None):
        """
        Test local package in local environment.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str cwd: path to the file
        :param int concurrency: the concurrency of the test
        :param dtlpy.entities.package.Package package: entities.package
        :param str module_name: module name
        :param str function_name: function name
        :param str class_name: class name
        :param str entry_point: the file to run like main.py
        :param str mock_file_path: the mock file that have the inputs
        :return: list created by the function that tested the output
        :rtype: list

        **Example**:

        .. code-block:: python

            project.packages.test_local_package(cwd='path_to_package',
                                                package='package_entity',
                                                function_name='run')
        """
        if cwd is None:
            cwd = os.getcwd()
        if mock_file_path is None:
            mock_file_path = assets.paths.MOCK_FILENAME
        with open(os.path.join(cwd, mock_file_path), 'r') as f:
            mock_json = json.load(f)
        is_multithread = self.is_multithread(inputs=mock_json['inputs'])

        local_runner = LocalServiceRunner(self._client_api,
                                          packages=self,
                                          cwd=cwd,
                                          package=package,
                                          multithreading=is_multithread,
                                          concurrency=concurrency,
                                          module_name=module_name,
                                          function_name=function_name,
                                          class_name=class_name,
                                          entry_point=entry_point,
                                          mock_file_path=mock_file_path)

        if self._project is None:
            try:
                project = repositories.Projects(client_api=self._client_api).get()
            except Exception:
                project = None
        else:
            project = self.project

        return local_runner.run_local_project(project=project)

    def __get_from_cache(self) -> entities.Package:
        package = self._client_api.state_io.get('package')
        if package is not None:
            package = entities.Package.from_json(_json=package, client_api=self._client_api, project=self._project)
        return package

    def checkout(self,
                 package: entities.Package = None,
                 package_id: str = None,
                 package_name: str = None):
        """
        Checkout (switch) to a package.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.package.Package package: package entity
        :param str package_id: package id
        :param str package_name: package name

        **Example**:

        .. code-block:: python

            project.packages.checkout(package='package_entity')

        """
        if package is None:
            package = self.get(package_id=package_id, package_name=package_name)
        self._client_api.state_io.put('package', package.to_json())
        logger.info("Checked out to package {}".format(package.name))

    @staticmethod
    def check_cls_arguments(cls, missing, function_name, function_inputs):
        """
        Check class arguments. This method checks that the package function is correct.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param cls: packages class
        :param list missing: list of the missing params
        :param str function_name: name of function
        :param list function_inputs: list of function inputs
        """
        # input to function and inputs definitions match
        func = getattr(cls, function_name)
        func_inspect = inspect.getfullargspec(func)
        if not isinstance(function_inputs, list):
            function_inputs = [function_inputs]
        defined_input_names = [inp['name'] if isinstance(inp, dict) else inp.name for inp in function_inputs]

        args_with_values = dict()
        # go over the defaults and inputs from end to start to map between them
        if func_inspect.defaults is not None:
            for i_value in range(-1, -len(func_inspect.defaults) - 1, -1):
                args_with_values[func_inspect.args[i_value]] = func_inspect.defaults[i_value]

        for input_name in func_inspect.args:
            if input_name in ['self', 'progress', 'context']:
                continue
            if input_name not in defined_input_names:
                logger.warning('missing input name: "{}" in function definition: "{}"'.format(input_name,
                                                                                              function_name))
                if input_name not in args_with_values:
                    missing.append('missing input name: "{}" in function definition: "{}"'.format(input_name,
                                                                                                  function_name))

    @staticmethod
    def _sanity_before_push(src_path, modules):
        """
        :param src_path:
        :param modules:
        """
        if modules is None:
            modules = [DEFAULT_PACKAGE_MODULE]

        if not isinstance(modules, list):
            modules = [modules]

        if not isinstance(modules[0], entities.PackageModule):
            modules = [entities.PackageModule.from_json(_json=module) for module in modules]

        missing = list()
        for module in modules:
            entry_point = module.entry_point
            class_name = module.class_name

            check_init = True
            functions = module.functions
            # check in inputs is a list
            if not isinstance(functions, list):
                functions = [functions]

            for function in functions:
                # entry point exists
                entry_point_filepath = os.path.join(src_path, entry_point)
                if not os.path.isfile(entry_point_filepath):
                    missing.append('missing entry point file: {}'.format(entry_point_filepath))
                    continue

                # class name in entry point
                try:
                    spec = importlib.util.spec_from_file_location(class_name, entry_point_filepath)
                    cls_def = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(cls_def)
                except ImportError as e:
                    logger.warning(
                        'Cannot run sanity check to find conflicts between package module and source code'
                        'because some packages in your source code are not installed in your local environment'.format(
                            e.__str__())
                    )
                    return modules

                if not hasattr(cls_def, class_name):
                    missing.append('missing class: "{}" from file: "{}"'.format(class_name, entry_point_filepath))
                    continue

                # function in class
                cls = getattr(cls_def, class_name)
                if not hasattr(cls, function.name):
                    missing.append(
                        'missing function: "{}" from class: "{}"'.format(function.name, entry_point_filepath))
                    continue

                if check_init:
                    check_init = False
                    # input to __init__ and inputs definitions match
                    Packages.check_cls_arguments(cls=cls,
                                                 missing=missing,
                                                 function_name="__init__",
                                                 function_inputs=module.init_inputs)

                Packages.check_cls_arguments(cls=cls,
                                             missing=missing,
                                             function_name=function.name,
                                             function_inputs=function.inputs)

        if len(missing) != 0:
            raise ValueError('There are conflicts between modules and source code:'
                             '\n{}\n{}'.format(missing,
                                               'Please fix conflicts or use flag ignore_sanity_check'))

        return modules


class LocalServiceRunner:
    """
    Service Runner Class
    """

    def __init__(self,
                 client_api: ApiClient,
                 packages,
                 cwd=None,
                 multithreading=False,
                 concurrency=10,
                 package: entities.Package = None,
                 module_name=entities.package_defaults.DEFAULT_PACKAGE_MODULE_NAME,
                 function_name=entities.package_defaults.DEFAULT_PACKAGE_FUNCTION_NAME,
                 class_name=entities.package_defaults.DEFAULT_PACKAGE_CLASS_NAME,
                 entry_point=entities.package_defaults.DEFAULT_PACKAGE_ENTRY_POINT,
                 mock_file_path=None):
        if cwd is None:
            self.cwd = os.getcwd()
        else:
            self.cwd = cwd

        self._client_api = client_api
        self._packages = packages
        self.package_io = PackageIO(cwd=self.cwd)
        self.multithreading = multithreading
        self.concurrency = concurrency
        self._module_name = module_name
        self._function_name = function_name
        self._entry_point = entry_point
        self._class_name = class_name
        self.package = package

        if mock_file_path is None:
            mock_file_path = 'mock.json'
        with open(os.path.join(self.cwd, mock_file_path), 'r') as f:
            self.mock_json = json.load(f)

    @property
    def function_name(self):
        return self.mock_json.get('function_name', self._function_name)

    @property
    def module_name(self):
        return self.mock_json.get('module_name', self._module_name)

    @property
    def class_name(self):
        return self.mock_json.get('class_name', self._class_name)

    @property
    def entry_point(self):
        return self.mock_json.get('entry_point', self._entry_point)

    def get_mainpy_run_service(self):
        """
        Get mainpy run service

        :return:
        """
        entry_point = os.path.join(self.cwd, self.entry_point)
        spec = importlib.util.spec_from_file_location(self.class_name, entry_point)
        cls_def = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls_def)
        service_runner = getattr(cls_def, self.class_name)

        if 'init_params' in self.mock_json:
            kwargs = self.mock_json.get('init_params')
        elif 'config' in self.mock_json:
            kwargs = self.mock_json.get('config')
        else:
            kwargs = dict()

        return service_runner(**kwargs)

    def run_local_project(self, project=None):
        """
        Run local project

        :param project: project entity
        """
        package_runner = self.get_mainpy_run_service()

        modules = self.package_io.get('modules') if self.package is None else [
            m.to_json() for m in self.package.modules
        ]

        if isinstance(modules, list) and len(modules) > 0:
            try:
                module = [module for module in modules if module['name'] == self.module_name][0]
            except Exception:
                raise exceptions.PlatformException(
                    '400', 'Module {} does not exist in package modules'.format(self.module_name)
                )
        else:
            module = DEFAULT_PACKAGE_MODULE.to_json()

        if isinstance(module['functions'], list) and len(module['functions']) > 0:
            try:
                func = [func for func in module['functions'] if func['name'] == self.function_name][0]
            except Exception:
                raise exceptions.PlatformException(
                    '400', 'function {} does not exist in package module'.format(self.function_name)
                )
        else:
            func = entities.PackageFunction(None, list(), list(), None).to_json()
        package_inputs = func['input']
        current_level = logging.root.level
        logging.root.setLevel('INFO')
        if not self.multithreading:
            kwargs = dict()
            progress = utilities.Progress()

            func = getattr(package_runner, self.function_name)
            params = list(inspect.signature(func).parameters)
            if "progress" in params:
                kwargs['progress'] = progress

            for package_input in package_inputs:
                kwargs[package_input['name']] = self.get_field(field_name=package_input['name'],
                                                               field_type=package_input['type'],
                                                               project=project, mock_json=self.mock_json)

            results = getattr(package_runner, self.function_name)(**kwargs)
        else:
            pool = ThreadPoolExecutor(max_workers=self.concurrency)
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
                    pool.submit(
                        getattr(package_runner, self.function_name),
                        **kwargs
                    )
                )
            for job in jobs:
                results.append(job.result())

        logging.root.level = current_level
        return results

    @staticmethod
    def _is_entity(output_type: str):
        # output_type is a entity class starts with capital
        return hasattr(entities, output_type)

    def _fetch_single_resource(self, value, output_type):
        if isinstance(value, dict):
            params = {'{}_id'.format(output_type.lower()): value['{}_id'.format(output_type.lower())]}
        else:
            params = {'{}_id'.format(output_type.lower()): value}
        return getattr(repositories, '{}s'.format(output_type))(self._client_api).get(**params)

    def get_field(self, field_name, field_type, mock_json, project=None, mock_inputs=None):
        """
        Get field in mock json.

        :param field_name: field name
        :param field_type: field type
        :param mock_json: mock json
        :param project: project
        :param mock_inputs: mock inputs
        :return:
        """
        if mock_inputs is None:
            mock_inputs = mock_json['inputs']
        filtered_mock_inputs = list(filter(lambda input_field: input_field['name'] == field_name, mock_inputs))

        if len(filtered_mock_inputs) == 0:
            raise Exception('No entry for field {} found in mock'.format(field_name))
        if len(filtered_mock_inputs) > 1:
            raise Exception('Duplicate entries for field {} found in mock'.format(field_name))

        if field_type not in list(entities.PackageInputType):
            raise exceptions.PlatformException('400', 'Unknown resource type for field {}'.format(field_name))

        mock_input = filtered_mock_inputs[0]
        resource_id = mock_input['value']

        if field_type.endswith('[]') and self._is_entity(output_type=field_type.replace('[]', '')):
            field_type = field_type.replace('[]', '')
            value = resource_id if isinstance(resource_id, list) else [resource_id]
            return [
                self._fetch_single_resource(value=val, output_type=field_type) for val in value
            ]
        elif self._is_entity(output_type=field_type):
            return self._fetch_single_resource(value=resource_id, output_type=field_type)
        else:
            return resource_id


class PackageIO:

    def __init__(self, cwd=None):
        if cwd is None:
            cwd = os.getcwd()

        self.package_file_path = os.path.join(cwd, assets.paths.PACKAGE_FILENAME)

    def read_json(self):
        file_path = self.package_file_path

        with open(file_path, 'r') as fp:
            cfg = json.load(fp)
        return cfg

    def get(self, key):
        """
        :param key:
        """
        cfg = self.read_json()
        return cfg[key]

    def put(self, key, value):
        """
        :param key:
        :param value:
        """
        try:
            cfg = self.read_json()
            cfg[key] = value
            file_path = self.package_file_path
            with open(file_path, 'w') as fp:
                json.dump(cfg, fp, indent=2)
        except Exception:
            pass
