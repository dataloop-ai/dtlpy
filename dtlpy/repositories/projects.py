import logging
from .. import entities, utilities, PlatformException
import attr


@attr.s
class Projects:
    """
    Projects repository
    """
    client_api = attr.ib()
    logger = attr.ib(default=logging.getLogger('dataloop.repositories.projects'))

    def __get_by_id(self, project_id):
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/projects/%s' % project_id)
        if success:
            project = entities.Project.from_json(client_api=self.client_api,
                                                 _json=response.json())
        else:
            self.logger.exception('Platform error getting project. id: %s', project_id)
            raise PlatformException('404', 'Project not found.')
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
        if self.client_api.environment == 'https://gate.dataloop.ai/api/v1':
            head = 'https://console.dataloop.ai'
        elif self.client_api.environment == 'https://dev-gate.dataloop.ai/api/v1':
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
        self.client_api.state_io.put('project', project.id)
        self.logger.info('Checked out to project {}'.format(project.name))

    def list(self):
        """
        Get users project's list.
        :return: List of Project objects
        """
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/projects')
        if success:
            projects = utilities.List(
                [entities.Project.from_json(client_api=self.client_api,
                                            _json=_json)
                 for _json in response.json()])
        else:
            self.logger.exception('Platform error getting projects')
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
                self.logger.info('Project not found. project_name: %s', project_name)
                raise PlatformException('404', 'Project not found.')
                # project = None
            elif len(project) > 1:
                # more than one matching project
                self.logger.exception('More than one project with same name. Please "get" by id')
                raise PlatformException('404', 'More than one project with same name. Please "get" by id')
            else:
                project = project[0]
        else:
            # get from state cookie
            state_project_id = self.client_api.state_io.get('project')
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
            success, response = self.client_api.gen_request('delete', '/projects/%s' % project.id)
            if not success:
                self.logger.exception('Platform error deleting a project')
                raise PlatformException(response)
            return True

        else:
            raise PlatformException(error='403',
                                    message='Cant delete project from SDK. Please login to platform to delete')

    def update(self, project, system_metadata=False):
        """
        Update a project
        :return: Project object
        """
        url_path = '/projects/%s' % project.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=project.to_json())
        if success:
            return project
        else:
            self.logger.exception('Platform error updating dataset. id: %s' % project.id)
            raise PlatformException(response)

    def create(self, project_name):
        """
        Create a new project
        :param project_name:
        :return: Project object
        """
        payload = {'name': project_name}
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/projects',
                                                        data=payload)
        if success:
            project = entities.Project.from_json(client_api=self.client_api,
                                                 _json=response.json())
        else:
            self.logger.exception('Platform error creating a project')
            raise PlatformException(response)
        assert isinstance(project, entities.Project)
        return project
