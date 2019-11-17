import logging
from .. import entities, miscellaneous, PlatformException

logger = logging.getLogger(name=__name__)


class Projects:
    """
    Projects repository
    """

    def __init__(self, client_api):
        self._client_api = client_api

    def __get_by_id(self, project_id):
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}'.format(project_id))
        if success:
            project = entities.Project.from_json(client_api=self._client_api,
                                                 _json=response.json())
        else:
            # raise PlatformException(response)
            # TODO because of a bug in gate wrong error is returned so for now manually raise not found
            raise PlatformException(error="404", message="Project not found")
        return project

    def __get_by_identifier(self, identifier):
        projects = self.list()
        projects_by_name = [project for project in projects if project.name == identifier]
        if len(projects_by_name) == 1:
            return projects_by_name[0]
        elif len(projects_by_name) > 1:
            raise Exception('Multiple projects with this name exist')

        projects_by_partial_id = [project for project in projects if project.id.startswith(identifier)]
        if len(projects_by_partial_id) == 1:
            return projects_by_partial_id[0]
        elif len(projects_by_partial_id) > 1:
            raise Exception("Multiple projects whose id begins with {} exist".format(identifier))
        raise Exception("Project not found")

    def open_in_web(self, project_name=None, project_id=None, project=None):
        import webbrowser
        if self._client_api.environment == 'https://gate.dataloop.ai/api/v1':
            head = 'https://console.dataloop.ai'
        elif self._client_api.environment == 'https://dev-gate.dataloop.ai/api/v1':
            head = 'https://dev-con.dataloop.ai'
        else:
            raise PlatformException('400', 'Unknown environment')
        if project is None:
            project = self.get(project_name=project_name, project_id=project_id)
        project_url = head + '/project-overview/{}'.format(project.id)
        webbrowser.open(url=project_url, new=2, autoraise=True)

    def checkout(self, identifier):
        """
        Check-out as project
        :param identifier: project name or partial id
        :return:
        """
        project = self.__get_by_identifier(identifier)
        self._client_api.state_io.put('project', project.id)
        logger.info('Checked out to project {}'.format(project.name))

    def list(self):
        """
        Get users project's list.
        :return: List of Project objects
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects')

        if success:
            pool = self._client_api.thread_pool_entities
            projects_json = response.json()
            jobs = [None for _ in range(len(projects_json))]
            # return triggers list
            for i_project, project in enumerate(projects_json):
                jobs[i_project] = pool.apply_async(entities.Project._protected_from_json,
                                                   kwds={'client_api': self._client_api,
                                                         '_json': project})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all resutls
            results = [j.get() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            projects = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.exception('Platform error getting projects')
            raise PlatformException(response)
        return projects

    def get(self, project_name=None, project_id=None):
        """
        Get a Project object
        :param project_name: optional - search by name
        :param project_id: optional - search by id
        :return: Project object

        """

        if project_id is not None:
            project = self.__get_by_id(project_id)
        elif project_name is not None:
            projects = self.list()
            project = [project for project in projects if project.name == project_name]
            if not project:
                # list is empty
                raise PlatformException('404', 'Project not found. Name: {}'.format(project_name))
                # project = None
            elif len(project) > 1:
                # more than one matching project
                raise PlatformException('404', 'More than one project with same name. Please "get" by id')
            else:
                project = project[0]
        else:
            # get from state cookie
            state_project_id = self._client_api.state_io.get('project')
            if state_project_id is None:
                raise PlatformException('400', 'Must choose by "project_id" or "project_name" OR checkout a project')
            else:
                project = self.__get_by_id(state_project_id)
        return project

    def delete(self, project_name=None, project_id=None, sure=False, really=False):
        """
        Delete a project forever!
        :param project_name: optional - search by name
        :param project_id: optional - search by id
        :param sure: are you sure you want to delete?
        :param really: really really?

        :return: True
        """
        if sure and really:
            project = self.get(project_name=project_name, project_id=project_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/projects/{}'.format(project.id))
            if not success:
                raise PlatformException(response)
            logger.info('Project {} deleted successfully'.format(project.name))
            return True

        else:
            raise PlatformException(error='403',
                                    message='Cant delete project from SDK. Please login to platform to delete')

    def update(self, project, system_metadata=False):
        """
        Update a project
        :return: Project object
        """
        url_path = '/projects/{}'.format(project.id)
        if system_metadata:
            url_path += '?system=true'
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=project.to_json())
        if success:
            return project
        else:
            raise PlatformException(response)

    def create(self, project_name):
        """
        Create a new project
        :param project_name:
        :return: Project object
        """
        payload = {'name': project_name}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects',
                                                         data=payload)
        if success:
            project = entities.Project.from_json(client_api=self._client_api,
                                                 _json=response.json())
        else:
            raise PlatformException(response)
        assert isinstance(project, entities.Project)
        return project
