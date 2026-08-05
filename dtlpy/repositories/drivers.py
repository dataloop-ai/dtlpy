import logging
import re

from .. import entities, miscellaneous, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name="dtlpy")


class Drivers:
    """
    Drivers Repository

    The Drivers class allows users to manage drivers that are used to connect with external storage.
    Read more about external storage in our `documentation <https://dataloop.ai/docs/overview-1>`_ and `developers' docs <https://developers.dataloop.ai/tutorials/data_management/>`_.
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        """
        Initialize the Drivers repository.

        :param ApiClient client_api: The API client instance
        :param Project project: Optional project entity. If not provided, will try to get from checkout
        """
        self._client_api = client_api
        # Try to get checked out project if project is None
        if project is None:
            checked_out_project = client_api.state_io.get("project")
            if checked_out_project is not None:
                project = entities.Project.from_json(_json=checked_out_project, client_api=client_api)
        self.project = project

    ###########
    # methods #
    ###########
    def __get_by_id(self, driver_id) -> entities.Driver:
        """
        Get a driver by its ID from the platform.

        :param str driver_id: The driver ID
        :return: Driver object
        :rtype: dtlpy.entities.driver.Driver
        :raises PlatformException: If the driver is not found or there's an API error
        """
        success, response = self._client_api.gen_request(req_type="get", path="/drivers/{}".format(driver_id))
        if self._client_api.check_response(success, response, path="/drivers") is False:
            return None

        _json = response.json()
        driver = self._get_driver_class(_json).from_json(client_api=self._client_api, _json=_json)
        return driver

    @_api_reference.add(path="/drivers", method="get")
    def list(self) -> miscellaneous.List[entities.Driver]:
        """
        Get the project's drivers list.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :return: List of Drivers objects
        :rtype: list

        **Example**:

        .. code-block:: python

            project.drivers.list()

        """

        success, response = self._client_api.gen_request(
            req_type="get", path="/drivers?projectId={}".format(self.project.id)
        )
        if self._client_api.check_response(success, response, path="/drivers?projectId={}".format(self.project.id)) is False:
            return None
        drivers = miscellaneous.List(
            [
                self._get_driver_class(_json).from_json(_json=_json, client_api=self._client_api)
                for _json in response.json()
            ]
        )
        return drivers

    def _get_driver_class(self, _json):
        """
        Determine the appropriate driver class based on the driver type in the JSON response.

        :param dict _json: The JSON response containing driver information
        :return: The appropriate driver class (S3Driver, GcsDriver, AzureBlobDriver, ComputeClusterDriver, or Driver)
        :rtype: type
        """
        driver_type = _json.get("type", None)
        if driver_type == entities.ExternalStorage.S3:
            driver_class = entities.S3Driver
        elif driver_type == entities.ExternalStorage.GCS:
            driver_class = entities.GcsDriver
        elif driver_type in [entities.ExternalStorage.AZUREBLOB, entities.ExternalStorage.AZURE_DATALAKE_GEN2]:
            driver_class = entities.AzureBlobDriver
        elif driver_type == entities.ExternalStorage.COMPUTE_CLUSTER:
            driver_class = entities.ComputeClusterDriver
        elif driver_type == entities.ExternalStorage.STORAGE:
            driver_class = entities.Driver
        else:
            driver_class = entities.Driver
        return driver_class

    @_api_reference.add(path="/drivers/{id}", method="get")
    def get(self, driver_name: str = None, driver_id: str = None) -> entities.Driver:
        """
        Get a Driver object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        You must provide at least ONE of the following params: driver_name, driver_id.

        :param str driver_name: optional - search by name
        :param str driver_id: optional - search by id
        :return: Driver object
        :rtype: dtlpy.entities.driver.Driver

        **Example**:

        .. code-block:: python

            project.drivers.get(driver_id='driver_id')
        """
        if driver_id is not None:
            driver = self.__get_by_id(driver_id)
        elif driver_name is not None:
            drivers = self.list()
            driver = [driver for driver in drivers if driver.name == driver_name]
            if not driver:
                # list is empty
                raise exceptions.PlatformException(
                    error="404", message="Driver not found. Name: {}".format(driver_name)
                )
                # driver = None
            elif len(driver) > 1:
                # more than one matching driver
                raise exceptions.PlatformException(
                    error="404", message='More than one driver with same name. Please "get" by id'
                )
            else:
                driver = driver[0]
        else:
            raise exceptions.PlatformException(error="400", message="Must provide an identifier (name or id) in inputs")
        return driver

    @_api_reference.add(path="/drivers", method="post")
    def _create_driver(self, payload: dict):
        """
        Create a driver on the platform using the provided payload.

        :param dict payload: The driver creation payload
        :return: The created driver object
        :rtype: dtlpy.entities.driver.Driver
        :raises PlatformException: If the driver creation fails
        """
        success, response = self._client_api.gen_request(req_type="post", path="/drivers", json_req=payload)
        if self._client_api.check_response(success, response, path="/drivers") is False:
            return None
        _json = response.json()
        return self._get_driver_class(_json).from_json(_json=_json, client_api=self._client_api)

    def create(
        self,
        name: str,
        driver_type: entities.ExternalStorage,
        integration_id: str,
        bucket_name: str,
        integration_type: entities.IntegrationType,
        project_id: str = None,
        allow_external_delete: bool = True,
        region: str = None,
        storage_class: str = "",
        path: str = "",
        endpoint: str = None
    ):
        """
        Create a storage driver.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str name: the driver name
        :param ExternalStorage driver_type: dl.ExternalStorage (Enum). For all options run: list(dl.ExternalStorage)
        :param str integration_id: the integration id
        :param str bucket_name: the external bucket name
        :param IntegrationType integration_type: dl.IntegrationType (Enum). For all options run: list(dl.IntegrationType)
        :param str project_id: project id
        :param bool allow_external_delete: true to allow deleting files from external storage when files are deleted in your Dataloop storage
        :param str region: relevant only for s3 - the bucket region
        :param str storage_class: relevant only for s3
        :param str path: Optional. By default path is the root folder. Path is case sensitive integration
        :param str endpoint: Optional. Custom endpoint for minio storage. Must be in the format 'http://<hostname>:<port>' or 'https://<hostname>:<port>'.
        :return: driver object
        :rtype: dtlpy.entities.driver.Driver

        **Example**:

        .. code-block:: python

            project.drivers.create(name='driver_name',
                       driver_type=dl.ExternalStorage.S3,
                       integration_id='integration_id',
                       bucket_name='bucket_name',
                       project_id='project_id',
                       region='ey-west-1')
        """
        if integration_type is None:
            integration_type = driver_type
        if driver_type == entities.ExternalStorage.S3:
            bucket_payload = "bucketName"
            if endpoint:
                if not re.match(r"^https?://[A-Za-z0-9.-]+:\d+$", endpoint):
                    raise ValueError(
                        f"Invalid endpoint URL '{endpoint}'. Must be 'http://<hostname>:<port>' or 'https://<hostname>:<port>'."
                    )

        elif driver_type == entities.ExternalStorage.GCS or driver_type == entities.ExternalStorage.FAAS_PROXY:
            bucket_payload = "bucket"
        else:
            bucket_payload = "containerName"
        payload = {
            "integrationId": integration_id,
            "integrationType": integration_type,
            "name": name,
            "metadata": {"system": {"projectId": self.project.id if project_id is None else project_id}},
            "type": driver_type,
            "payload": {bucket_payload: bucket_name, "storageClass": storage_class, "region": region, "path": path},
            "allowExternalDelete": allow_external_delete,
            "creator": self._client_api.info().get("user_email"),
        }

        if endpoint and driver_type == entities.ExternalStorage.S3:
            payload["payload"]["endpoint"] = endpoint

        return self._create_driver(payload)


    def create_storage_driver(
        self,
        name: str,
        integration: entities.Integration,
        bucket_name: str = None,
        directory: str = None,
        path: str = None,
        allow_external_delete: bool = True,
        project_id: str = None,
        elastic_index: str = None,
        elastic_index_path: str = None,
    ) -> entities.Driver:
        """
        Create a storage driver for NFS, hostPath, or S3-compatible API integrations.

        The driver type is determined automatically from the integration type:

        - **NFS / hostPath**: use ``directory`` for the subdirectory within the mount.
        - **S3-compatible API**: use ``bucket_name`` (required) and optionally ``path`` for prefix.
        - **Dell PowerScale**: pass ``elastic_index`` and ``elastic_index_path`` for Elastifile-backed volumes.

        The compute cluster association and endpoint/region (for S3) are resolved automatically by the backend.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str name: driver name
        :param Integration integration: storage integration (type must be NFS, hostPath, or S3)
        :param str bucket_name: bucket name (required for S3-compatible API integrations)
        :param str directory: optional - subdirectory within the NFS share or hostPath volume. Leading slash is enforced.
        :param str path: optional - path prefix within an S3 bucket (e.g. 'datasets/project1')
        :param bool allow_external_delete: True to allow deleting files from external storage (default: True)
        :param str project_id: optional - project ID. If not provided, uses the current project
        :param str elastic_index: optional - Elastifile index name (Dell PowerScale only)
        :param str elastic_index_path: optional - Elastifile index path (Dell PowerScale only)
        :return: Driver object
        :rtype: dtlpy.entities.driver.Driver
        :raises ValueError: If the integration type is not supported or required params are missing

        **Example**:

        .. code-block:: python

            # NFS driver
            nfs_integration = project.integrations.create_nfs(
                name='my-nfs', server='10.0.0.50', path='/exports/data'
            )
            project.drivers.create_storage_driver(
                name='my-nfs-driver', integration=nfs_integration
            )

            # S3-compatible API driver
            s3_integration = project.integrations.create_s3_compatible_api(
                name='my-minio', key='key', secret='secret',
                endpoint='http://10.0.0.1:9000'
            )
            project.drivers.create_storage_driver(
                name='my-minio-driver', integration=s3_integration,
                bucket_name='my-bucket'
            )

        """
        supported_types = [entities.IntegrationType.NFS, entities.IntegrationType.HOST_PATH, entities.IntegrationType.S3]
        if integration.type not in supported_types:
            raise ValueError(
                f"Integration type must be one of {[t.value for t in supported_types]}, got '{integration.type}'"
            )

        if integration.type == entities.IntegrationType.S3:
            if bucket_name is None:
                raise ValueError("bucket_name is required for S3-compatible API drivers")
            driver_payload = {"bucketName": bucket_name, "path": path}
        else:
            if directory is not None and not directory.startswith('/'):
                directory = '/' + directory
            driver_payload = {"directory": directory}

        if elastic_index is not None:
            driver_payload["elasticIndex"] = elastic_index
        if elastic_index_path is not None:
            driver_payload["elasticIndexPath"] = elastic_index_path

        payload = {
            "integrationId": integration.id,
            "integrationType": integration.type,
            "name": name,
            "metadata": {"system": {"projectId": self.project.id if project_id is None else project_id}},
            "type": entities.ExternalStorage.STORAGE,
            "payload": driver_payload,
            "allowExternalDelete": allow_external_delete,
            "creator": self._client_api.info().get("user_email"),
        }
        return self._create_driver(payload)

    @_api_reference.add(path="/drivers/{id}", method="delete")
    def delete(self, driver_name: str = None, driver_id: str = None, sure: bool = False, really: bool = False):
        """
        Delete a driver forever!

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        **Example**:

        .. code-block:: python

            project.drivers.delete(dataset_id='dataset_id', sure=True, really=True)

        :param str driver_name: optional - search by name
        :param str driver_id: optional - search by id
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: True if success
        :rtype: bool
        """
        if sure and really:
            driver = self.get(driver_name=driver_name, driver_id=driver_id)
            success, response = self._client_api.gen_request(req_type="delete", path="/drivers/{}".format(driver.id))
            if self._client_api.check_response(success, response, path="/drivers/{}".format(driver.id)) is False:
                return False
            logger.info("Driver {!r} was deleted successfully".format(driver.name))
            return True
        else:
            raise exceptions.PlatformException(
                error="403", message="Cant delete driver from SDK. Please login to platform to delete"
            )
