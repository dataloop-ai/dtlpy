import os
import logging
from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize

from .. import entities, services, utilities, repositories


class Artifacts:
    """
    Artifacts repository
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

    def list(self, session_id=None, task_id=None):
            """
            List of artifacts
            :return:
            """
            if session_id is not None:
                pages = self.items_repository.list(query={'directories': ['/artifacts/sessions/%s' % session_id]})
            elif task_id is not None:
                pages = self.items_repository.list(query={'directories': ['/artifacts/tasks/%s' % task_id]})
            else:
                raise ValueError('Must input one search parameter')
            items = [item for page in pages for item in page]
            return items

    def get(self, artifact_id=None, artifact_name=None,
            session_id=None, task_id=None):
        """

        Get an artifact object by name, id or type
        If by name or type - need to input also session/task id for the artifact folder
        :param artifact_id: optional - search by id
        :param artifact_name:
        :param session_id:
        :param task_id:
        :return:
        """
        if artifact_id is not None:
            artifact = self.items_repository.get(item_id=artifact_id)
            return artifact
        elif artifact_name is not None:
            artifacts = self.list(session_id=session_id, task_id=task_id)
            artifact = [artifact for artifact in artifacts if artifact.name == artifact_name]
            if len(artifact) == 1:
                artifact = artifact[0]
            else:
                artifact = None
            return artifact
        else:
            msg = 'one input must be not None: artifact_id or artifact_name'
            raise ValueError(msg)

    def download(self, artifact_id=None, artifact_name=None,
                 session_id=None, task_id=None,
                 local_path=None, download_options=None):
        """

        Download artifact binary.
        Get artifact by name, id or type

        :param artifact_id: optional - search by id
        :param local_path: artifact will be saved to this filepath
        :param download_options: {'overwrite': True/False, 'relative_path':True/False}
        :param artifact_name:
        :param session_id:
        :param task_id:
        :return:
        """
        if download_options is None:
            download_options = {'relative_path': False}
        if artifact_id is not None:
            artifact = self.items_repository.download(item_id=artifact_id,
                                                      save_locally=True,
                                                      local_path=local_path,
                                                      download_options=download_options)
            return artifact

        if artifact_name is None:
            if session_id is not None:
                directories = '/artifacts/sessions/%s' % session_id
            elif task_id is not None:
                directories = '/artifacts/tasks/%s' % task_id
            else:
                raise ValueError('Must input task or session (id or entity)')
            query = {'directories': [directories]}
            if not (local_path.endswith('/*') or local_path.endswith(r'\*')):
                # download directly to folder
                local_path = os.path.join(local_path, '*')
            self.project.datasets.download(dataset_id=self.dataset.id,
                                           query=query,
                                           save_locally=True,
                                           local_path=local_path,
                                           download_options=download_options)
        else:
            artifact = self.get(artifact_id=artifact_id,
                                session_id=session_id,
                                task_id=task_id,
                                artifact_name=artifact_name)

            if artifact is None:
                msg = 'Cant find artifact. remote_filename: %s.' % artifact_name
                self.logger.exception(msg=msg)
                raise ValueError(msg)
            artifact = self.items_repository.download(item_id=artifact.id,
                                                      save_locally=True,
                                                      local_path=local_path,
                                                      download_options=download_options)
            return artifact

    def upload(self,
               # what to upload
               filepath,
               # where to upload
               task_id=None, task=None, session_id=None, session=None,
               # add information
               upload_options=None):
        """

        Upload binary file to artifact. get by name, id or type.
        If artifact exists - overwriting binary
        Else and if create==True a new artifact will be created and uploaded

        :param filepath: local binary file
        :param upload_options: 'merge' or 'overwrite'
        :param task_id:
        :param task:
        :param session_id:
        :param session:
        :return:
        """
        if session_id is not None or session is not None:
            if session is not None:
                session_id = session.id
            remote_path = '/artifacts/sessions/%s' % session_id
        elif task_id is not None or task is not None:
            if task is not None:
                task_id = task.id
            remote_path = '/artifacts/tasks/%s' % task_id
        else:
            raise ValueError('Must input task or session (id or entity)')

        if os.path.isfile(filepath):
            artifact = self.items_repository.upload(filepath=filepath,
                                                    remote_path=remote_path,
                                                    upload_options=upload_options)
        elif os.path.isdir(filepath):
            if not (filepath.endswith('/*') or filepath.endswith(r'\*')):
                # upload directly to folder
                filepath = os.path.join(filepath, '*')
            artifact = self.project.datasets.upload(dataset_id=self.dataset.id,
                                                    local_path=filepath,
                                                    remote_path=remote_path,
                                                    upload_options=upload_options)
        else:
            raise ValueError('Missing file or directory: %s' % filepath)
        return artifact

    def delete(self, artifact_id):
        pass

    def edit(self):
        pass
