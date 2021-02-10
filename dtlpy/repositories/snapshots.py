import logging
import os
from typing import List

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
                 project_id: str = None):
        self._client_api = client_api
        self._project = project
        self._model = model
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
    def model(self) -> entities.Model:
        if self._model is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Model entity in {} repository.'.format(self.__class__.__name__) + \
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
            # verify input snapshot name is same as the given id
            if snapshot_name is not None and snapshot.name != snapshot_name:
                logger.warning(
                    "Mismatch found in snapshots.get: snapshot_name is different then snapshot.name:"
                    " {!r} != {!r}".format(
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
            labels: list = None,
            description: str = None,
            bucket: entities.Bucket = None,
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
        :param ontology_id: ontology to connect to the snapshot
        :param labels: list of labels from ontology (must mach ontology id) can be a subset
        :param description: description
        :param bucket: optional
        :param project_id: project that owns the snapshot
        :param is_global: bool
        :param tags: list of string tags
        :param model: optional - Model object
        :param configuration: optional - snapshot configuration - dict
        :return: Snapshot Entity
        """

        if ontology_id is None:
            raise exceptions.PlatformException(error='400',
                                               message='Must provide arguments ontology_id')

        if labels is None:
            ontologies = repositories.Ontologies(client_api=self._client_api)
            labels = [label.tag for label in ontologies.get(ontology_id=ontology_id).labels]
        ontology_spec = entities.OntologySpec(ontology_id=ontology_id,
                                              labels=labels)

        # TODO: Check that given dataset is of type frozen
        # ds = self.datasets.get(dataset_id=dataset_id)
        # if ds.type != 'frozen':
        #     raise TypeError("Dataset {ds_id} is of type {ds_type} which does not support Snapshot creation".
        #                     format(ds_id=dataset_id, ds_type=ds.type))

        if bucket is not None and bucket.type != entities.BucketType.ITEM:
            logger.warning("It is suggesgeted to use ItemBucket which support all functionality")
            # raise NotImplementedError('Cannot create to snapshot without an Item bucket')

        if bucket is not None and not isinstance(bucket, entities.Bucket):
            raise exceptions.PlatformException(error='500',
                                               message="Snapshot does not support {} as a bucket".format(bucket))

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

        if bucket is None:
            bucket = entities.LocalBucket(local_path=os.getcwd())

        # create payload for request
        payload = {
            'modelId': model.id,
            'name': snapshot_name,
            'projectId': project_id,
            'datasetId': dataset_id,
            'ontologySpec': ontology_spec.to_json(),
            'bucket': bucket.to_json()
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

    def upload_to_bucket(self,
                         local_path: str,
                         snapshot: entities.Snapshot,
                         overwrite: bool = False):
        """
        Uploads bucket to remote server

        :param local_path: path of files to upload
        :param snapshot: Snapshot entity
        :param overwrite: overwrite the remote files (if same name exists)
        :return: Snapshot Entity
        """

        if snapshot.bucket is None:
            raise NotImplementedError('Cannot upload to snapshot without an Item bucket')

        if snapshot.bucket.type in [entities.BucketType.ITEM, entities.BucketType.GCS]:
            output = snapshot.bucket.upload(local_path=local_path,
                                            overwrite=overwrite)
        else:
            raise ValueError('Cannot download bucket of type: {}'.format(snapshot.bucket.type))

        return output

    def download_from_bucket(self, snapshot_id=None, snapshot=None, local_path=None, remote_paths=None):
        """
        Download files from a remote bucket

        :param snapshot_id: `str` specific snapshot id
        :param snapshot: `dl.Snapshot` specific snapshot
        :param local_path: `str` directory path to load the bucket content to
        :param remote_paths: `List[`str`]` specific files to download
        :return: list of something - TBD
        """
        if snapshot is None:
            if snapshot_id is None:
                raise exceptions.PlatformException(error='400',
                                                   message='Please provide snapshot or snapshot id')
            snapshot = self.get(snapshot_id=snapshot_id)
        elif snapshot_id is not None and snapshot.id != snapshot_id:
            raise exceptions.PlatformException(error="409",
                                               message="snapshot id {!r} does not match given snapshot {}: {!r}".format(
                                                   snapshot_id, snapshot.name, snapshot.id))

        if local_path is None:
            local_path = os.getcwd()

        if snapshot.bucket is None:
            raise ValueError('Missing Bucket on snapshot. id: {}'.format(snapshot.id))

        if snapshot.bucket.type in [entities.BucketType.ITEM, entities.BucketType.GCS]:
            output = snapshot.bucket.download()
        else:
            raise ValueError('Cannot download bucket of type: {}'.format(snapshot.bucket.type))
        return output

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
