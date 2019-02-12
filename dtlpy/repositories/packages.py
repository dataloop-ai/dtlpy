import traceback
import logging
import os

from .. import services, entities, repositories, utilities



class Packages:
    """
    Packages repository
    """

    def __init__(self, project):
        self.logger = logging.getLogger('dataloop.packages')
        self.client_api = services.ApiClient()
        self.project = project
        self.packages = list()

    def list(self):
        """
        List all packages
        :return:
        """
        success = self.client_api.gen_request('get', '/packages')
        if success:
            self.packages = utilities.List([entities.Package(entity_dict=entity_dict) for entity_dict in
                                            self.client_api.last_response.json()])
            return self.packages
        else:
            self.logger.exception('Platform error when listing packages')
            raise self.client_api.platform_exception

    def edit(self):
        pass

    def delete(self):
        pass
        # # delete all
        # return self.gen_request('delete', '/packages/%s' % package_id)
        # # delete from project
        # return self.gen_request('delete', '/projects/%s/packages/%s' % (project_id, package_id))

    def get(self, package_id=None, package_name=None):
        """
        Get a Package object
        :param package_id: optional - search by id
        :param package_name: optional - search by name
        :return: Package object
        """
        if package_id is not None and package_name is not None:
            self.logger.exception('Search by more than one parameter. Using id only')
        if package_id is not None:
            success = self.client_api.gen_request('get', '/packages/%s' % package_id)
            if success:
                res = self.client_api.last_response.json()
                if len(res) > 0:
                    package = entities.Package(entity_dict=res[0])
                else:
                    package = None
            else:
                self.logger.exception('Unable to get package info. package id: %s' % package_id)
                raise self.client_api.platform_exception
        elif package_name is not None:
            packages = self.list()
            package = [package for package in packages if package.name == package_name]
            if len(package) == 0:
                self.logger.warning('No package was found. name: %s' % package_name)
                package = None
            elif len(package) > 1:
                self.logger.exception('More than one package with matching name. Try search by id. name: %s' % package_name)
                assert ValueError('More than one package with matching name. Try search by id. name: %s' % package_name)
            else:
                package = package[0]
        else:
            self.logger.exception('Must input one search parameter!')
            raise ValueError('Must input one search parameter!')

        return package

    def pack(self, directory, name=None, description='', add_to_project=False):
        """
        Zip a local code directory and post to packages
        :param directory: local directory to pack
        :param name: package name
        :param description: package description
        :param add_to_project: bool. add package to project
        :return:
        """
        zip_filename = None
        try:
            if not os.path.isdir(directory):
                self.logger.exception('Not a directory: %s' % directory)
                raise ValueError('Not a directory: %s' % directory)

            utilities.Miscellaneous.zip_directory(directory)
            zip_filename = directory + '.zip'

            # create package
            if name is None:
                name = os.path.basename(directory)
            payload = {'name': name, 'description': description}
            success = self.client_api.gen_request('post', '/packages', data=payload)
            if success:
                package = entities.Package(entity_dict=self.client_api.last_response.json())
            else:
                self.logger.exception('unable to create new model.')
                raise self.client_api.platform_exception

            # create and upload artifact for package
            success = package.artifacts.upload(filepath=zip_filename,
                                               artifact_type='source',
                                               description='source code for ' + name)
            if success:
                artifact = entities.Artifact(entity_dict=self.client_api.last_response.json())
            else:
                self.logger.exception('unable to add artifact to package. package id: %s' % package.id)
                raise self.client_api.platform_exception

            if add_to_project and self.project is not None:
                success = self.client_api.gen_request('post', '/projects/%s/packages' % self.project.id,
                                                      data={'package_id': package.id})
                if not success:
                    self.logger.warning('package was NOT add to project: package_id: %s, project_id: %s' % (
                        package.id, self.project.id))
            return package, artifact

        except Exception as e:
            self.logger.exception('%s\n%s' % (e, traceback.format_exc()))
            raise
        finally:
            # cleanup
            if zip_filename is not None:
                if os.path.isfile(zip_filename):
                    os.remove(zip_filename)

    def unpack(self, package_id=None, package_name=None, local_path=None):
        """
        Unpack package locally. dDownload source code and unzip
        :param package_id: optional - search by id
        :param package_name: optional - search by name
        :param local_path: local path to save package source
        :return:
        """
        package = self.get(package_id=package_id, package_name=package_name)
        artifact_filepath = package.artifacts.download(artifact_type='source', local_path=local_path)
        utilities.Miscellaneous.unzip_directory(zip_filename=artifact_filepath,
                                                to_directory=os.path.dirname(artifact_filepath))
        os.remove(artifact_filepath)
        self.logger.info('Source code was unpacked to: %s' % os.path.dirname(artifact_filepath))
        return os.path.dirname(artifact_filepath)
