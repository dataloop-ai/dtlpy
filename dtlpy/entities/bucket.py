import os
from .. import entities, services, repositories


class BucketType:
    ITEM = 'item'
    GCS = 'gcs'
    LOCAL = 'local'


class Bucket:
    def __init__(self,
                 bucket_type=BucketType.LOCAL,
                 buckets=None):
        self.type = bucket_type
        self._buckets = buckets

    def to_json(self):
        _json = {'type': self.type}
        return _json

    @staticmethod
    def from_json(_json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        if _json['type'] == BucketType.ITEM:
            cls = ItemBucket.from_json(_json=_json,
                                       client_api=client_api,
                                       project=project)
        elif _json['type'] == BucketType.LOCAL:
            cls = LocalBucket.from_json(_json=_json,
                                        client_api=client_api,
                                        project=project)
        elif _json['type'] == BucketType.GCS:
            cls = GCSBucket.from_json(_json=_json,
                                      client_api=client_api,
                                      project=project)
        else:
            raise ValueError('[Bucket constructor] Unknown bucket type: {}'.format(_json['type']))

        cls._buckets = repositories.Buckets(client_api=client_api,
                                            project=project)
        return cls

    @property
    def buckets(self):
        assert isinstance(self._buckets, repositories.Buckets)
        return self._buckets

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return self.type in [BucketType.ITEM, BucketType.GCS]


class ItemBucket(Bucket):
    def __init__(self, directory_item_id: str):
        super().__init__(bucket_type=BucketType.ITEM)
        self.directory_item_id = directory_item_id

    def to_json(self):
        _json = super().to_json()
        _json['itemId'] = self.directory_item_id
        return _json

    @classmethod
    def from_json(cls, _json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        return cls(
            directory_item_id=_json.get('itemId')
        )

    def upload(self, local_path, overwrite=False):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded

        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        self.buckets.upload(bucket=self,
                            local_path=local_path,
                            overwrite=overwrite)

    def download(self,
                 remote_paths=None,
                 local_path=None,
                 overwrite=False,
                 ):
        """

        Download binary file from bucket.

        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        self.buckets.download(bucket=self,
                              local_path=local_path,
                              remote_paths=remote_paths,
                              overwrite=overwrite)


class LocalBucket(Bucket):
    """ Local FileSystem base Bucket.
        Manage file on user responsibility
    """

    def __init__(self, local_path: str = None):
        super().__init__(bucket_type=BucketType.LOCAL)
        self._local_path = local_path

    def to_json(self):
        _json = super().to_json()
        if self._local_path is not None:
            _json['localPath'] = self._local_path
        return _json

    @property
    def local_path(self):
        """ Returns the local path using environment variables in the path"""
        return os.path.expandvars(self._local_path)

    @local_path.setter
    def local_path(self, local_path: str):
        self._local_path = local_path

    @classmethod
    def from_json(cls, _json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        return cls(
            local_path=_json.get('localPath', None),
        )


class GCSBucket(Bucket):
    """ Google Cloud Storage based bucket
    https://cloud.google.com/docs/authentication/getting-started
    """

    def __init__(self, gcs_project_name: str, gcs_bucket_name: str, prefix: str = '/', gcs_url: str = None):
        from google.cloud import storage
        super().__init__(bucket_type=BucketType.GCS)
        self.gcs_url = gcs_url
        self._gcs_project_name = gcs_project_name
        self._gcs_bucket_name = gcs_bucket_name
        self.prefix = prefix

        # Connect to GCS
        #   Requires application credentials
        self._client = storage.Client(project=self._gcs_project_name)
        self._bucket = self._client().get_bucket(self._gcs_bucket_name)

    def to_json(self):
        _json = super().to_json()
        _json['gcsUrl'] = self.gcs_url
        _json['_gcs_project_name'] = self._gcs_project_name
        _json['_gcs_bucket_name'] = self._gcs_bucket_name
        return _json

    @classmethod
    def from_json(cls, _json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        return cls(
            gcs_url=_json.get('gcsUrl'),
            gcs_project_name=_json.get('_gcs_project_name'),
            gcs_bucket_name=_json.get('_gcs_bucket_name'),
        )

    def upload(self, local_path, overwrite=False):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded

        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        self.buckets.upload(bucket=self,
                            local_path=local_path,
                            overwrite=overwrite)

    def download(self,
                 remote_paths=None,
                 local_path=None,
                 overwrite=False,
                 ):
        """

        Download binary file from bucket.

        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        self.buckets.download(bucket=self,
                              local_path=local_path,
                              remote_paths=self.prefix,
                              overwrite=overwrite)
