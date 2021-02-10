import hashlib
import logging
import os
import io
import random

from .. import entities, PlatformException, exceptions, repositories, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Codebases:
    """
    Codebases repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None,
                 project_id: str = None):
        self._client_api = client_api
        if project is None and dataset is None:
            if project_id is None:
                raise PlatformException('400', 'at least one must be not None: dataset, project or project_id')
            else:
                project = repositories.Projects(client_api=client_api).get(project_id=project_id)
        self._project = project
        self._dataset = dataset
        self._items_repository = None

    @property
    def items_repository(self) -> repositories.Items:
        if self._items_repository is None:
            self._items_repository = self.dataset.items
        assert isinstance(self._items_repository, repositories.Items)
        return self._items_repository

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            self._project = self.dataset.project
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            # get dataset from project
            try:
                self._dataset = self.project.datasets.get(dataset_name='Binaries')
            except exceptions.NotFound:
                self._dataset = None
            if self._dataset is None:
                logger.debug(
                    'Dataset for codebases was not found. Creating... dataset name: "Binaries". project_id={}'.format(
                        self.project.id))
                self._dataset = self.project.datasets.create(dataset_name='Binaries')
                # add system to metadata
                if 'metadata' not in self._dataset.to_json():
                    self._dataset.metadata = dict()
                if 'system' not in self._dataset.metadata:
                    self._dataset.metadata['system'] = dict()
                self._dataset.metadata['system']['scope'] = 'system'
                self.project.datasets.update(dataset=self._dataset, system_metadata=True)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @staticmethod
    def __file_hash(filepath):
        m = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                m.update(chunk)
        return m.hexdigest()

    def list_versions(self, codebase_name):
        """
        List all codebase versions

        :param codebase_name: code base name
        :return: list of versions
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/codebases/{}/*'.format(codebase_name))
        versions = self.items_repository.list(filters=filters)
        return versions

    def list(self) -> entities.PagedEntities:
        """
        List all code bases
        :return: Paged entity
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/codebases/*')
        filters.add(field='type', values='dir')
        codebases = self.items_repository.list(filters=filters)
        return codebases

    def get(self, codebase_name=None, codebase_id=None, version=None):
        """
        Get a Codebase object
        :param version: codebase version. default is latest. options: "all", "latests" or ver number - "10"
        :param codebase_id: optional - search by id
        :param codebase_name: optional - search by name
        :return: Codebase object
        """
        if codebase_id is not None:
            matched_version = self.items_repository.get(item_id=codebase_id)
            # verify input codebase name is same as the given id
            if codebase_name is not None and matched_version.name != codebase_name:
                logger.warning(
                    "Mismatch found in codebases.get: codebase_name is different then codebase.name: "
                    "{!r} != {!r}".format(
                        codebase_name,
                        matched_version.name))
            codebase = entities.ItemCodebase(item_id=matched_version.id,
                                             item=matched_version)
            return codebase

        if codebase_name is None:
            raise PlatformException(error='400', message='Either "codebase_name" or "codebase_id" is needed')
        if version is None:
            version = 'latest'

        if version not in ['all', 'latest']:
            try:
                matched_version = self.items_repository.get(
                    filepath='/codebases/{}/{}.zip'.format(codebase_name, version))
            except Exception:
                raise PlatformException(error='404',
                                        message='No matching version was found. version: {}'.format(version))
            codebase = entities.ItemCodebase(item_id=matched_version.id,
                                             item=matched_version)
            return codebase

        # get all or latest
        versions_pages = self.list_versions(codebase_name=codebase_name)
        if versions_pages.items_count == 0:
            raise PlatformException(error='404', message='No codebase was found. name: {}'.format(codebase_name))
        else:
            if version == 'all':
                codebase = [entities.ItemCodebase(item_id=mv.id,
                                                  item=mv) for mv in versions_pages.all()]
            elif version == 'latest':
                max_ver = -1
                matched_version = None
                for page in versions_pages:
                    for ver in page:
                        if ver.type == 'dir':
                            continue
                        # extract version from filepath
                        ver_int = int(os.path.splitext(ver.name)[0])
                        if ver_int > max_ver:
                            max_ver = ver_int
                            matched_version = ver
                if matched_version is None:
                    raise PlatformException(error='404',
                                            message='No codebase was found. name: {}'.format(codebase_name))
                else:
                    codebase = entities.ItemCodebase(item_id=matched_version.id,
                                                     item=matched_version)
            else:
                raise PlatformException(error='404', message='Unknown version string: {}'.format(version))

        return codebase

    @staticmethod
    def get_current_version(all_versions_pages, zip_md):
        latest_version = 0
        same_version_found = None
        # go over all existing versions
        for v_item in all_versions_pages:
            # get latest version
            if int(os.path.splitext(v_item.item.name)[0]) > latest_version:
                latest_version = int(os.path.splitext(v_item.item.name)[0])
            # check md5 to find same codebase
            if 'md5' in v_item.item.metadata['system'] and v_item.item.metadata['system']['md5'] == zip_md:
                same_version_found = v_item
                break
        return latest_version + 1, same_version_found

    def pack(self, directory, name=None, description=''):
        """
        Zip a local code directory and post to codebases
        :param directory: local directory to pack
        :param name: codebase name
        :param description: codebase description
        :return: Codebase object
        """
        # create/get .dataloop dir
        cwd = os.getcwd()
        dl_dir = os.path.join(cwd, '.dataloop')
        if not os.path.isdir(dl_dir):
            os.mkdir(dl_dir)

        # get codebase name
        if name is None:
            name = os.path.basename(directory)

        # create/get dist folder
        zip_filename = os.path.join(dl_dir, '{}_{}.zip'.format(name, str(random.randrange(0, 1000))))

        try:
            if not os.path.isdir(directory):
                raise PlatformException(error='400', message='Not a directory: {}'.format(directory))
            directory = os.path.abspath(directory)

            # create zipfile
            miscellaneous.Zipping.zip_directory(zip_filename=zip_filename, directory=directory)
            zip_md = self.__file_hash(zip_filename)

            # get latest version
            same_version_found = None
            try:
                all_versions_pages = self.get(codebase_name=name, version='all')
            except exceptions.NotFound:
                all_versions_pages = None
            if all_versions_pages is None:
                # no codebase with that name - create new version
                current_version = 0
            else:
                current_version, same_version_found = self.get_current_version(all_versions_pages=all_versions_pages,
                                                                               zip_md=zip_md)

            if same_version_found is not None:
                # same md5 hash file found in version - return the matched version
                codebase = same_version_found
            else:
                # no matched version was found - create a new version
                # read from zipped file
                with open(zip_filename, 'rb') as f:
                    buffer = io.BytesIO(f.read())
                    buffer.name = str(current_version) + '.zip'

                # upload item
                item = self.items_repository.upload(local_path=buffer,
                                                    remote_path='/codebases/{}'.format(name))
                if isinstance(item, list) and len(item) == 0:
                    raise PlatformException(error='400', message='Failed upload codebase, check log file for details')

                # add source code to metadata
                if 'system' not in item.metadata:
                    item.metadata['system'] = dict()
                item.metadata['system']['description'] = description
                item.metadata['system']['md5'] = zip_md

                # add git info to metadata
                if miscellaneous.GitUtils.is_git_repo(path=directory):
                    # create 'git' field in metadata
                    if 'git' not in item.metadata:
                        item.metadata['git'] = dict()

                    # add to metadata
                    item.metadata['git']['status'] = miscellaneous.GitUtils.git_status(path=directory)
                    item.metadata['git']['log'] = miscellaneous.GitUtils.git_log(path=directory)
                    item.metadata['git']['url'] = miscellaneous.GitUtils.git_url(path=directory)

                # update item
                item = self.items_repository.update(item=item, system_metadata=True)
                codebase = entities.ItemCodebase(item_id=item.id,
                                                 client_api=self._client_api)
        except Exception:
            logger.error('Error when packing:')
            raise
        finally:
            # cleanup
            if zip_filename is not None:
                if os.path.isfile(zip_filename):
                    os.remove(zip_filename)
        return codebase

    def unpack_single(self,
                      codebase,
                      download_path, local_path):
        # downloading with specific filename
        if isinstance(codebase, entities.ItemCodebase):
            artifact_filepath = self.items_repository.download(items=codebase.item_id,
                                                               save_locally=True,
                                                               local_path=os.path.join(download_path,
                                                                                       codebase.item.name),
                                                               to_items_folder=False)
            if not os.path.isfile(artifact_filepath):
                raise PlatformException(error='404',
                                        message='error downloading codebase. see above for more information')
            miscellaneous.Zipping.unzip_directory(zip_filename=artifact_filepath,
                                                  to_directory=local_path)
            os.remove(artifact_filepath)
        elif isinstance(codebase, entities.Item):
            artifact_filepath = codebase.download(save_locally=True,
                                                  local_path=os.path.join(download_path,
                                                                          codebase.name),
                                                  to_items_folder=False)
            if not os.path.isfile(artifact_filepath):
                raise PlatformException(error='404',
                                        message='error downloading codebase. see above for more information')
            miscellaneous.Zipping.unzip_directory(zip_filename=artifact_filepath,
                                                  to_directory=local_path)
            os.remove(artifact_filepath)
        else:
            raise ValueError('Not implemented: "unpack_single" for codebase type: {!r}'.format(codebase.type))
        return artifact_filepath

    def unpack(self, codebase_name=None, codebase_id=None, local_path=None, version=None):
        """
        Unpack codebase locally. Download source code and unzip
        :param codebase_name: search by name
        :param codebase_id: search by id
        :param local_path: local path to save codebase
        :param version: codebase version to unpack. default - latest
        :return: String (dirpath)
        """
        codebase = self.get(codebase_name=codebase_name,
                            codebase_id=codebase_id,
                            version=version)
        download_path = local_path
        if isinstance(codebase, entities.PagedEntities):
            for page in codebase:
                for item in page:
                    local_path = os.path.join(download_path, 'v.' + item.name.split('.')[0])
                    self.unpack_single(codebase=item,
                                       download_path=download_path,
                                       local_path=local_path)
            return os.path.dirname(local_path)
        elif isinstance(codebase, list):
            for item in codebase:
                local_path = os.path.join(download_path, 'v.' + item.item.name.split('.')[0])
                self.unpack_single(codebase=item,
                                   download_path=download_path,
                                   local_path=local_path)
            return os.path.dirname(local_path)
        elif isinstance(codebase, entities.Codebase) or isinstance(codebase, entities.Item):
            artifact_filepath = self.unpack_single(codebase=codebase,
                                                   download_path=download_path,
                                                   local_path=local_path)
            logger.info('Source code was unpacked to: {}'.format(os.path.dirname(artifact_filepath)))
        else:
            raise PlatformException(
                error='404',
                message='Codebase was not found! name:{name}, id:{id}'.format(name=codebase_name,
                                                                              id=codebase_id))
        return os.path.dirname(artifact_filepath)
