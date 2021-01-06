import logging
import uuid
import os
from typing import Union, List

from .. import entities, repositories, exceptions, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Snapshots:
    """
    Snapshots Repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 model: entities.Model = None,
                 project: entities.Project = None,
                 artifacts: repositories.Artifacts = None,
                 project_id: str = None):
        self._client_api = client_api
        self._project = project
        self._model = model
        self._artifacts = artifacts
        self._project_id = project_id

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            if self._project_id is not None:
                projects = repositories.Projects(client_api=self._client_api)
                self._project = projects.get(project_id=self._project_id)
        if self._project is None:
            if self._model is not None:
                if self._model._project is not None:
                    self._project = self._model._project
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.snapshots repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def artifacts(self) -> repositories.Artifacts:
        assert isinstance(self.project.artifacts, repositories.Artifacts)
        return self.project.artifacts

    @property
    def model(self) -> entities.Model:
        if self._model is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Model entity in Datasets repository.'
                        ' Please use model.snapshots or set a model')
        assert isinstance(self._model, entities.Model)
        return self._model

    ###########
    # methods #
    ###########
    def get(self, snapshot_name=None, snapshot_id=None) -> entities.Snapshot:
        """
        Get snapshot object

        :param snapshot_id:
        :param snapshot_name:
        :return: snapshot object
        """

        if snapshot_id is not None:
            success, response = self._client_api.gen_request(req_type="get",
                                                             path="/snapshots/{}".format(snapshot_id))
            if not success:
                raise exceptions.PlatformException(response)
            snapshot = entities.Snapshot.from_json(client_api=self._client_api,
                                                   _json=response.json(),
                                                   project=self._project,
                                                   model=self._model)
            # verify input model name is same as the given id
            if snapshot_name is not None and snapshot.name != snapshot_name:
                logger.warning(
                    "Mismatch found in snapshots.get: snapshot_name is different then snapshot.name: {!r} != {!r}".format(
                        snapshot_name,
                        snapshot.name))
        elif snapshot_name is not None:

            filters = entities.Filters(
                resource=entities.FiltersResource.SNAPSHOT,
                field='name',
                values=snapshot_name
            )

            project_id = None

            if self._project is not None:
                project_id = self._project.id
            elif self._project_id is not None:
                project_id = self._project_id

            if project_id is not None:
                filters.add(field='projectId', values=project_id)

            if self._model is not None:
                filters.add(field='modelId', values=self._model.id)

            snapshots = self.list(filters=filters)

            if snapshots.items_count == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message='Snapshot not found. Name: {}'.format(snapshot_name))
            elif snapshots.items_count > 1:
                raise exceptions.PlatformException(
                    error='400',
                    message='More than one file found by the name of: {}'.format(snapshot_name))
            snapshot = snapshots.items[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='No checked-out Snapshot was found, must checkout or provide an identifier in inputs')

        return snapshot

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Snapshot]:
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, service in enumerate(response_items):
            jobs[i_service] = pool.apply_async(entities.Snapshot._protected_from_json,
                                               kwds={'client_api': self._client_api,
                                                     '_json': service,
                                                     'model': self._model,
                                                     'project': self._project})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        url = '/query/machine-learning'
        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project snapshots
        :return:
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.SNAPSHOT)
            if self._project is not None:
                filters.add(field='projectId', values=self._project.id)
            if self._model is not None:
                filters.add(field='modelId', values=self._model.id)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def create(
            self,
            snapshot_name: str,
            dataset_id: str,
            ontology_id: str = None,
            ontology_spec: entities.OntologySpec = None,
            description: str = None,
            artifact: Union[entities.GitCodebase, entities.ItemCodebase, entities.FilesystemCodebase] = None,
            # bucket: Union[entities.GcsBucket, entities.AwsBucket, entities.LocalBucket] , # TODO: we want to change it?
            project_id=None,
            is_global=None,
            tags: List[str] = None,
            model: entities.Model = None,
            configuration: dict = None,
    ) -> entities.Snapshot:
        """
            Create a Snapshot entity

        :param snapshot_name: name of the snapshot
        :param dataset_id: dataset id
        :param ontology_id:
        :param ontology_spec: OntologySpec object
        :param description: description
        :param artifact: optional
        :param project_id: project that owns the snapshot
        :param is_global: bool
        :param tags: list of string tags
        :param model: optional - Model object
        :param configuration: optional - snapshot configuration - dict
        :return: Snapshot Entity
        """

        if ontology_id is None and \
                ontology_spec is None:
            raise exceptions.PlatformException(error='400',
                                               message='Must provide arguments ontology_id OR ontology_spec')
        elif ontology_id is not None and \
                ontology_spec is not None and \
                ontology_id != ontology_spec.ontology_id:
            raise exceptions.PlatformException(error='400',
                                               message="ontology id: {} don't match ontology_spec: {}. please provide matching ontology".format(
                                                   ontology_id, ontology_spec.ontology_id))
        elif ontology_id is not None:
            ontologies = repositories.Ontologies(client_api=self._client_api)
            ontology_spec = entities.OntologySpec(ontology_id=ontology_id,
                                                  labels=[label.tag for label in
                                                          ontologies.get(ontology_id=ontology_id).labels])

        if artifact is not None and artifact.type != entities.PackageCodebaseType.ITEM:
            raise NotImplementedError('Cannot create to snapshot without an Item artifact')

        # TODO need to remove the entire project id user interface - need to take it from dataset id (in BE)
        if project_id is None:
            if self._project is None:
                raise exceptions.PlatformException('Please provide project_id')
            project_id = self._project.id
        else:
            if project_id != self._project_id:
                logger.warning(
                    "Note! you are specified project_id {!r} which is different from repository context: {!r}".format(
                        project_id, self._project_id))

        if model is None and self._model is None:
            raise exceptions.PlatformException('Must provide a model or create from model.snapshots')
        elif model is None:
            model = self._model

        if artifact is None:
            artifact_dir_item = self.artifacts.items_repository.make_dir(
                directory=self.artifacts._build_path_header(model_name=model.name,
                                                            snapshot_name='{}_{}'.format(snapshot_name,
                                                                                         str(uuid.uuid1()))))
            artifact = entities.ItemCodebase(codebase_id=artifact_dir_item.id)

        # create payload for request
        payload = {
            'modelId': model.id,
            'name': snapshot_name,
            'projectId': project_id,
            'datasetId': dataset_id,
            'ontologySpec': ontology_spec.to_json(),
            'artifact': artifact.to_json()
        }

        if configuration is not None:
            payload['configuration'] = configuration

        if tags is not None:
            payload['tags'] = tags

        if is_global is not None:
            payload['global'] = is_global

        if description is not None:
            payload['description'] = description

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/snapshots',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        snapshot = entities.Snapshot.from_json(_json=response.json(),
                                               client_api=self._client_api,
                                               project=self._project,
                                               model=model)
        return snapshot

    def upload(self,
               local_path: str,
               snapshot: entities.Snapshot,
               overwrite: bool = False):
        """
        Create a snapshot in platform

        :param local_path: path of artifacts to upload
        :param snapshot: Snapshot entity
        :param overwrite: overwrite the artifacts (if same name exists)
        :return: Snapshot Entity
        """

        if snapshot.artifact is None or snapshot.artifact.type != entities.PackageCodebaseType.ITEM:
            raise NotImplementedError('Cannot upload to snapshot without an Item artifact')

        # upload artifacts
        if not local_path.endswith('/'):
            local_path += '/'
        # snapshot binaries must be flatten (no directory trees)
        local_path += '*'
        artifact_dir_item = self.artifacts.items_repository.get(item_id=snapshot.artifact.codebase_id)
        artifacts = self.artifacts.items_repository.upload(local_path=local_path,
                                                           remote_path=artifact_dir_item.filename,
                                                           overwrite=overwrite)
        return artifacts

    def download(self, snapshot_id=None, snapshot=None, local_path=None):
        if snapshot is None:
            if snapshot_id is None:
                raise exceptions.PlatformException(error='400',
                                                   message='Please provide snapshot or snapshot id')
            snapshot = self.get(snapshot_id=snapshot_id)
        if snapshot.id != snapshot_id:
            raise exceptions.PlatformException(error="409",
                                               message="snapshot id {!r} does not match given sanpshot {}: {!r}".format(
                                                   snapshot_id, snapshot.name, snapshot.id))

        if local_path is None:
            local_path = os.getcwd()

        if snapshot.artifact is None or snapshot.artifact.type != entities.PackageCodebaseType.ITEM:
            raise NotImplementedError('Cannot upload to snapshot without an Item artifact')

        snapshot_artifact_item = self.artifacts.get(artifact_id=snapshot.artifact.codebase_id)
        if snapshot_artifact_item.type == 'dir':
            filters = entities.Filters(field='dir', values='{}*'.format(snapshot_artifact_item.filename))
            artifacts = self.artifacts.items_repository.download(
                filters=filters,
                local_path=local_path,
                to_items_folder=False,
                without_relative_path=snapshot_artifact_item.filename)
        else:
            artifacts = snapshot_artifact_item.download(local_path=local_path)
        return artifacts

    def download_data(self, snapshot_id=None, snapshot=None, local_path=None):
        """
        Download Frozen Dataset from snapshot, by Model format
        """
        # TODO: implememtn this function - this is only a rough sketch
        if snapshot is None:
            if snapshot_id is None:
                raise exceptions.PlatformException('400', 'Please provide snapshot or snapshot id')
            snapshot = self.get(snapshot_id=snapshot_id)
        if snapshot.id != snapshot_id:
            raise exceptions.PlatformException(error="409",
                                               message="snapshot id {!r} does not match given sanpshot {}: {!r}".format(
                                                   snapshot_id, snapshot.name, snapshot.id))

        if local_path is None:
            local_path = os.getcwd()

        datasets = repositories.Datasets(client_api=self._client_api)
        dataset = datasets.get(dataset_id=snapshot.dataset_id)
        ret_list = dataset.download(local_path=local_path)  # Question - what is the return value? list of what?
        # models = repositories.Models(client_api=self._client_api)
        # model = modelsdebug(model_id=snapshot.model_id)  # TODO: can I use snapshot.model?
        model = snapshot.model
        # TODO: need to create the convertor / or use the adapter
        adapter = model.build()
        if adapter is not None:
            ret_list = adapter.convert(ret_list)  # TODO: @Shefi + @Or define mandatory API for adapter

        return ret_list

    def delete(self, snapshot: entities.Snapshot = None, snapshot_name=None, snapshot_id=None):
        """
        Delete Snapshot object

        :param snapshot: Snapshot entity to delete
        :param snapshot_name: delete by snapshot name
        :param snapshot_id: delete by snapshot id
        :return: True
        """
        # get id and name
        if snapshot_id is None:
            if snapshot is not None:
                snapshot_id = snapshot.id
            elif snapshot_name is not None:
                snapshot = self.get(snapshot_name=snapshot_name)
                snapshot_id = snapshot.id
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Must input at least one parameter to snapshots.delete')

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/snapshots/{}".format(snapshot_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, snapshot: entities.Snapshot) -> entities.Snapshot:
        """
        Update Snapshot changes to platform

        :param snapshot:
        :return: Snapshot entity
        """
        # payload
        payload = snapshot.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/snapshots/{}'.format(snapshot.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Snapshot.from_json(_json=response.json(),
                                           client_api=self._client_api,
                                           project=self._project,
                                           model=snapshot._model)
