import hashlib
import traceback
import logging
import os
import shutil
import io
import random

from .. import entities, utilities, PlatformException, exceptions


class Packages:
    """
    Packages repository
    """

    def __init__(self, client_api, project=None, dataset=None):
        self.logger = logging.getLogger('dataloop.packages')
        self.client_api = client_api
        if project is None and dataset is None:
            self.logger.exception('at least one must be not None: dataset or project')
            raise PlatformException('400', 'at least one must be not None: dataset or project')
        self.project = project
        self._dataset = dataset
        self._items_repository = None

    @property
    def items_repository(self):
        if self._items_repository is None:
            # load Binaries dataset

            # load items repository
            self._items_repository = self.dataset.items
            self._items_repository.set_items_entity(entities.Package)
        return self._items_repository

    @property
    def dataset(self):
        if self._dataset is None:
            # get dataset from project
            try:
                self._dataset = self.project.datasets.get(dataset_name='Binaries')
            except exceptions.NotFound:
                self._dataset = None
            if self._dataset is None:
                self.logger.warning(
                    'Dataset for packages was not found. Creating... dataset name: "Binaries". project_id={}'.format(self.project.id))
                self._dataset = self.project.datasets.create(dataset_name='Binaries')
                # add system to metadata
                if 'metadata' not in self._dataset.to_json():
                    self._dataset.metadata = dict()
                if 'system' not in self._dataset.metadata:
                    self._dataset.metadata['system'] = dict()
                self._dataset.metadata['system']['scope'] = 'system'
                self.project.datasets.update(dataset=self._dataset, system_metadata=True)
        return self._dataset

    @staticmethod
    def __file_hash(filepath):
        m = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                m.update(chunk)
        return m.hexdigest()

    def list_versions(self, package_name):
        """
        List all package versions

        :param package_name: package name
        :return: list of versions
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/packages/{}/*'.format(package_name))
        versions = self.items_repository.list(filters=filters)
        return versions

    def list(self):
        """
        List all packages
        :return: Paged entity
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/packages/*')
        filters.add(field='type', values='dir')
        packages = self.items_repository.list(filters=filters)
        return packages

    def update(self):
        pass

    def delete(self):
        pass
        # # delete all
        # return self.gen_request('delete', '/packages/%s' % package_id)
        # # delete from project
        # return self.gen_request('delete', '/projects/%s/packages/%s' % (project_id, package_id))

    def get(self, package_name=None, package_id=None, version=None):
        """
        Get a Package object
        :param version: package version. default is latest. options: "all", "latests" or ver number - "10"
        :param package_id: optional - search by id
        :param package_name: optional - search by name
        :return: Package object
        """
        if package_id is not None:
            matched_version = self.items_repository.get(item_id=package_id)
            return matched_version

        if package_name is None:
            raise PlatformException('400', 'Either "package_name" or "package_id" is needed')
        if version is None:
            version = 'latest'

        if version not in ['all', 'latest']:
            try:
                matched_version = self.items_repository.get(filepath='/packages/%s/%s.zip' % (package_name, version))
            except Exception:
                self.logger.warning('No matching version was found. version: %s' % version)
                message = ('No matching version was found. version: %s' % version)
                raise PlatformException('404', message)
            return matched_version

        # get all or latest
        versions_pages = self.list_versions(package_name=package_name)
        if versions_pages.items_count == 0:
            self.logger.warning('No package was found. name: %s' % package_name)
            message = ('No package was found. name: %s' % package_name)
            raise PlatformException('404', message)
        else:
            if version == 'all':
                matched_version = versions_pages
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
                    message = ('No package was found. name: %s' % package_name)
                    raise PlatformException('404', message)
            else:
                message = ('unknown version string: %s' % version)
                raise PlatformException('404', message)

        return matched_version

    def get_current_version(self, all_versions_pages, zip_md):
        latest_version = 0
        same_version_found = None
        # go over all existing versions
        for page in all_versions_pages:
            for v_item in page:
                # get latest version
                if int(os.path.splitext(v_item.name)[0]) > latest_version:
                    latest_version = int(os.path.splitext(v_item.name)[0])
                # check md5 to find same package
                if v_item.md5 == zip_md:
                    same_version_found = v_item
                    break
        return latest_version + 1, same_version_found

    def pack(self, directory, name=None, description=''):
        """
        Zip a local code directory and post to packages
        :param directory: local directory to pack
        :param name: package name
        :param description: package description
        :return: Package object
        """

        cwd = os.getcwd()
        temp_path = str(random.randrange(1000, 100000))
        dist_path = os.path.join(cwd, '.dataloop', temp_path, 'dist')
        zip_filename = None
        try:
            if not os.path.isdir(directory):
                self.logger.exception('Not a directory: %s' % directory)
                message = ('Not a directory: %s' % directory)
                raise PlatformException('400', message)
            directory = os.path.abspath(directory)

            if os.path.isdir(dist_path):
                shutil.rmtree(dist_path)
            shutil.copytree(directory, dist_path)

            # create zipfile
            utilities.Miscellaneous.zip_directory(dist_path)
            zip_filename = dist_path + '.zip'
            zip_md = self.__file_hash(zip_filename)

            # get package name
            if name is None:
                name = os.path.basename(directory)

            # get latest version
            same_version_found = None
            try:
                all_versions_pages = self.get(package_name=name, version='all')
            except exceptions.NotFound:
                all_versions_pages = None
            if all_versions_pages is None:
                # no package with that name - create new version
                current_version = 0
            else:
                current_version, same_version_found = self.get_current_version(all_versions_pages=all_versions_pages,
                                                                               zip_md=zip_md)

            if same_version_found is not None:
                # same md5 hash file found in version - return the matched version
                item = same_version_found
            else:
                # no matched version was found - create a new version

                with open(zip_filename, 'rb') as f:
                    buffer = io.BytesIO(f.read())
                    buffer.name = str(current_version) + '.zip'
                item = self.items_repository.upload(local_path=buffer,
                                                    remote_path='/packages/%s' % name)
                if isinstance(item, list) and len(item) == 0:
                    raise PlatformException(error='400', message='Failed upload package, check log file for details')

                # add metadata to source code
                item.metadata['system']['description'] = description
                item.metadata['system']['md5'] = zip_md
                item = self.items_repository.update(item=item, system_metadata=True)
            return item

        except Exception as e:
            self.logger.exception('%s\n%s' % (e, traceback.format_exc()))
            raise
        finally:
            # cleanup
            if zip_filename is not None:
                if os.path.isfile(zip_filename):
                    os.remove(zip_filename)

            if os.path.exists(dist_path):
                shutil.rmtree(dist_path)

    def unpack_single(self, package, download_path, local_path):
        # downloading with specific filename
        artifact_filepath = self.items_repository.download(items=package.id,
                                                           save_locally=True,
                                                           local_path=os.path.join(download_path, package.name),
                                                           to_items_folder=False)
        if not os.path.isfile(artifact_filepath):
            raise PlatformException(error='404',
                                    message='error downloading package. see above for more information')
        utilities.Miscellaneous.unzip_directory(zip_filename=artifact_filepath,
                                                to_directory=local_path)
        os.remove(artifact_filepath)
        return artifact_filepath

    def unpack(self, package_name=None, package_id=None, local_path=None, version=None):
        """
        Unpack package locally. Download source code and unzip
        :param package_name: search by name
        :param package_id: search by id
        :param local_path: local path to save package source
        :param version: package version to unpack. default - latest
        :return: String (dirpath)
        """
        package = self.get(package_name=package_name, package_id=package_id, version=version)
        download_path = local_path
        if isinstance(package, entities.PagedEntities):
            for page in package:
                for item in page:
                    local_path = os.path.join(download_path, 'v.' + item.name.split('.')[0])
                    self.unpack_single(package=item, download_path=download_path, local_path=local_path)
            return os.path.dirname(local_path)
        elif isinstance(package, entities.Package):
            artifact_filepath = self.unpack_single(package=package, download_path=download_path, local_path=local_path)
            self.logger.info('Source code was unpacked to: %s' % os.path.dirname(artifact_filepath))
        else:
            raise PlatformException(
                error='404',
                message='Package was not found! name:{name}, id:{id}'.format(name=package_name, id=package_id))
        return os.path.dirname(artifact_filepath)
