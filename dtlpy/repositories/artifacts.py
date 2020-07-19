import logging

from .. import entities, miscellaneous, PlatformException, exceptions, services

logger = logging.getLogger(name=__name__)


class Artifacts:
    """
    Artifacts repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None):
        self._client_api = client_api
        if project is None and dataset is None:
            raise PlatformException('400', 'at least one must be not None: dataset or project')
        self._project = project
        self._dataset = dataset
        self._items_repository = None

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
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

    ################
    # repositories #
    ################
    @property
    def items_repository(self):
        if self._items_repository is None:
            # load Binaries dataset
            # load items repository
            self._items_repository = self.dataset.items
            self._items_repository.set_items_entity(entities.Artifact)
        return self._items_repository

    ###########
    # methods #
    ###########
    @staticmethod
    def _build_path_header(package_name=None, package=None, execution_id=None, execution=None, model_name=None,
                           snapshot_name=None):
        remote_path = '/artifacts'
        if package_name is not None or package is not None:
            if package is not None:
                package_name = package.name
            remote_path += '/packages/{}'.format(package_name)
        if execution_id is not None or execution is not None:
            if execution is not None:
                execution_id = execution.id
            remote_path += '/executions/{}'.format(execution_id)
        if model_name is not None:
            remote_path += '/models/{}'.format(model_name)
        if snapshot_name is not None:
            remote_path += '/snapshots/{}'.format(snapshot_name)

        return remote_path

    def list(self, execution_id=None, package_name=None) -> miscellaneous.List[entities.Artifact]:
        """
        List of artifacts
        :return: list of artifacts
        """
        filters = entities.Filters()
        remote_path = self._build_path_header(package_name=package_name, execution_id=execution_id)
        remote_path += '/*'
        filters.add(field='filename', values=remote_path)
        pages = self.items_repository.list(filters=filters)
        items = [item for page in pages for item in page]
        return miscellaneous.List(items)

    def get(self, artifact_id=None, artifact_name=None,
            execution_id=None, package_name=None) -> entities.Artifact:
        """

        Get an artifact object by name, id or type
        If by name or type - need to input also execution/task id for the artifact folder
        :param package_name:
        :param artifact_id: optional - search by id
        :param artifact_name:
        :param execution_id:
        :return: Artifact object
        """
        if artifact_id is not None:
            artifact = self.items_repository.get(item_id=artifact_id)
            return artifact
        elif artifact_name is not None:
            artifacts = self.list(execution_id=execution_id, package_name=package_name)
            artifact = [artifact for artifact in artifacts if artifact.name == artifact_name]
            if len(artifact) == 1:
                artifact = artifact[0]
            elif len(artifact) > 1:
                raise PlatformException('404', 'More Than one Artifact found')
            else:
                raise PlatformException('404', 'Artifact not found')
            return artifact
        else:
            msg = 'one input must be not None: artifact_id or artifact_name'
            raise ValueError(msg)

    def download(self, artifact_id=None, artifact_name=None,
                 execution_id=None, package_name=None,
                 local_path=None, overwrite=False, save_locally=True):
        """

        Download artifact binary.
        Get artifact by name, id or type

        :param save_locally:
        :param overwrite: optional - default = False
        :param artifact_id: optional - search by id
        :param local_path: artifact will be saved to this filepath
        :param artifact_name:
        :param execution_id:
        :param package_name:
        :return: Artifact object
        """
        if artifact_id is not None:
            artifact = self.items_repository.download(items=artifact_id,
                                                      save_locally=save_locally,
                                                      local_path=local_path,
                                                      overwrite=overwrite)
        elif artifact_name is None:
            if all(elem is None for elem in [package_name, execution_id]):
                raise PlatformException(error='400', message='Must input package or execution (id or entity)')

            remote_path = self._build_path_header(package_name=package_name,
                                                  execution_id=execution_id)
            without_relative_path = remote_path
            remote_path += '/*'
            filters = entities.Filters()
            filters.add(field='filename', values=remote_path)
            artifact = self.items_repository.download(filters=filters,
                                                      save_locally=save_locally,
                                                      local_path=local_path,
                                                      to_items_folder=False,
                                                      overwrite=overwrite,
                                                      without_relative_path=without_relative_path)
        else:
            artifact_obj = self.get(artifact_id=artifact_id,
                                    execution_id=execution_id,
                                    package_name=package_name,
                                    artifact_name=artifact_name)

            artifact = artifact_obj.download(save_locally=save_locally,
                                             local_path=local_path,
                                             overwrite=overwrite)
        return artifact

    def upload(self,
               # what to upload
               filepath,
               # where to upload
               package_name=None, package=None, execution_id=None, execution=None, model_name=None,
               snapshot_name=None,
               # add information
               overwrite=False):
        """

        Upload binary file to artifact. get by name, id or type.
        If artifact exists - overwriting binary
        Else and if create==True a new artifact will be created and uploaded

        :param overwrite: optional - default = False
        :param filepath: local binary file
        :param model_name:
        :param snapshot_name:
        :param package_name:
        :param package:
        :param execution_id:
        :param execution:
        :return: Artifact Object
        """
        remote_path = self._build_path_header(package_name=package_name,
                                              package=package,
                                              execution=execution,
                                              execution_id=execution_id,
                                              model_name=model_name,
                                              snapshot_name=snapshot_name)

        if all(elem is None for elem in [package_name, package, execution_id, execution, model_name, snapshot_name]):
            raise ValueError('Must input package or execution (id or entity)')

        artifact = self.items_repository.upload(local_path=filepath,
                                                remote_path=remote_path,
                                                overwrite=overwrite)

        logger.debug('Artifact uploaded successfully')
        return artifact

    def delete(self, artifact_id=None, artifact_name=None, execution_id=None, package_name=None):
        if artifact_id is not None or artifact_name is not None:
            artifacts = [self.get(artifact_id=artifact_id, artifact_name=artifact_name)]
        elif execution_id is not None or package_name is not None:
            artifacts = self.list(execution_id=execution_id, package_name=package_name)
        else:
            raise PlatformException('400',
                                    'Must provide one of: artifact_id, artifact_name, execution_id, package_name')

        # TODO - Temporary
        for artifact in artifacts:
            self.items_repository.delete(item_id=artifact.id)

        # TODO - when delete with filters is enabled again use this:
        # values = [artifact.id for artifact in artifacts]
        # self.items_repository.delete(filters=entities.Filters(field='id', values=values, operator='in'))

        return True
