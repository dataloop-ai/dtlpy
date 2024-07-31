import json
import logging
import os
from typing import List, Optional
from pathlib import Path

from .. import exceptions, entities, services, miscellaneous, assets
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Dpks:
    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    @property
    def project(self) -> Optional[entities.Project]:
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def init(self, directory: str = None, name: str = None, description: str = None,
             attributes: dict = None, icon: str = None, scope: str = None):
        """
        Initialize a dpk project with the specified projects.

        :param str directory: the directory where to initialize the project
        :param str name: the name of the dpk.
        :param str description: the description of the dpk.
        :param str attributes: the attributes of the dpk.
        :param str icon: the icon of the dpk.
        :param str scope: the scope of the dpk.

        ** Example **
        .. code-block:: python
            dl.dpks.init(name='Hello World', description='A description of the dpk', attributes={
                "Provider": "Dataloop",
                "License": "",
                "Category": "Model",
                "Computer Vision": "Object Detection",
                "Media Type": "Image"
              },
                        icon='path_to_icon', scope='organization')
        """
        if directory is None:
            directory = os.getcwd()
        dpk = entities.Dpk.from_json(_json={'name': miscellaneous.JsonUtils.get_if_absent(name),
                                            'description': miscellaneous.JsonUtils.get_if_absent(description),
                                            'attributes': miscellaneous.JsonUtils.get_if_absent(attributes),
                                            'icon': miscellaneous.JsonUtils.get_if_absent(icon),
                                            'scope': miscellaneous.JsonUtils.get_if_absent(scope, 'organization'),
                                            'components': dict()
                                            },
                                     client_api=self._client_api)
        dataloop_filepath = os.path.join(directory, assets.paths.APP_JSON_FILENAME)
        with open(dataloop_filepath, 'w') as json_file:
            json_file.write(json.dumps(dpk.to_json(), indent=4))
        os.makedirs(os.path.join(directory, 'functions'), exist_ok=True)
        os.makedirs(os.path.join(directory, 'panels'), exist_ok=True)

    # noinspection PyMethodMayBeStatic
    def pack(self, directory: str = None, name: str = None, subpaths_to_append: List[str] = None) -> str:
        """
        :param str directory: optional - the project to pack, if not specified use the current project,
        :param str name: optional - the name of the dpk file.
        :param List[str] subpaths_to_append: optional - the files/directories to add to the dpk file.
                                            (along with functions, panels and dataloop.json)
        :return the path of the dpk file

        **Example**

        .. code-block:: python
            filepath = dl.apps.pack(directory='/my-current-project', name='project-name')
        """
        # create/get .dataloop dir
        cwd = os.getcwd()
        dl_dir = os.path.join(cwd, '.dataloop')
        if not os.path.isdir(dl_dir):
            os.mkdir(dl_dir)
        if directory is None:
            directory = cwd

        # get dpk name
        if name is None:
            name = os.path.basename(directory)

        with open(os.path.join(directory, 'dataloop.json'), 'r') as file:
            app_json = json.load(file)
        version = app_json.get('version', None)
        if version is None:
            logger.warning('No Version specified, setting to 1.0.0')
            version = '1.0.0'
        # create/get dist folder
        dpk_filename = os.path.join(dl_dir, '{}_{}.dpk'.format(name, version))

        if not os.path.isdir(directory):
            raise ValueError('Not a directory: {}'.format(directory))
        if subpaths_to_append is None:
            subpaths_to_append = []

        try:
            directory = os.path.abspath(directory)
            # create zipfile
            miscellaneous.Zipping.zip_directory(zip_filename=dpk_filename,
                                                directory=directory,
                                                ignore_directories=['artifacts'])
            return dpk_filename
        except Exception:
            logger.error('Error when packing:')
            raise

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Dpk]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(entities.Dpk._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item,
                                          'project': self._project})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items

    def pull(self, dpk: entities.Dpk = None, dpk_id: str = None, dpk_name: str = None, local_path=None) -> str:
        """
        Pulls the app from the platform as dpk file.

        Note: you must pass either dpk_name or dpk_id to the function.
        :param str dpk: DPK entity.
        :param str dpk_id: the name of the dpk.
        :param str dpk_name: the id of the dpk.
        :param local_path: the path where you want to install the dpk file.
        :return local path where the package pull

        **Example**
        ..code-block:: python
            path = dl.dpks.pull(dpk_name='my-app')
        """
        if dpk is None:
            dpk = self.get(dpk_id=dpk_id, dpk_name=dpk_name)
        if local_path is None:
            local_path = os.path.join(
                services.service_defaults.DATALOOP_PATH,
                "dpks",
                dpk.name,
                str(dpk.version))

        dpk.codebases.unpack(codebase=dpk.codebase, local_path=local_path)
        return local_path

    def __get_by_name(self, dpk_name: str, dpk_version: str = None):
        filters = entities.Filters(field='name',
                                   values=dpk_name,
                                   resource=entities.FiltersResource.DPK,
                                   use_defaults=False)
        dpks = self.list(filters=filters)
        # only latest version returns so should be only one
        if dpks.items_count == 0:
            raise exceptions.PlatformException(error='404',
                                               message='Dpk not found. Name: {}'.format(dpk_name))
        elif dpks.items_count > 1:
            raise exceptions.PlatformException(
                error='400',
                message='More than one dpk found by the name of: {}'.format(dpk_name))
        dpk: entities.Dpk = dpks.items[0]

        ########################
        # get specific version #
        ########################
        if dpk_version is not None and dpk.version != dpk_version:
            filters = entities.Filters(field='version',
                                       values=dpk_version,
                                       resource=entities.FiltersResource.DPK,
                                       use_defaults=False)
            dpk_v = dpk._get_revision_pages(filters=filters)
            if dpk_v.items_count == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message=f'Dpk version not found. Name: {dpk_name}, version: {dpk_version}')
            elif dpk_v.items_count > 1:
                # should never be here - more than one with same name and version
                raise exceptions.PlatformException(
                    error='400',
                    message=f'More than one dpk found with name: {dpk_name}, version: {dpk_version}')
            dpk = dpk_v.items[0]
        return dpk

    def publish(self, dpk: entities.Dpk = None, ignore_max_file_size: bool = False,
                manifest_filepath='dataloop.json') -> entities.Dpk:
        """
        Upload a dpk entity to the dataloop platform.

        :param entities.Dpk dpk: Optional. The DPK entity to publish. If None, a new DPK is created
                             from the manifest file.
        :param bool ignore_max_file_size: Optional. If True, the maximum file size check is ignored
                                        during the packaging of the codebase.
        :param str manifest_filepath: Optional. Path to the manifest file. Can be absolute or relative.
                                    Defaults to 'dataloop.json'

        :return the published dpk
        :rtype dl.entities.Dpk

        **Example**

        .. code-block:: python
            published_dpk = dl.dpks.publish()
        """
        manifest_path = Path(manifest_filepath).resolve()

        if dpk is None:
            if not manifest_path.exists():
                raise FileNotFoundError(f'{manifest_filepath} file must exist in order to publish a dpk')
            with open(manifest_filepath, 'r') as f:
                json_file = json.load(f)
            dpk = entities.Dpk.from_json(_json=json_file,
                                         client_api=self._client_api,
                                         project=self.project)

        if not dpk.context:
            dpk.context = {}
        if 'project' not in dpk.context:
            if not self.project:
                raise exceptions.PlatformException('400', 'project id must be provided in the context')
            dpk.context['project'] = self.project.id
        if 'org' not in dpk.context and dpk.scope == 'organization':
            if not self.project:
                raise exceptions.PlatformException('400', 'org id must be provided in the context')
            dpk.context['org'] = self.project.org['id']

        if self.project and self.project.id != dpk.context['project']:
            logger.warning("the project id that provide different from the dpk project id")

        if dpk.codebase is None:
            dpk.codebase = self.project.codebases.pack(directory=os.getcwd(),
                                                       name=dpk.display_name,
                                                       extension='dpk',
                                                       ignore_directories=['artifacts'],
                                                       ignore_max_file_size=ignore_max_file_size)

        success_pack, response_pack = self._client_api.gen_request(req_type='post',
                                                                   json_req=dpk.to_json(),
                                                                   path='/app-registry')
        if not success_pack:
            raise exceptions.PlatformException(error=response_pack)

        return entities.Dpk.from_json(response_pack.json(), self._client_api, dpk.project)

    def delete(self, dpk_id: str) -> bool:
        """
        Delete the dpk from the app store.

        Note: after removing the dpk, you cant get it again, it's advised to pull it first.

        :param str dpk_id: the id of the dpk.
        :return whether the operation ran successfully
        :rtype bool
        """
        success, response = self._client_api.gen_request(req_type='delete', path=f'/app-registry/{dpk_id}')
        if success:
            logger.info('Deleted dpk successfully')
        else:
            raise exceptions.PlatformException(response)
        return success

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List the available dpks.

        :param entities.Filters filters: the filters to apply on the list
        :return a paged entity representing the list of dpks.

        ** Example **
        .. code-block:: python
            dpks = dl.dpks.list()
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.DPK)
        elif not isinstance(filters, entities.Filters):
            raise ValueError('Unknown filters type: {!r}'.format(type(filters)))
        elif filters.resource != entities.FiltersResource.DPK:
            raise ValueError('Filters resource must to be FiltersResource.DPK. Got: {!r}'.format(filters.resource))

        if self._project is not None:
            filters.add(field='context.project', values=self._project.id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def _list(self, filters: entities.Filters):
        url = '/app-registry/query'

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def get_revisions(self, dpk_id: str, version: str):
        """
        Get the revision of a specific dpk.

        :param str dpk_id: the id of the dpk.
        :param str version: the version of the dpk.
        :return the entity of the dpk
        :rtype entities.Dpk

        ** Example **
        ..coed-block:: python
            dpk = dl.dpks.get_revisions(dpk_id='id', version='1.0.0')
        """
        if dpk_id is None or version is None:
            raise ValueError('You must provide both dpk_id and version')
        url = '/app-registry/{}/revisions/{}'.format(dpk_id, version)

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        dpk = entities.Dpk.from_json(_json=response.json(),
                                     client_api=self._client_api,
                                     project=self._project,
                                     is_fetched=False)
        return dpk

    def get(self, dpk_name: str = None, dpk_version: str = None, dpk_id: str = None) -> entities.Dpk:
        """
        Get a specific dpk from the platform.

        Note: you must pass either dpk_id or dpk_name.

        :param str dpk_id: the id of the dpk to get.
        :param str dpk_name: the name of the dpk to get.
        :param str dpk_version: options - to get a specific dpk version
        :return the entity of the dpk
        :rtype entities.Dpk

        ** Example **
        ..coed-block:: python
            dpk = dl.dpks.get(dpk_name='name')
        """
        if dpk_id is None and dpk_name is None:
            raise ValueError('You must provide an identifier, either dpk_id or dpk_name')
        if dpk_id is not None:
            url = '/app-registry/{}'.format(dpk_id)

            # request
            success, response = self._client_api.gen_request(req_type='get',
                                                             path=url)
            if not success:
                raise exceptions.PlatformException(response)

            dpk = entities.Dpk.from_json(_json=response.json(),
                                         client_api=self._client_api,
                                         project=self._project,
                                         is_fetched=False)
        else:
            dpk = self.__get_by_name(dpk_name=dpk_name, dpk_version=dpk_version)

        return dpk
