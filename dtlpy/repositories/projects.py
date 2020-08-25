import logging

import jwt

from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Projects:
    """
    Projects repository
    """

    def __init__(self, client_api: services.ApiClient):
        self._client_api = client_api

    def __get_from_cache(self) -> entities.Project:
        project = self._client_api.state_io.get('project')
        if project is not None:
            project = entities.Project.from_json(_json=project, client_api=self._client_api)
        return project

    def __get_by_id(self, project_id: str) -> entities.Project:
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}'.format(project_id))
        if success:
            project = entities.Project.from_json(client_api=self._client_api,
                                                 _json=response.json())
        else:
            # raise PlatformException(response)
            # TODO because of a bug in gate wrong error is returned so for now manually raise not found
            raise exceptions.PlatformException(error="404", message="Project not found")
        return project

    def __get_by_identifier(self, identifier=None) -> entities.Project:
        projects = self.list()
        projects_by_name = [project for project in projects if identifier in project.id or identifier in project.name]
        if len(projects_by_name) == 1:
            return projects_by_name[0]
        elif len(projects_by_name) > 1:
            raise Exception('Multiple projects with this name/identifier exist')
        else:
            raise Exception("Project not found")

    def open_in_web(self, project_name: str = None, project_id: str = None, project: entities.Project = None):
        if project_id is None:
            if project is not None:
                project_id = project.id
            elif project_name is not None:
                project_id = self.get(project_name=project_name)
            else:
                raise exceptions.PlatformException('400', 'Please provide project, project name or project id')
        self._client_api._open_in_web(resource_type='project', project_id=project_id)

    def checkout(self,
                 identifier: str = None,
                 project_name: str = None,
                 project_id: str = None,
                 project: entities.Project = None):
        """
        Check-out a project
        :param project:
        :param project_id:
        :param project_name:
        :param identifier: project name or partial id
        :return:
        """
        if project is None:
            if project_id is not None or project_name is not None:
                project = self.get(project_id=project_id, project_name=project_name)
            elif identifier is not None:
                project = self.__get_by_identifier(identifier=identifier)
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Must provide partial/full id/name to checkout')
        self._client_api.state_io.put('project', project.to_json())
        logger.info('Checked out to project {}'.format(project.name))

    def _send_mail(self, project_id: str, send_to: str, title: str, content: str) -> bool:
        url = '/projects/{}/mail'.format(project_id)
        assert isinstance(title, str)
        assert isinstance(content, str)
        if self._client_api.token is not None:
            sender = jwt.decode(self._client_api.token, algorithms=['HS256'], verify=False)['email']
        else:
            raise exceptions.PlatformException('600', 'Token expired please log in')

        payload = {
            'to': send_to,
            'from': sender,
            'subject': title,
            'body': content
        }

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url,
                                                         json_req=payload)

        if not success:
            raise exceptions.PlatformException(response)
        return True

    def add_member(self, email: str, project_id: str, role: str = 'engineer'):
        url_path = '/projects/{}/members/{}'.format(project_id, email)
        payload = dict(role=role)
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    def list_members(self, project: entities.Project, role: str = None):
        url_path = '/projects/{}/members'.format(project.id)
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        members = miscellaneous.List(
            [entities.User.from_json(_json=user, client_api=self._client_api, project=project) for user in
             response.json()])

        if role is not None:
            members = [member for member in members if member.role == role]

        return members

    def list(self) -> miscellaneous.List[entities.Project]:
        """
        Get users project's list.
        :return: List of Project objects
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects')

        if success:
            pool = self._client_api.thread_pools(pool_name='entity.create')
            projects_json = response.json()
            jobs = [None for _ in range(len(projects_json))]
            # return triggers list
            for i_project, project in enumerate(projects_json):
                jobs[i_project] = pool.apply_async(entities.Project._protected_from_json,
                                                   kwds={'client_api': self._client_api,
                                                         '_json': project})
            # wait for all jobs
            _ = [j.wait() for j in jobs]
            # get all results
            results = [j.get() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            projects = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.error('Platform error getting projects')
            raise exceptions.PlatformException(response)
        return projects

    def get(self,
            project_name: str = None,
            project_id: str = None,
            checkout: bool = False,
            fetch: bool = None) -> entities.Project:
        """
        Get a Project object
        :param checkout:
        :param project_name: optional - search by name
        :param project_id: optional - search by id
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Project object

        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if project_id is None and project_name is None:
            project = self.__get_from_cache()
            if project is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Project was found, must checkout or provide an identifier in inputs')
        elif fetch:
            if project_id is not None:
                project = self.__get_by_id(project_id)
            elif project_name is not None:
                projects = self.list()
                project = [project for project in projects if project.name == project_name]
                if not project:
                    # list is empty
                    raise exceptions.PlatformException(error='404',
                                                       message='Project not found. Name: {}'.format(project_name))
                    # project = None
                elif len(project) > 1:
                    # more than one matching project
                    raise exceptions.PlatformException(
                        error='404',
                        message='More than one project with same name. Please "get" by id')
                else:
                    project = project[0]
            else:
                raise exceptions.PlatformException(
                    error='404',
                    message='No input and no checked-out found')
        else:
            project = entities.Project.from_json(_json={'id': project_id,
                                                        'name': project_name},
                                                 client_api=self._client_api,
                                                 is_fetched=False)
        assert isinstance(project, entities.Project)
        if checkout:
            self.checkout(project=project)
        return project

    def delete(self,
               project_name: str = None,
               project_id: str = None,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete a project forever!
        :param project_name: optional - search by name
        :param project_id: optional - search by id
        :param sure: are you sure you want to delete?
        :param really: really really?

        :return: True
        """
        if sure and really:
            if project_id is None:
                project = self.get(project_name=project_name)
                project_id = project.id
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/projects/{}'.format(project_id))
            if not success:
                raise exceptions.PlatformException(response)
            logger.info('Project id {} deleted successfully'.format(project_id))
            return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete project from SDK. Please login to platform to delete')

    def update(self,
               project: entities.Project,
               system_metadata: bool = False) -> entities.Project:
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
            raise exceptions.PlatformException(response)

    def create(self,
               project_name: str,
               checkout: bool = False) -> entities.Project:
        """
        Create a new project
        :param checkout:
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
            raise exceptions.PlatformException(response)
        assert isinstance(project, entities.Project)
        if checkout:
            self.checkout(project=project)
        return project
