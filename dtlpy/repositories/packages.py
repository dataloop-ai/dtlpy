import hashlib
import traceback
import logging
import os

from .. import services, entities, utilities


class Packages:
    """
    Packages repository
    """

    def __init__(self, project=None, dataset=None):
        self.logger = logging.getLogger('dataloop.packages')
        self.client_api = services.ApiClient()
        if project is None and dataset is None:
            self.logger.exception('at least one must be not None: dataset or project')
            raise ValueError('at least one must be not None: dataset or project')
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
            self._dataset = self.project.datasets.get(dataset_name='Binaries')
            if self._dataset is None:
                self.logger.warning(
                    'Dataset for packages was not found. Creating... dataset name: "Binaries". project_id=%s' % self.project.id)
                self._dataset = self.project.datasets.create(dataset_name='Binaries')
                # add system to metadata
                self._dataset.entity_dict['metadata']['system']['scope'] = 'system'
                self.project.datasets.edit(dataset=self._dataset, system_metadata=True)
        return self._dataset

    @staticmethod
    def __file_hash(filepath):
        m = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                m.update(chunk)
        return m.hexdigest()

    def list_versions(self, package_name):
        versions = self.items_repository.list(query={'directories': ['/packages/%s' % package_name]})
        return versions

    def list(self):
        """
        List all packages
        :return:
        """
        packages = self.items_repository.list(query={'directories': ['/packages']})
        return packages

    def edit(self):
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
            raise ValueError('Need to input only least of "package_name" or "package_id"')
        if version is None:
            version = 'latest'

        if version not in ['all', 'latest']:
            matched_version = self.items_repository.get(filepath='/packages/%s/%s.zip' % (package_name, version))
            if matched_version is None:
                self.logger.warning('No matching version was found. version: %s' % version)
            return matched_version
        # get all or latest

        # list all packages
        versions_pages = self.list_versions(package_name=package_name)
        if versions_pages.items_count == 0:
            self.logger.warning('No package was found. name: %s' % package_name)
            matched_version = None
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
            else:
                raise ValueError('unknown version string: %s' % version)
        return matched_version

    def pack(self, directory, name=None, description=''):
        """
        Zip a local code directory and post to packages
        :param directory: local directory to pack
        :param name: package name
        :param description: package description
        :return:
        """
        zip_filename = None
        try:
            if not os.path.isdir(directory):
                self.logger.exception('Not a directory: %s' % directory)
                raise ValueError('Not a directory: %s' % directory)
            directory = os.path.abspath(directory)
            # create zipfile
            utilities.Miscellaneous.zip_directory(directory)
            zip_filename = directory + '.zip'

            zip_md = self.__file_hash(zip_filename)

            # get package name
            if name is None:
                name = os.path.basename(directory)

            # get latest version
            same_version_found = None
            all_versions_pages = self.get(package_name=name, version='all')
            if all_versions_pages is None:
                # no package with that name - create new version
                current_version = 0
            else:
                latest_version = 0
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
                current_version = latest_version + 1

            if same_version_found is not None:
                # same md5 hash file found in version - return the matched version
                item = same_version_found
            else:
                # no matched version was found - create a new version
                item = self.items_repository.upload(filepath=zip_filename,
                                                    remote_path='/packages/%s' % name,
                                                    uploaded_filename=str(current_version) + '.zip')
                if item is None:
                    self.logger.exception('unable to create package item.')
                    raise self.client_api.platform_exception

                # add metadata to source code
                item.entity_dict['metadata']['system']['description'] = description
                item.entity_dict['metadata']['system']['md5'] = zip_md
                item = self.items_repository.edit(item=item, system_metadata=True)
            return item

        except Exception as e:
            self.logger.exception('%s\n%s' % (e, traceback.format_exc()))
            raise
        finally:
            # cleanup
            if zip_filename is not None:
                if os.path.isfile(zip_filename):
                    os.remove(zip_filename)

    def unpack(self, package_name=None, package_id=None, local_path=None, version=None):
        """
        Unpack package locally. Download source code and unzip
        :param package_name: search by name
        :param local_path: local path to save package source
        :param version: package version to unpack. default - latest
        :return:
        """
        package = self.get(package_name=package_name, package_id=package_id, version=version)
        download_path = local_path
        if not (local_path.endswith('/*') or local_path.endswith('\*')):
            # add * to download directly to folder
            download_path = os.path.join(local_path, '*')
        artifact_filepath = self.items_repository.download(item_id=package.id,
                                                           save_locally=True,
                                                           local_path=download_path,
                                                           download_options={'relative_path': False})
        utilities.Miscellaneous.unzip_directory(zip_filename=artifact_filepath,
                                                to_directory=local_path)
        # to_directory=os.path.dirname(os.path.dirname(artifact_filepath)))
        os.remove(artifact_filepath)
        self.logger.info('Source code was unpacked to: %s' % os.path.dirname(artifact_filepath))
        return os.path.dirname(artifact_filepath)
