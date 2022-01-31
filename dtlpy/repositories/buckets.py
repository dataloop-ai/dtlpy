import tempfile
import logging
import shutil
import uuid
import os
import io
import distutils.dir_util

from .. import entities, services, repositories

logger = logging.getLogger(name='dtlpy')


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

        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :return: list of items in bucket TBD
        :rtype: list
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            output = directory_item.dataset.items.list(filters=entities.Filters(field='dir',
                                                                                values=directory_item.filename + '*'))
        elif isinstance(bucket, entities.GCSBucket):
            gcs_bucket = bucket._bucket
            blobs = gcs_bucket.list_blobs(prefix=bucket._gcs_prefix)
            output = [b.name for b in blobs if not b.name.endswith('/')]
        elif isinstance(bucket, entities.LocalBucket):
            output = os.listdir(bucket.local_path)
        else:
            raise NotImplemented('missing implementation for "list" in bucket type: {!r}'.format(bucket.type))
        return output

    def get_single_file(self,
                        filename: str,
                        bucket: entities.Bucket):
        """

        Get a filename from bucket
        If by name or type - need to input also execution/task id for the bucket folder

        :param str filename: filename
        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :return:
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            filters = entities.Filters(field='dir', values=directory_item.filename + '*')
            filters.add(field='name', values=filename)
            output = directory_item.dataset.items.list(filters=filters)
        else:
            raise NotImplemented('missing implementation for "buckets.get" for bucket type: {!r}'.format(bucket.type))
        return output

    def download(self,
                 bucket: entities.Bucket,
                 local_path: str = None,
                 overwrite: bool = False,
                 without_relative_path: bool = True
                 ):
        """

        Download binary file from bucket.

        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :param str local_path: local binary file or folder to upload
        :param bool overwrite: optional - default = False
        :param bool without_relative_path: download items without the relative path from platform
        :return:
        """
        if isinstance(bucket, entities.ItemBucket):
            bucket_dir_item = self.items.get(item_id=bucket.directory_item_id)
            # fetch: False does not use an API call but created the dataset entity (with id)
            dataset = bucket_dir_item.datasets.get(dataset_id=bucket_dir_item.dataset_id, fetch=False)
            bucket_filter = entities.Filters(field='dir', values=bucket_dir_item.filename + '*')
            # 1. download to temp folder
            temp_dir = tempfile.mkdtemp()
            local_temp_files = list(dataset.items.download(
                filters=bucket_filter,
                local_path=temp_dir,
                overwrite=overwrite,
                to_items_folder=False,
            ))
            # 2. move to local_path without remote path prefix
            for item in bucket.list_content().all():
                for filepath in local_temp_files:
                    if os.path.join(temp_dir, item.filename[1:]) == filepath:
                        src = filepath
                        # remove the prefix with relpath
                        dst = os.path.join(local_path,
                                           os.path.relpath(item.filename, bucket_dir_item.filename))
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.move(src=src, dst=dst)
            # clean temo dir
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)

            if len(local_temp_files) == 0:
                logger.warning("Bucket {} was empty".format(bucket))
            else:
                logger.info('Bucket artifacts was unpacked to: {}'.format(local_path))

        elif isinstance(bucket, entities.GCSBucket):
            blobs = list(bucket._bucket.list_blobs(prefix=bucket._gcs_prefix))
            for blob in blobs:
                if blob.name.endswith("/"):
                    # ignore folders
                    continue
                filename = os.path.join(local_path, blob.name.replace(bucket._gcs_prefix, ''))
                if not os.path.isdir(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                blob.download_to_filename(filename=filename,
                                          client=bucket._client)
        elif isinstance(bucket, entities.LocalBucket):
            _ = distutils.dir_util.copy_tree(src=bucket.local_path, dst=local_path)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.download" for bucket type: {!r}'.format(bucket.type))
        return True

    def upload(self,
               bucket: entities.Bucket,
               # what to upload
               local_path: str,
               # add information
               overwrite: bool = False,
               file_types: list = None):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded
        For LocalBucket - this "upload" will copy the content of "local_path" to the bucket.path

        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :param str local_path: local binary file or folder to upload
        :param bool overwrite: optional - default = False
        :param list file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :return: True if success
        :rtype: bool
        """
        if isinstance(bucket, entities.ItemBucket):
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            # Upload  the artifacts files them selves rather than  the directory  # 2021-14-06
            local_files = [os.path.join(local_path, ff) for ff in os.listdir(local_path)]
            items = directory_item.dataset.items.upload(local_path=local_files,
                                                        remote_path=directory_item.filename,
                                                        overwrite=overwrite,
                                                        file_types=file_types)

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
                    if file_types is not None and os.path.splitext(file_name)[1] not in file_types:
                        continue
                    blob = gcs_bucket.blob(os.path.join(bucket._gcs_prefix, local_path[local_prefix_len:], file_name))
                    blob.upload_from_filename(os.path.join(root, file_name))
        elif isinstance(bucket, entities.LocalBucket):
            _ = distutils.dir_util.copy_tree(local_path, bucket.local_path)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.upload" for bucket type: {!r}'.format(bucket.type))
        return True

    def delete(self, bucket: entities.Bucket):
        """
        Delete bucket

        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :return: True if success
        :rtype: bool
        """
        if isinstance(bucket, entities.ItemBucket):
            path = self.items.delete(item_id=bucket.directory_item_id)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.delete" for bucket type: {!r}'.format(bucket.type))
        return path

    def create(self, bucket_type=entities.BucketType.ITEM,
               # item bucket / local_bucket
               local_path: str = None,
               # gcs bucket
               gcs_project_name: str = None,
               gcs_bucket_name: str = None,
               gcs_prefix: str = '/',
               use_existing_gcs: bool = True,
               # item_bucket names
               model_name: str = None,
               snapshot_name: str = None,

               ):
        """
        Create a new bucket- directory contains the artifacts (weights and other configurations) of the model.
        Available Bucket type:
        Local Bucket: is simply a the path to where the bucket is stored locally . environment vars are valid
        Item Bucket: is used when you want to store your binary files of the model on our Dataloop Platform, they are saved i a different dataset in a defined path
        Gcs Bucket: is used when you have a Google Cloud Storage bucket and you can connect to it, save / download your models directly to the bucket

        :param str bucket_type: `dl.BucketType`: Local, Item, Gcs
        :param str local_path: where were the weights are currently saved - what directory to upload to the bucket
        :param str gcs_project_name: project name in your GCS (Google Cloud Storage) platform
        :param str gcs_bucket_name: bucket name in your GCS
        :param str gcs_prefix:  prefix/ remote path of where your bucket is defined in GCS
        :param str model_name: optional to override the repo settings
        :param str snapshot_name: optional to override the repo settings
        :param bool use_existing_gcs: use existing gcs

        :return: `dl.Bucket`
        :rtype: dtlpy.entities.bucket.Bucket
        """

        if bucket_type == entities.BucketType.ITEM:
            artifacts = repositories.Artifacts(project=self._project,
                                               project_id=self._project_id,
                                               client_api=self._client_api)
            buffer = io.BytesIO()
            buffer.name = '.keep'
            if model_name is None:
                model_name = str(uuid.uuid1())
                if self._snapshot is not None and self._snapshot._model is not None:
                    model_name = self.snapshot.model.name
            if snapshot_name is None:
                snapshot_name = str(uuid.uuid1())
                if self._snapshot is not None:
                    snapshot_name = self.snapshot.name

            remote_dir_path = artifacts._build_path_header(model_name=model_name,
                                                           snapshot_name=snapshot_name)
            directory = artifacts.dataset.items.make_dir(directory=remote_dir_path)
            # init an empty bucket
            bucket = entities.ItemBucket(directory_item_id=directory.id, buckets=self)
            if local_path is not None:
                self.upload(bucket,
                            local_path=local_path,
                            overwrite=True)
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

    def clone(self,
              src_bucket: entities.Bucket,
              dst_bucket: entities.Bucket):
        """
        Clone the entire bucket's content

        :param dtlpy.entities.bucket.Bucket src_bucket: source bucket
        :param dtlpy.entities.bucket.Bucket dst_bucket: dist bucket
        """
        temp_dir = tempfile.mkdtemp()
        src_bucket.download(local_path=temp_dir)
        dst_bucket.upload(local_path=temp_dir)
        shutil.rmtree(temp_dir)

    def empty_bucket(self,
                     bucket: entities.Bucket,
                     sure: bool = False):
        """
        Delete the entire bucket's content

        :param dtlpy.entities.bucket.Bucket bucket: Bucket entity
        :param bool sure: must be True to perform the action
        :return: True is deletion was successful
        :rtype: bool
        """

        if not sure:
            raise ValueError('Trying the delete ALL bucket\'s files! If you are sure use param: sure=True')

        if isinstance(bucket, entities.ItemBucket):
            # delete entire folder content with DQL
            directory_item = self.items.get(item_id=bucket.directory_item_id)
            filters = entities.Filters(field='dir', values=directory_item.filename + '*')
            directory_item.dataset.items.delete(filters=filters)
        elif isinstance(bucket, entities.GCSBucket):
            raise NotImplemented(
                'missing implementation for "buckets.empty_bucket" for bucket type: {!r}'.format(bucket.type))
        elif isinstance(bucket, entities.LocalBucket):
            # remove directory and create an empty one
            shutil.rmtree(bucket.local_path)
            os.makedirs(bucket.local_path)
        else:
            raise NotImplemented(
                'missing implementation for "buckets.empty_bucket" for bucket type: {!r}'.format(bucket.type))
        return True
