import tempfile
import requests
import logging
import shutil
import os

from .. import entities, miscellaneous, PlatformException, exceptions, repositories
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Artifacts:
    """
    Artifacts repository
    """

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None,
                 project_id: str = None,
                 model: entities.Model = None,
                 package: entities.Package = None,
                 dataset_name='Binaries'):
        self._client_api = client_api
        self._project = project
        self._dataset = dataset
        self._items_repository = None
        self.dataset_name = dataset_name
        self.project_id = project_id
        self.model = model
        self.package = package

    ############
    # entities #
    ############
    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            # get dataset from project
            try:
                self._dataset = self.project.datasets.get(dataset_name=self.dataset_name)
            except exceptions.NotFound:
                self._dataset = None
            if self._dataset is None:
                logger.debug(
                    'Dataset for artifacts was not found. Creating... dataset name: {ds!r}. project_id={id}'.format(
                        ds=self.dataset_name, id=self.project.id))
                self._dataset = self.project.datasets.create(dataset_name=self.dataset_name)
                # add system to metadata
                if 'metadata' not in self._dataset.to_json():
                    self._dataset.metadata = dict()
                if 'system' not in self._dataset.metadata:
                    self._dataset.metadata['system'] = dict()
                self._dataset.metadata['system']['scope'] = 'system'
                self.project.datasets.update(dataset=self._dataset, system_metadata=True)
        return self._dataset

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            if self._dataset is not None:
                self._project = self._dataset.project
            elif self.project_id is not None:
                self._project = repositories.Projects(client_api=self._client_api).get(project_id=self.project_id)
            else:
                raise PlatformException(error='400',
                                        message='Artifacts doesnt have a project, at least one must not be None: dataset, project or project_id')
        return self._project

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
    def _build_path_header(
            package_name=None,
            package=None,
            execution_id=None,
            execution=None,
            model_name=None,
    ):
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

        return remote_path

    def list(self,
             execution_id: str = None,
             package_name: str = None,
             model_name: str = None) -> miscellaneous.List[entities.Artifact]:
        """
        List of artifacts

        :param str execution_id: list by execution id
        :param str package_name: list by package name
        :param str model_name: list by model name
        :return: list of artifacts
        :rtype: miscellaneous.List[dtlpy.entities.artifact.Artifact]

        **Example**:

        .. code-block:: python

            project.artifacts.list(package_name='package_name')
        """
        if self.model is not None:
            model_name = self.model.name
        if self.package is not None:
            package_name = self.package.name

        filters = entities.Filters()
        remote_path = self._build_path_header(
            package_name=package_name,
            execution_id=execution_id,
            model_name=model_name
        )

        remote_path += '/*'
        filters.add(field='filename', values=remote_path)
        pages = self.items_repository.list(filters=filters)
        items = [entities.Artifact.from_json(_json=item.to_json(),
                                             client_api=self._client_api,
                                             dataset=item._dataset,
                                             project=self.project)
                 for page in pages for item in page]
        return miscellaneous.List(items)

    def get(self,
            artifact_id: str = None,
            artifact_name: str = None,
            model_name: str = None,
            execution_id: str = None,
            package_name: str = None) -> entities.ItemArtifact:
        """

        Get an artifact object by name, id or type
        If by name or type - need to input also execution/task id for the artifact folder

        :param str artifact_id: search by artifact id
        :param str artifact_name: search by artifact id
        :param str model_name: search by model name
        :param str execution_id: search by execution id
        :param str package_name: search by  package name
        :return: Artifact object
        :rtype: dtlpy.entities.artifact.Artifact

        **Example**:

        .. code-block:: python

            project.artifacts.get(artifact_id='artifact_id')
        """
        if self.model is not None:
            model_name = self.model.name
        if self.package is not None:
            package_name = self.package.name

        if artifact_id is not None:
            artifact = self.items_repository.get(item_id=artifact_id)
            # verify input artifact name is same as the given id
            if artifact_name is not None and artifact.name != artifact_name:
                logger.warning(
                    "Mismatch found in artifacts.get: artifact_name is different then artifact.name:"
                    " {!r} != {!r}".format(
                        artifact_name,
                        artifact.name))
        elif artifact_name is not None:
            artifacts = self.list(
                execution_id=execution_id,
                package_name=package_name,
                model_name=model_name
            )
            artifact = [artifact for artifact in artifacts if artifact.name == artifact_name]
            if len(artifact) == 1:
                artifact = artifact[0]
            elif len(artifact) > 1:
                raise PlatformException('404', 'More Than one Artifact found')
            else:
                raise PlatformException('404', 'Artifact not found')
        else:
            msg = 'one input must be not None: artifact_id or artifact_name'
            raise ValueError(msg)
        return artifact

    def download(
            self,
            artifact_id: str = None,
            artifact_name: str = None,
            execution_id: str = None,
            package_name: str = None,
            model_name: str = None,
            local_path: str = None,
            overwrite: bool = False,
            save_locally: bool = True
    ):
        """

        Download artifact binary.
        Get artifact by name, id or type

        :param str artifact_id: search by artifact id
        :param str artifact_name: search by artifact id
        :param str execution_id: search by execution id
        :param str package_name: search by package name
        :param str model_name: search by model name
        :param str local_path: artifact will be saved to this filepath
        :param bool overwrite: optional - default = False
        :param bool save_locally: to save the file local
        :return: file path
        :rtype: str

        **Example**:

        .. code-block:: python

            project.artifacts.download(artifact_id='artifact_id',
                                        local_path='your_path',
                                        overwrite=True,
                                        save_locally=True)
        """
        if self.model is not None:
            model_name = self.model.name
        if self.package is not None:
            package_name = self.package.name

        if artifact_id is not None:
            # download
            artifact = self.items_repository.download(items=artifact_id,
                                                      save_locally=save_locally,
                                                      local_path=local_path,
                                                      overwrite=overwrite)
        elif artifact_name is not None:
            artifact_obj: entities.ItemArtifact = self.get(artifact_id=artifact_id,
                                                           execution_id=execution_id,
                                                           package_name=package_name,
                                                           artifact_name=artifact_name)

            artifact = artifact_obj.download(save_locally=save_locally,
                                             local_path=local_path,
                                             overwrite=overwrite)

        else:
            if self.model is not None:
                artifact = list()
                for m_artifact in self.model.model_artifacts:
                    if isinstance(m_artifact, entities.ItemArtifact):
                        if not m_artifact.is_fetched:
                            m_artifact = self.items_repository.get(item_id=m_artifact.id)
                        model_remote_root = m_artifact.filename.split('/')
                        model_remote_root = '/'.join(model_remote_root[:4])
                        # remove the prefix with relpath
                        local_dst = os.path.join(local_path,
                                                 os.path.relpath(m_artifact.filename, model_remote_root))
                        if not os.path.isfile(local_dst) or overwrite:
                            # need_to_download
                            # 1. download to temp folder
                            temp_dir = tempfile.mkdtemp()
                            local_temp_file = m_artifact.download(
                                local_path=temp_dir,
                                overwrite=overwrite,
                                to_items_folder=False,
                            )
                            src = local_temp_file
                            # remove the prefix with relpath
                            dst = local_dst
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.move(src=src, dst=dst)
                            # clean temp dir
                            if os.path.isdir(temp_dir):
                                shutil.rmtree(temp_dir)
                        artifact.append(local_path)
                    elif isinstance(m_artifact, entities.LinkArtifact):
                        # remove the prefix with relpath
                        local_dst = os.path.join(local_path, m_artifact.filename)
                        if not os.path.isfile(local_dst) or overwrite:
                            # need_to_download
                            # 1. download to temp folder
                            temp_dir = tempfile.mkdtemp()
                            response = requests.get(m_artifact.url, stream=True)
                            local_temp_file = os.path.join(temp_dir, m_artifact.filename)
                            with open(local_temp_file, "wb") as handle:
                                for data in response.iter_content(chunk_size=8192):
                                    handle.write(data)
                            src = local_temp_file
                            # remove the prefix with relpath
                            dst = local_dst
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.move(src=src, dst=dst)
                            # clean temp dir
                            if os.path.isdir(temp_dir):
                                shutil.rmtree(temp_dir)
                        artifact.append(local_path)
                    elif isinstance(m_artifact, entities.LocalArtifact):
                        pass
                    else:
                        raise ValueError('unsupported artifact type: {}'.format(type(m_artifact)))
            else:
                # for package artifacts - download using filter on the package directory
                if all(elem is None for elem in [package_name, execution_id]):
                    raise PlatformException(error='400', message='Must input package or execution (id or entity)')
                remote_path = self._build_path_header(
                    package_name=package_name,
                    execution_id=execution_id,
                    model_name=model_name,
                )
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
        return artifact

    def upload(self,
               # what to upload
               filepath: str,
               # where to upload
               package_name: str = None,
               package: entities.Package = None,
               execution_id: str = None,
               execution: entities.Execution = None,
               model_name: str = None,
               # add information
               overwrite: bool = False):
        """

        Upload binary file to artifact. get by name, id or type.
        If artifact exists - overwriting binary
        Else and if create==True a new artifact will be created and uploaded

        :param str filepath: local binary file
        :param str package_name: package name that include the artifact
        :param dtlpy.entities.package.Package package: package object
        :param str execution_id: execution id that include the artifact
        :param dtlpy.entities.execution.Execution execution: execution object
        :param str model_name: model name that include the artifact
        :param bool overwrite: optional - default = False to overwrite an existing object
        :return: Artifact Object
        :rtype: dtlpy.entities.artifact.Artifact

        **Example**:

        .. code-block:: python

            project.artifacts.upload(filepath='filepath',
                                    package_name='package_name')
        """
        if self.model is not None:
            model_name = self.model.name
        if self.package is not None:
            package_name = self.package.name

        remote_path = self._build_path_header(package_name=package_name,
                                              package=package,
                                              execution=execution,
                                              execution_id=execution_id,
                                              model_name=model_name)

        if all(elem is None for elem in [package_name, package, execution_id, execution, model_name]):
            raise ValueError('Must input package or execution (id or entity)')

        artifact = self.items_repository.upload(local_path=filepath,
                                                remote_path=remote_path,
                                                overwrite=overwrite,
                                                output_entity=entities.Artifact)
        if self.model is not None:
            # list and update model
            filters = entities.Filters()
            filters.add(field='dir', values=remote_path + '*')
            pages = self.items_repository.list(filters=filters)
            model_artifacts = list()
            for item in pages.all():
                model_artifacts.append(entities.Artifact.from_json(_json=item.to_json(),
                                                                   client_api=self._client_api,
                                                                   dataset=item._dataset))
            self.model.model_artifacts = model_artifacts
            self.model.update()
        logger.debug('Artifact uploaded successfully')
        return artifact

    def delete(self,
               artifact_id=None,
               artifact_name=None,
               execution_id=None,
               model_name=None,
               package_name=None):
        """
        Delete artifacts

        :param str artifact_id: search by artifact id
        :param str artifact_name: search by artifact id
        :param str execution_id: search by execution id
        :param str model_name: search by model name
        :param str package_name: search by package name
        :return: True if success
        :rtype: bool

         **Example**:

        .. code-block:: python

            project.artifacts.delete(artifact_id='artifact_id',
                                    package_name='package_name')
        """
        if self.model is not None:
            model_name = self.model.name
        if self.package is not None:
            package_name = self.package.name

        if artifact_id is not None or artifact_name is not None:
            artifacts = [
                self.get(
                    artifact_id=artifact_id,
                    artifact_name=artifact_name,
                    model_name=model_name,
                )
            ]
        elif execution_id is not None or package_name is not None:
            artifacts = self.list(
                execution_id=execution_id,
                package_name=package_name,
                model_name=model_name,
            )
        else:
            raise PlatformException('400',
                                    'Must provide one of: artifact_id, artifact_name, execution_id, package_name')

        values = [artifact.id for artifact in artifacts]
        self.items_repository.delete(filters=entities.Filters(field='id', values=values,
                                                              operator=entities.FiltersOperations.IN))

        return True
