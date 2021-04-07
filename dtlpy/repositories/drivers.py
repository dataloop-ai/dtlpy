import logging

from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Drivers:
    """
    Drivers repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
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
            driver = entities.Driver.from_json(client_api=self._client_api,
                                               _json=response.json())
        else:
            raise exceptions.PlatformException(response)
        return driver

    def list(self) -> miscellaneous.List[entities.Driver]:
        """
        Get project's drivers list.
        :return: List of Drivers objects
        """

        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/drivers?projectId={}'.format(self.project.id))
        if not success:
            raise exceptions.PlatformException(response)
        drivers = miscellaneous.List([entities.Driver.from_json(_json=_json,
                                                                client_api=self._client_api) for _json in
                                      response.json()])
        return drivers

    def get(self,
            driver_name: str = None,
            driver_id: str = None) -> entities.Driver:
        """
        Get a Driver object
        :param driver_name: optional - search by name
        :param driver_id: optional - search by id
        :return: Driver object

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
