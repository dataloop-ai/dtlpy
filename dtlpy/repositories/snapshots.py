import datetime
import logging
import tempfile
import shutil
import os
from typing import List

from .. import entities, repositories, exceptions, miscellaneous, services

logger = logging.getLogger(name='dtlpy')


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

        if self._project is not None:
            self._project_id = self._project.id

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
                message='Cannot perform action WITHOUT Model entity in {} repository.'.format(self.__class__.__name__) +
                        ' Please use model.snapshots or set a model')
        assert isinstance(self._model, entities.Model)
        return self._model

    ###########
    # methods #
    ###########
    def get(self, snapshot_name=None, snapshot_id=None) -> entities.Snapshot:
        """
        Get snapshot object
        :param snapshot_name:
        :param snapshot_id:
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
            jobs[i_service] = pool.submit(entities.Snapshot._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': service,
                                             'model': self._model,
                                             'project': self._project})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        url = '/snapshots/query'
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

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities
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
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))

        if filters.resource != entities.FiltersResource.SNAPSHOT:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.SNAPSHOT. Got: {!r}'.format(filters.resource))

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
            labels: list = None,
            ontology_id: str = None,
            description: str = None,
            bucket: entities.Bucket = None,
            project_id=None,
            is_global=None,
            tags: List[str] = None,
            model: entities.Model = None,
            configuration: dict = None,
            status: str = None,
    ) -> entities.Snapshot:
        """
        Create a Snapshot entity

        :param str snapshot_name: name of the snapshot
        :param str dataset_id: dataset id
        :param list labels: list of labels from ontology (must mach ontology id) can be a subset
        :param str ontology_id: ontology to connect to the snapshot
        :param str description: description
        :param bucket: optional dl.Bucket.  If None - creates a local bucket at the current working dir
        :param str project_id: project that owns the snapshot
        :param bool is_global: is global
        :param list tags: list of string tags
        :param model: optional - Model object
        :param dict configuration: optional - snapshot configuration - dict
        :param str status: `str` of the optional values of
        :return: Snapshot Entity
        """

        if labels is None and ontology_id is None:
            raise exceptions.PlatformException(error='400',
                                               message='Must provide either labels or ontology_id as arguments')
        elif labels is not None:
            ontology_spec = entities.OntologySpec(ontology_id='null', labels=labels)
        else:  # ontology_id is not None
            ontologies = repositories.Ontologies(client_api=self._client_api)
            labels = [label.tag for label in ontologies.get(ontology_id=ontology_id).labels]
            ontology_spec = entities.OntologySpec(ontology_id=ontology_id, labels=labels)

        if bucket is not None and bucket.type != entities.BucketType.ITEM:
            logger.warning("It is suggested to use ItemBucket which support all functionality")
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

        if status is not None:
            payload['status'] = status

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

        if dataset_id is None:
            logger.warning(
                "Snapshot {!r} was created without a dataset. This may cause unexpected errors.".format(snapshot.id))
        else:
            if snapshot.dataset.readonly is False:
                logger.error("Snapshot does not support 'unlocked dataset'. Please change {!r} to readonly".format(
                    snapshot.dataset.name))

        return snapshot

    def clone(self,
              from_snapshot: entities.Snapshot,
              snapshot_name: str,
              bucket: entities.Bucket = None,
              dataset_id: entities.Dataset = None,
              configuration: dict = None,
              status='created',
              project_id: str = None,
              labels: list = None,
              description: str = None,
              tags: list = None,
              ) -> entities.Snapshot:
        """
        Clones and creates a new snapshot out of existing one

        :param from_snapshot: existing snapshot to clone from
        :param str snapshot_name: `str` new snapshot name
        :param bucket: `dl.Bucket` (optional) if passed replaces the current bucket
        :param str dataset_id: dataset_id for the cloned snapshot
        :param dict configuration: `dict` (optional) if passed replaces the current configuration
        :param str status: `str` (optional) set the new status
        :param str project_id: `str` specify the project id to create the new snapshot on (if other the the source snapshot)
        :param list labels:  `list` of `str` - label of the snapshot
        :param str description: `str` description of the new snapshot
        :param list tags:  `list` of `str` - label of the snapshot
        :return: dl.Snapshot which is a clone version of the existing snapshot
        """
        # FIXME: replace the clone with a Backend clone
        from_json = from_snapshot.to_json()
        from_json['status'] = status
        from_json['name'] = snapshot_name
        if project_id is not None:
            from_json['projectId'] = project_id
        if dataset_id is not None:
            from_json['datasetId'] = dataset_id
        if configuration is not None:
            from_json['configuration'].update(configuration)
        if labels is not None:
            ontology_spec = entities.OntologySpec(ontology_id='null', labels=labels)
            from_json['ontologySpec'] = ontology_spec.to_json()
        if description is not None:
            from_json['description'] = description
        if tags is not None:
            from_json['tags'] = tags

        # update required fields or replace with new values
        if bucket is None:
            # creating new bucket for the clone
            if isinstance(from_snapshot.bucket, entities.LocalBucket):
                orig_dir = os.path.dirname(from_snapshot.bucket.local_path)
                clone_bucket_path = os.path.join(orig_dir, datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
                bucket = from_snapshot.buckets.create(bucket_type=entities.BucketType.LOCAL,
                                                      local_path=clone_bucket_path,
                                                      snapshot_name=snapshot_name)
            elif isinstance(from_snapshot.bucket, entities.ItemBucket):
                logger.info("Copying bucket_item")
                bucket = from_snapshot.buckets.create(bucket_type=entities.BucketType.ITEM,
                                                      model_name=from_snapshot.model.name,
                                                      snapshot_name=snapshot_name)
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/snapshots',
                                                         json_req=from_json)
        # exception handling
        if not success:
            raise exceptions.PlatformException(response)
        new_snapshot = entities.Snapshot.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   project=self._project,
                                                   model=from_snapshot.model)
        # cloning the bucket
        if bucket is not None:
            logger.info("Cloning bucket...")
            from_snapshot.buckets.clone(src_bucket=from_snapshot.bucket,
                                        dst_bucket=bucket)
            logger.info("Cloning bucket... Done")
            new_snapshot.bucket = bucket
            new_snapshot.update()
        else:
            logger.warning('Not cloning the bucket!')

        if new_snapshot._dataset is not None and new_snapshot._dataset.readonly is False:
            logger.error("Snapshot does not support 'unlocked dataset'. Please change {!r} to readonly".format(
                new_snapshot.dataset.name))

        return new_snapshot

    def upload_to_bucket(self,
                         local_path: str,
                         snapshot: entities.Snapshot,
                         overwrite: bool = False):
        """
        Uploads bucket to remote server

        :param str local_path: path of files to upload
        :param snapshot: Snapshot entity
        :param bool overwrite: overwrite the remote files (if same name exists)
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

    def download_from_bucket(self, snapshot_id=None, snapshot=None, local_path=None):
        """
        Download files from a remote bucket

        :param str snapshot_id: `str` specific snapshot id
        :param snapshot: `dl.Snapshot` specific snapshot
        :param str local_path: `str` directory path to load the bucket content to
        :return: list of something - TBD
        """
        if snapshot is None:
            if snapshot_id is None:
                raise exceptions.PlatformException(error='400',
                                                   message='Please provide snapshot or snapshot id')
            snapshot = self.get(snapshot_id=snapshot_id)
        elif snapshot_id is not None and snapshot.id != snapshot_id:
            raise exceptions.PlatformException(error="409",
                                               message="snapshot_id {!r} does not match given snapshot {}: {!r}".format(
                                                   snapshot_id, snapshot.name, snapshot.id))

        if local_path is None:
            local_path = os.getcwd()

        if snapshot.bucket is None:
            raise ValueError('Missing Bucket on snapshot. id: {}'.format(snapshot.id))

        if snapshot.bucket.type in [entities.BucketType.ITEM, entities.BucketType.GCS]:
            output = snapshot.bucket.download(local_path=local_path)
        else:
            raise ValueError('Cannot download bucket of type: {}'.format(snapshot.bucket.type))
        return output

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/snapshots".format(self.project.id))

    def open_in_web(self, snapshot=None, snapshot_id=None):
        """
        Open the snapshot in web platform

        :param snapshot: snapshot entity
        :param str snapshot_id: snapshot id
        """
        if snapshot is not None:
            snapshot.open_in_web()
        elif snapshot_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(snapshot_id) + '/main')
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def delete(self, snapshot: entities.Snapshot = None, snapshot_name=None, snapshot_id=None):
        """
        Delete Snapshot object

        :param snapshot: Snapshot entity to delete
        :param str snapshot_name: delete by snapshot name
        :param str snapshot_id: delete by snapshot id
        :return: True
        :rtype: bool
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

        :param snapshot: Snapshot entity
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
