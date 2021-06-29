import logging
import tqdm
import os
import io
import uuid

from .. import entities, services, repositories, exceptions, miscellaneous

logger = logging.getLogger(name=__name__)


class Buckets:
    """
    Buckets repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 project=None,
                 snapshot=None,
                 project_id=None):
        self._client_api = client_api
        self._project = project
        self._snapshot = snapshot
        self._items = None
        if project is not None:
            if project_id is None:
                project_id = project.id
            elif project_id != project.id:
                raise RuntimeError("mismatching project {!r} and project_id {!r}".format(project.id, project_id))
        self._project_id = project_id

    ################
    # repositories #
    ################
    @property
    def items(self):
        if self._project is not None:
            self._items = self.project.items
        else:
            self._items = repositories.Items(client_api=self._client_api)
        assert isinstance(self._items, repositories.Items)
        return self._items

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def snapshot(self) -> entities.Snapshot:
        assert isinstance(self._snapshot, entities.Snapshot)
        return self._snapshot

    ###########
    # methods #
    ###########

    def list_content(self, bucket: entities.Bucket):
        """
        List bucket content
        :return: list of items in bucket TBD
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            output = directory_item.dataset.items.list(filters=entities.Filters(field='dir',
                                                                                values=directory_item.filename))
        elif isinstance(bucket, entities.GCSBucket):
            gcs_bucket = bucket._bucket
            blobs = gcs_bucket.list_blobs(prefix=bucket._gcs_prefix)
            output = list(blobs)
        elif isinstance(bucket, entities.LocalBucket):
            output = os.listdir(bucket.local_path)
        else:
            raise NotImplemented('missing implementation for "list" in bucket type: {!r}'.format(bucket.type))
        return output

    def get_single_file(self,
                        filename,
                        bucket: entities.Bucket):
        """

        Get a filename from bucket
        If by name or type - need to input also execution/task id for the bucket folder

        :param bucket: Bucket entity
        :param filename: Bucket entity
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            filters = entities.Filters(field='dir', values=directory_item.filename)
            filters.add(field='name', values=filename)
            output = directory_item.dataset.items.list(filters=filters)
        else:
            raise NotImplemented('missing implementation for "buckets.get" for bucket type: {!r}'.format(bucket.type))
        return output

    def download(self,
                 bucket: entities.Bucket,
                 local_path=None,
                 overwrite=False,
                 ):
        """

        Download binary file from bucket.

        :param bucket: bucket entity
        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        if isinstance(bucket, entities.ItemBucket):
            bucket_dir_item = self.items.get(item_id=bucket.directory_item_id)
            # fetch: False does not use an API call but created the dataset entity (with id)
            dataset = bucket_dir_item.datasets.get(dataset_id=bucket_dir_item.datasetId, fetch=False)
            bucket_filter = entities.Filters(field='dir', values=bucket_dir_item.filename)
            local_path = dataset.items.download(
                filters=bucket_filter,
                local_path=local_path,
                overwrite=overwrite,
                to_items_folder=False,
                without_relative_path=bucket_dir_item.filename
            )
            logger.info('Bucket artifacts was unpacked to: {}'.format(local_path))

        elif isinstance(bucket, entities.GCSBucket):
            gcs_bucket = bucket._bucket
            remote_prefix = bucket._gcs_prefix  # This should be all the bucket
            blobs = gcs_bucket.list_blobs(prefix=remote_prefix)
            remote_prefix += '' if remote_prefix.endswith('/') else '/'
            prefix_len = len(remote_prefix)

            for blob in tqdm.tqdm(blobs, leave=None):
                rel_fname = blob.name[prefix_len:]  # To create tree structure from the prefix only

                if blob.name.endswith('/'):  # This is a dir
                    if blob.name == remote_prefix:
                        continue
                    else:
                        os.makedirs(os.path.join(local_path, rel_fname), exist_ok=True)
                else:  # blob is a file
                    base_dir = os.path.join(local_path, *os.path.split(rel_fname)[:-1])
                    # make sure dir exist even if there is no blob for it
                    if not os.path.isdir(base_dir):
                        os.makedirs(base_dir, exist_ok=True)
                    local_file_path = os.path.join(local_path, rel_fname)
                    blob.download_to_filename(local_file_path)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.download" for bucket type: {!r}'.format(bucket.type))
        return True

    def upload(self,
               bucket: entities.Bucket,
               # what to upload
               local_path,
               # add information
               overwrite=False):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded

        :param bucket: bucket entity
        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            # Upload  the artifacts files them selves rather than  the directory  # 2021-14-06
            local_files = [os.path.join(local_path, ff) for ff in os.listdir(local_path)]
            items = directory_item.dataset.items.upload(local_path=local_files,
                                                        remote_path=directory_item.filename,
                                                        overwrite=overwrite)

        elif isinstance(bucket, entities.GCSBucket):
            gcs_bucket = bucket._bucket
            # FIXME: this supports only upload of entire dir
            local_path += '' if local_path.endswith('/') else '/'
            local_prefix_len = len(local_path)
            for root, dir_names, file_names in os.walk(top=local_path, topdown=True):
                for dir_name in dir_names:
                    # TODO: check if i need to create dir blobs
                    blob = gcs_bucket.blob(os.path.join(bucket._gcs_prefix, local_path[local_prefix_len:], dir_name))
                    blob.upload_from_filename(os.path.join(root, dir_name))
                for file_name in file_names:
                    blob = gcs_bucket.blob(os.path.join(bucket._gcs_prefix, local_path[local_prefix_len:], file_name))
                    blob.upload_from_filename(os.path.join(root, file_name))
        else:
            raise NotImplemented(
                'missing implementation for "buckets.upload" for bucket type: {!r}'.format(bucket.type))
        return True

    def delete(self, bucket: entities.Bucket):
        """
        Delete bucket

        :param bucket: bucket entity
        :return: True if success
        """
        if isinstance(bucket, entities.ItemBucket):
            path = self.items.delete(item_id=bucket.directory_item_id)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.delete" for bucket type: {!r}'.format(bucket.type))
        return path

    def create(self, bucket_type=entities.BucketType.ITEM,
               # item bucket / local_bucket
               local_path=None,
               # gcs bucket
               gcs_project_name: str = None,
               gcs_bucket_name: str = None,
               gcs_prefix: str = '/',
               # item_bucket names
               item_bucket_model_name:str = None,
               item_bucket_snapshot_name:str = None,
               use_existing_gcs: bool = True,
               ):
        """
        Create a new bucket- directory contains the artifacts (weights and other configurations) of the model.
        :param bucket_type: `dl.BucketType`: Local, Item, Gcs
            Local Bucket: is simply a the path to where the bucket is stored locally . environment vars are valid
            Item Bucket: is used when you want to store your binary files of the model on our Dataloop Platform,
                they are saved i a different dataset in a defined path
            Gcs Bucket: is used when you have a Google Cloud Storage bucket and you can connect to it,
                save / download your models directly to the bucket
        :param local_path:  `str` where were the weights are currently saved - what directory to upload to the bucket

        :param gcs_project_name: `str` project name in your GCS (Google Cloud Storage) platform
        :param gcs_bucket_name:  `str` bucket name in your GCS
        :param gcs_prefix:  `str` prefix/ remote path of where your bucket is defined in GCS

        :param item_bucket_model_name: `str` optional to override the repo settings
        :param item_bucket_snapshot_name: `str` = optional to override the repo settings
        :param use_existing_gcs:
        :return: `dl.Bucket`
        """
        if bucket_type == entities.BucketType.ITEM:
            artifacts = repositories.Artifacts(project=self._project,
                                               project_id=self._project_id,
                                               client_api=self._client_api,
                                               dataset_name='Buckets')
            buffer = io.BytesIO()
            buffer.name = '.keep'

            if self._snapshot is None:
                model_name = None
                snapshot_name = str(uuid.uuid1())
            else:
                model_name = self.snapshot.model.name
                snapshot_name = self.snapshot.name

            # Override names if they were explicitly given
            if item_bucket_model_name is not None:
                model_name = item_bucket_model_name
            if item_bucket_snapshot_name is not None:
                snapshot_name = item_bucket_snapshot_name

            remote_dir_path = artifacts._build_path_header(model_name=model_name,
                                                           snapshot_name=snapshot_name)
            directory = artifacts.dataset.items.make_dir(directory=remote_dir_path)
            # init an empty bucket
            bucket = entities.ItemBucket(directory_item_id=directory.id, buckets=self)
            self.upload(bucket, local_path=local_path, overwrite=True)
            # bucket.upload(local_path=local_path)
            return bucket

        elif bucket_type == entities.BucketType.LOCAL:
            bucket = entities.LocalBucket(local_path=local_path, buckets=self)
            return bucket

        elif bucket_type == entities.BucketType.GCS:
            if gcs_project_name is None or gcs_bucket_name is None:
                raise RuntimeError("Can not create GCS Bucket without project and bucket name")
            if use_existing_gcs:
                bucket = entities.GCSBucket(gcs_project_name=gcs_project_name,
                                            gcs_bucket_name=gcs_bucket_name,
                                            gcs_prefix=gcs_prefix,
                                            buckets=self)
            else:
                raise NotImplementedError(
                    'Create a new bucket in GCS platform is not yet supported. Please connect an esiting GCS bucket')
            return bucket
        else:
            raise NotImplemented('missing implementation in "buckets.create" for bucket type: {!r}'.format(bucket_type))
