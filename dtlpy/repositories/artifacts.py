import os
import logging

from .. import entities, miscellaneous, PlatformException, exceptions

logger = logging.getLogger(name=__name__)


class Artifacts:
    """
    Artifacts repository
    """

    def __init__(self, client_api, project=None, dataset=None):
        self._client_api = client_api
        if project is None and dataset is None:
            raise PlatformException('400', 'at least one must be not None: dataset or project')
        self._project = project
        self._dataset = dataset
        self._items_repository = None

    @property
    def project(self):
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def items_repository(self):
        if self._items_repository is None:
            # load Binaries dataset

            # load items repository
            self._items_repository = self.dataset.items
            self._items_repository.set_items_entity(entities.Artifact)
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
                logger.debug(
                    'Dataset for artifacts was not found. Creating... dataset name: "Binaries". project_id={id}'.format(
                        id=self.project.id))
                self._dataset = self.project.datasets.create(dataset_name='Binaries')
                # add system to metadata
                if 'metadata' not in self._dataset.to_json():
                    self._dataset.metadata = dict()
                if 'system' not in self._dataset.metadata:
                    self._dataset.metadata['system'] = dict()
                self._dataset.metadata['system']['scope'] = 'system'
                self.project.datasets.update(dataset=self._dataset, system_metadata=True)
        return self._dataset

    def list(self, session_id=None, plugin_name=None):
        """
        List of artifacts
        :return: list of artifacts
        """
        filters = entities.Filters()
        remote_path = '/artifacts'
        if plugin_name is not None:
            remote_path += '/plugins/{}'.format(plugin_name)
        if session_id is not None:
            remote_path += '/sessions/{}'.format(session_id)
        remote_path += '/*'
        filters.add(field='filename', values=remote_path)
        pages = self.items_repository.list(filters=filters)
        items = [item for page in pages for item in page]
        return miscellaneous.List(items)

    def get(self, artifact_id=None, artifact_name=None,
            session_id=None, plugin_name=None):
        """

        Get an artifact object by name, id or type
        If by name or type - need to input also session/task id for the artifact folder
        :param plugin_name:
        :param artifact_id: optional - search by id
        :param artifact_name:
        :param session_id:
        :return: Artifact object
        """
        if artifact_id is not None:
            artifact = self.items_repository.get(item_id=artifact_id)
            return artifact
        elif artifact_name is not None:
            artifacts = self.list(session_id=session_id, plugin_name=plugin_name)
            artifact = [artifact for artifact in artifacts if artifact.name == artifact_name]
            if len(artifact) == 1:
                artifact = artifact[0]
            else:
                raise PlatformException('404', 'Artifact not found')
            return artifact
        else:
            msg = 'one input must be not None: artifact_id or artifact_name'
            raise ValueError(msg)

    def download(self, artifact_id=None, artifact_name=None,
                 session_id=None, plugin_name=None,
                 local_path=None, overwrite=False):
        """

        Download artifact binary.
        Get artifact by name, id or type

        :param overwrite: optional - default = False
        :param artifact_id: optional - search by id
        :param local_path: artifact will be saved to this filepath
        :param artifact_name:
        :param session_id:
        :param plugin_name:
        :return: Artifact object
        """
        if artifact_id is not None:
            artifact = self.items_repository.download(item_id=artifact_id,
                                                      save_locally=True,
                                                      local_path=local_path,
                                                      overwrite=overwrite)
            return artifact

        if artifact_name is None:
            directories = '/artifacts'
            if plugin_name is not None:
                directories += '/plugins/{}'.format(plugin_name)
            if session_id is not None:
                directories = '/sessions/{}'.format(session_id)
            directories += '/*'.format(plugin_name)
            if all(elem is None for elem in [plugin_name, session_id]):
                raise PlatformException(error='400', message='Must input plugin or session (id or entity)')

            filters = entities.Filters()
            filters.add(field='filename', values=directories)
            if not (local_path.endswith('/*') or local_path.endswith(r'\*')):
                # download directly to folder
                local_path = os.path.join(local_path, '*')
            self.items_repository.download(filters=filters,
                                           save_locally=True,
                                           local_path=local_path,
                                           overwrite=overwrite)

        else:
            artifact = self.get(artifact_id=artifact_id,
                                session_id=session_id,
                                plugin_name=plugin_name,
                                artifact_name=artifact_name)

            artifact.download(save_locally=True,
                              local_path=local_path,
                              overwrite=overwrite)
            return artifact

    def upload(self,
               # what to upload
               filepath,
               # where to upload
               plugin_name=None, plugin=None, session_id=None, session=None,
               # add information
               overwrite=False):
        """

        Upload binary file to artifact. get by name, id or type.
        If artifact exists - overwriting binary
        Else and if create==True a new artifact will be created and uploaded

        :param overwrite: optional - default = False
        :param filepath: local binary file
        :param plugin_name:
        :param plugin:
        :param session_id:
        :param session:
        :return: Artifact Object
        """
        remote_path = '/artifacts'
        if plugin_name is not None or plugin is not None:
            if plugin is not None:
                plugin_name = plugin.name
            remote_path += '/plugins/{}'.format(plugin_name)
        if session_id is not None or session is not None:
            if session is not None:
                session_id = session.id
            remote_path += '/sessions/{}'.format(session_id)

        if all(elem is None for elem in [plugin_name, plugin, session_id, session]):
            raise ValueError('Must input plugin or session (id or entity)')

        if os.path.isfile(filepath):
            artifact = self.items_repository.upload(local_path=filepath,
                                                    remote_path=remote_path,
                                                    overwrite=overwrite)
        elif os.path.isdir(filepath):
            if not (filepath.endswith('/*') or filepath.endswith(r'\*')):
                # upload directly to folder
                filepath = os.path.join(filepath, '*')
            artifact = self.items_repository.upload(local_path=filepath,
                                                    remote_path=remote_path,
                                                    overwrite=overwrite)
        else:
            raise ValueError('Missing file or directory: %s' % filepath)
        logger.debug('Artifact uploaded successfully')
        return artifact
