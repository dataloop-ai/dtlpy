import os
import logging

from .. import entities, services, repositories

logger = logging.getLogger(name='dtlpy')


class BucketType:
    ITEM = 'item'
    GCS = 'gcs'
    LOCAL = 'local'


class Bucket:
    def __init__(self,
                 bucket_type=BucketType.LOCAL,
                 buckets=None,
                 client_api=None,
                 ):
        self.type = bucket_type
        if buckets is None and client_api is not None:
            buckets = repositories.Buckets(client_api=client_api)
        self._buckets = buckets

    def __str__(self):
        return str(self.to_json())

    # @_repositories.default
    # def set_repositories(self):
    #     reps = namedtuple('repositories',
    #                       field_names=['projects', 'buckets'])

    #     r = reps(projects=repositories.Projects(client_api=self._client_api),
    #              buckets=repositories.Buckets(client_api=self._client_api,
    #                                           project=self._project,
    #                                           snapshot=self._snapshot)

    def to_json(self):
        _json = {'type': self.type}
        return _json

    @staticmethod
    def from_json(_json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        """
        Build a Bucket entity object from a json

        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :return: Bucket
        """
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

    def list_content(self):
        """
        :return:  list of the the content in the bucket
        """
        return self.buckets.list_content(self)

    def empty_bucket(self, sure: bool = False):
        """
        Delete the entire bucket's content

        :param sure: bool. must be True to perform the action
        """
        self.buckets.empty_bucket(bucket=self, sure=sure)

    def upload(self, local_path, overwrite=False, file_types=None):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded

        :param local_path: local binary file or folder to upload
        :param overwrite: optional - default = False
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :return:
        """
        self.buckets.upload(bucket=self,
                            local_path=local_path,
                            overwrite=overwrite,
                            file_types=file_types
                            )

    def download(self,
                 local_path=None,
                 overwrite=False,
                 ):
        """

        Download binary file from bucket.

        :param local_path: local binary file or folder to upload
        :param overwrite: optional - default = False
        :return:
        """
        self.buckets.download(bucket=self,
                              local_path=local_path,
                              overwrite=overwrite)


class ItemBucket(Bucket):
    def __init__(self, directory_item_id: str, buckets=None):
        super().__init__(bucket_type=BucketType.ITEM, buckets=buckets)
        self.directory_item_id = directory_item_id

    def to_json(self):
        _json = super().to_json()
        _json['itemId'] = self.directory_item_id
        return _json

    @classmethod
    def from_json(cls, _json: dict,
                  client_api: services.ApiClient,
                  project: entities.Project):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :return: ItemBucket
        """
        return cls(
            directory_item_id=_json.get('itemId')
        )


class LocalBucket(Bucket):
    """ Local FileSystem base Bucket.
        Manage file on user responsibility
    """

    def __init__(self, local_path: str = None, buckets=None):
        super().__init__(bucket_type=BucketType.LOCAL, buckets=buckets)
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
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :return: LocalBucket
        """
        return cls(local_path=_json.get('localPath', None), )


class GCSBucket(Bucket):
    """ Google Cloud Storage based bucket
    https://cloud.google.com/docs/authentication/getting-started
    """

    def __init__(self, gcs_project_name: str, gcs_bucket_name: str, gcs_prefix: str = '', buckets=None):
        try:
            from google.cloud import storage
        except (ModuleNotFoundError, ImportError) as err:
            raise RuntimeError('dtlpy requires external package. Please install and re-run') from err

        super().__init__(bucket_type=BucketType.GCS, buckets=buckets)
        self._gcs_project_name = gcs_project_name
        self._gcs_bucket_name = gcs_bucket_name
        if len(gcs_prefix) > 0 and not gcs_prefix.endswith('/'):
            # prefix should end with a backslash (directory)
            gcs_prefix += '/'
        self._gcs_prefix = gcs_prefix

        # Connect to GCS
        #   Requires application credentials
        if self._gcs_bucket_name is None or self._gcs_project_name is None:
            print('invalid bucket with no gcs names')
            self._bucket = None
        else:
            self._client = storage.Client.create_anonymous_client()
            self._bucket = self._client.bucket(self._gcs_bucket_name)

    def to_json(self):
        _json = super().to_json()
        _json['gcsProjectName'] = self._gcs_project_name
        _json['gcsBucketName'] = self._gcs_bucket_name
        _json['gcsPrefix'] = self._gcs_prefix
        return _json

    @classmethod
    def from_json(
            cls,
            _json: dict,
            client_api: services.ApiClient,
            project: entities.Project):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        :param project: project entity
        :return: GCSBucket
        """
        return cls(
            gcs_project_name=_json.get('gcsProjectName'),
            gcs_bucket_name=_json.get('gcsBucketName'),
            gcs_prefix=_json.get('gcsPrefix'),
        )
