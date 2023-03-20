import logging

from .. import entities, miscellaneous, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Drivers:
    """
    Drivers Repository
    
    The Drivers class allows users to manage drivers that are used to connect with external storage. Read more about external storage in our `documentation <https://dataloop.ai/docs/storage>`_ and `SDK documentation <https://dataloop.ai/docs/sdk-sync-storage>`_.
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Drivers repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def __get_by_id(self, driver_id) -> entities.Driver:
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/drivers/{}'.format(driver_id))
        if success:
            _json = response.json()
            driver = self._getDriverClass(_json).from_json(client_api=self._client_api,
                                                           _json=_json)
        else:
            raise exceptions.PlatformException(response)
        return driver

    @_api_reference.add(path='/drivers?projectId={id}', method='get')
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

        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/drivers?projectId={}'.format(self.project.id))
        if not success:
            raise exceptions.PlatformException(response)
        drivers = miscellaneous.List([self._getDriverClass(_json).from_json(_json=_json,
                                                                            client_api=self._client_api) for _json in
                                      response.json()])
        return drivers

    def _getDriverClass(self, _json):
        driver_type = _json.get('type', None)
        if driver_type == entities.ExternalStorage.S3:
            driver_class = entities.S3Driver
        elif driver_type == entities.ExternalStorage.GCS:
            driver_class = entities.GcsDriver
        elif driver_type in [entities.ExternalStorage.AZUREBLOB, entities.ExternalStorage.AZURE_DATALAKE_GEN2]:
            driver_class = entities.AzureBlobDriver
        else:
            driver_class = entities.Driver
        return driver_class

    @_api_reference.add(path='/drivers/{id}', method='get')
    def get(self,
            driver_name: str = None,
            driver_id: str = None) -> entities.Driver:
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
                raise exceptions.PlatformException(error='404',
                                                   message='Driver not found. Name: {}'.format(driver_name))
                # driver = None
            elif len(driver) > 1:
                # more than one matching driver
                raise exceptions.PlatformException(
                    error='404',
                    message='More than one driver with same name. Please "get" by id')
            else:
                driver = driver[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier (name or id) in inputs')
        return driver

    @_api_reference.add(path='/drivers', method='post')
    def create(self,
               name: str,
               driver_type: entities.ExternalStorage,
               integration_id: str,
               bucket_name: str,
               integration_type: entities.ExternalStorage,
               project_id: str = None,
               allow_external_delete: bool = True,
               region: str = None,
               storage_class: str = "",
               path: str = ""):
        """
        Create a storage driver.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str name: the driver name
        :param str driver_type: ExternalStorage.S3, ExternalStorage.GCS, ExternalStorage.AZUREBLOB
        :param str integration_id: the integration id
        :param str bucket_name: the external bucket name
        :param str integration_type: ExternalStorage.S3, ExternalStorage.GCS, ExternalStorage.AZUREBLOB, ExternalStorage.AWS_STS
        :param str project_id: project id
        :param bool allow_external_delete: true to allow deleting files from external storage when files are deleted in your Dataloop storage
        :param str region: relevant only for s3 - the bucket region
        :param str storage_class: rilevante only for s3
        :param str path: Optional. By default path is the root folder. Path is case sensitive integration
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
            bucket_payload = 'bucketName'
        elif driver_type == entities.ExternalStorage.GCS:
            bucket_payload = 'bucket'
        else:
            bucket_payload = 'containerName'
        payload = {
            "integrationId": integration_id,
            'integrationType': integration_type,
            "name": name,
            "metadata": {
                "system": {
                    "projectId": self.project.id if project_id is None else project_id
                }
            },
            "type": driver_type,
            "payload": {
                bucket_payload: bucket_name,
                "storageClass": storage_class,
                "region": region,
                "path": path
            },
            "allowExternalDelete": allow_external_delete,
            "creator": self._client_api.info().get('user_email')
        }

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/drivers',
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        else:
            _json = response.json()
            return self._getDriverClass(_json).from_json(_json=_json, client_api=self._client_api)

    @_api_reference.add(path='/drivers/{id}', method='delete')
    def delete(self,
               driver_name: str = None,
               driver_id: str = None,
               sure: bool = False,
               really: bool = False):
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
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/drivers/{}'.format(driver.id))
            if not success:
                raise exceptions.PlatformException(response)
            logger.info('Driver {!r} was deleted successfully'.format(driver.name))
            return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete driver from SDK. Please login to platform to delete')
