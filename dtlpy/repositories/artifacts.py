import os
import logging
from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize

from .. import entities, services, utilities

logger = logging.getLogger('dataloop.artifaces')


class Artifacts:
    """
    Artifacts repository
    """

    def __init__(self, session=None, package=None):
        self.client_api = services.ApiClient()
        if session is not None and package is not None:
            logger.exception('Need one none None input')
            raise ValueError
        self._artifacts = list()
        self._session = session
        self._package = package

    def _get_url(self):
        if self._package is not None:
            return '/packages/%s' % self._package.id
        elif self._session is not None:
            return '/sessions/%s' % self._session.id
        else:
            logger.exception('no package or session')
            raise ValueError

    def list(self):
        """
        List of artifacts
        :return:
        """
        url = self._get_url()
        success = self.client_api.gen_request('get', url + '/artifacts')
        if success:
            artifacts = utilities.List([entities.Artifact(entity_dict=entity_dict) for entity_dict in
                                        self.client_api.last_response.json()])
        else:
            logger.exception('Error getting artifacts list from platform')
            raise self.client_api.platform_exception
        return artifacts

    def create(self, artifact_name='', artifact_type='', description=''):
        """
        Create a new artifact
        :param artifact_name:
        :param artifact_type:
        :param description:
        :return:
        """
        payload = {'name': artifact_name, 'type': artifact_type, 'description': description}
        url = self._get_url()
        success = self.client_api.gen_request(req_type='post',
                                              path=url + '/artifacts',
                                              data=payload)
        if success:
            artifact = entities.Artifact(entity_dict=self.client_api.last_response.json())
            return artifact
        else:
            logger.exception('Artifact id was not created')
            raise self.client_api.platform_exception

    def get(self, artifact_id=None, artifact_name=None, artifact_type=None):
        """
        Get an artifact object by name, id or type
        :param artifact_id: optional - search by id
        :param artifact_name: optional - search by name
        :param artifact_type: optional - search by type
        :return:
        """
        artifacts = self.list()
        if artifact_id is not None:
            artifact = [artifact for artifact in artifacts if artifact.id == 'id']
        elif artifact_name is not None:
            artifact = [artifact for artifact in artifacts if artifact.name == artifact_name]
        elif artifact_type is not None:
            artifact = [artifact for artifact in artifacts if artifact.type == artifact_type]
        else:
            logger.exception('Missing search params for "get"')
            raise ValueError('Missing search params for "get"')
        if len(artifact) == 1:
            artifact = artifact[0]
        else:
            artifact = None
        return artifact

    def download(self, artifact_id=None, artifact_name=None, artifact_type=None,
                 local_path=None, download_options=None, chunk_size=8192):
        """
        Download artifact binary to disk. get artifact by name, id or type
        :param artifact_id: optional - search by id
        :param artifact_name: optional - search by name
        :param artifact_type: optional - search by type
        :param local_path: artifact will be saved to this filepath
        :param download_options: 'merge' or 'overwrite'
        :param chunk_size: defaule - 8192
        :return:
        """
        artifact = self.get(artifact_id=artifact_id, artifact_name=artifact_name, artifact_type=artifact_type)
        if artifact is None:
            logger.exception('Artifact was not found. id: %s, name: %s, type: %s' % (artifact_id, artifact_name, artifact_type))
            raise ValueError('Artifact was not found. id: %s, name: %s, type: %s' % (artifact_id, artifact_name, artifact_type))
        if download_options is None:
            download_options = 'overwrite'
        if local_path is None:
            local_path = os.getcwd()
        if artifact_name is None:
            artifact_name = artifact.name
        if not os.path.isdir(local_path):
            os.makedirs(local_path)
        local_filename = os.path.join(local_path, artifact_name)
        # checking if directory already exists
        if os.path.isfile(local_filename):
            logger.info('Local file already exists: %s' % local_filename)
            if download_options.lower() == 'overwrite':
                # dont use cached dataset
                logger.warning('download_options flag is overwrite. deleting local directory: %s' % local_filename)
                os.remove(local_filename)
            else:
                # use cached dataset
                logger.info(
                    'file exists. To overwrite set the "download_options" flag to "overwrite". %s' % local_filename)
                return local_filename

        # download
        success = self.client_api.gen_request(req_type='get',
                                              path='/artifacts/%s/body?name=%s' % (artifact.id, artifact.name),
                                              stream=True)
        if not success:
            raise self.client_api.platform_exception

        resp = self.client_api.last_response

        total_length = resp.headers.get('content-length')
        pbar = ProgressBar(
            widgets=
            [' [', Timer(), '] ', Bar(), ' (', FileTransferSpeed(), ' | ', DataSize(), ' | ', ETA(), ')'])
        pbar.max_value = total_length
        dl = 0
        with open(local_filename, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    dl += len(chunk)
                    pbar.update(dl)
                    f.write(chunk)
        pbar.finish()
        return local_filename

    def upload(self, filepath, artifact_id=None, artifact_name=None, artifact_type=None, description=None, create=True):
        """
        Upload binary file to artifact. get by name, id or type.
        If artifact exists - overwriting binary
        Else and if create==True a new artifact will be created and uploaded
        :param filepath: local binary file
        :param artifact_id: optional - search by id
        :param artifact_name: optional - search by name
        :param artifact_type: optional - search by type
        :param description:
        :param create: bool. Create new artifact
        :return:
        """
        if not artifact_name:
            artifact_name = os.path.basename(filepath)

        artifact = self.get(artifact_id=artifact_id, artifact_name=artifact_name, artifact_type=artifact_type)
        if artifact is None:
            # create new artifact for the model
            artifact = self.create(artifact_name=artifact_name, artifact_type=artifact_type, description=description)
            logger.warning('Artifact was not found. New artifact created. id: %s' % artifact.id)
        # prepare request
        success = self.client_api.upload_local_file(filepath=filepath,
                                                    remote_url='/artifacts/%s/body' % artifact.id,
                                                    uploaded_filename=artifact_name)
        if success:
            return artifact
        else:
            logger.exception('Artifact id was not created. session_id: %s' % self._session.id)
            raise self.client_api.platform_exception

    def delete(self):
        pass

    def edit(self):
        pass
