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
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/projects/%s' % project_id)
            if success:
                project = entities.Project.from_json(client_api=self.client_api,
                                                     _json=response.json())
            else:
                self.logger.exception('Platform error getting project. id: %s', project_id)
                raise PlatformException('404', 'Project not found.')
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
            self.logger.exception('Must choose by at least one. "project_id" or "project_name"')
            raise PlatformException('404', 'Must choose by at least one. "project_id" or "project_name"')
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
        return project
