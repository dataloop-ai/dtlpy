"""
Project Repository
"""
import logging

from .. import services, entities, utilities


class Projects:
    """
        Projects repository
    """

    def __init__(self):
        self.logger = logging.getLogger('dataloop.repositories.projects')
        self.client_api = services.ApiClient()

    def list(self):
        """
        Get users project's list.
        :return: List of Project objects
        """
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/projects')
        if success:
            projects = utilities.List([entities.Project(entity_dict=entity_dict)
                                       for entity_dict in response.json()])
        else:
            self.logger.exception('Platform error getting projects')
            raise self.client_api.platform_exception
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
                project = entities.Project(entity_dict=response.json())
            else:
                self.logger.exception('Platform error getting project. id: %s', project_id)
                raise self.client_api.platform_exception
        elif project_name is not None:
            projects = self.list()
            project = [project for project in projects if project.name == project_name]
            if not project:
                # list is empty
                self.logger.info('Project not found. project_name: %s', project_name)
                project = None
            elif len(project) > 1:
                # more than one matching project
                self.logger.exception('More than one project with same name. Please "get" by id')
                raise ValueError('More than one project with same name. Please "get" by id')
            else:
                project = project[0]
        else:
            self.logger.exception('Must choose by at least one. "project_id" or "project_name"')
            raise ValueError('Must choose by at least one. "project_id" or "project_name"')
        return project

    def delete(self, project_name=None, project_id=None):
        """
        Delete a project forever!
        :param project_name: optional - search by name
        :param project_id: optional - search by id
        :return:
        """
        project = self.get(project_name=project_name, project_id=project_id)
        success = self.client_api.gen_request(req_type='delete',
                                              path='/projects/%s' % project.id)
        if not success:
            self.logger.exception('Platform error deleting a project')
            raise self.client_api.platform_exception
        return True

    def edit(self):
        """
        Edit a project
        :return:
        """

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
            project = entities.Project(entity_dict=response.json())
        else:
            self.logger.exception('Platform error creating a project')
            raise self.client_api.platform_exception
        return project
