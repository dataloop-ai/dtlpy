import logging
from urllib.parse import quote
import jwt

from .. import entities, miscellaneous, exceptions, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Projects:
    """
    Projects Repository

    The Projects class allows the user to manage projects and their properties.

    For more information on Projects see the `Dataloop documentation <https://dataloop.ai/docs/project#>`_.
    """

    def __init__(self, client_api: ApiClient, org=None):
        self._client_api = client_api
        self._org = org

    def __get_from_cache(self) -> entities.Project:
        project = self._client_api.state_io.get('project')
        if project is not None:
            project = entities.Project.from_json(_json=project, client_api=self._client_api)
        return project

    def __get_by_id(self, project_id: str, log_error: bool) -> entities.Project:
        """
        :param project_id:
        """
        success, response = self._client_api.gen_request(
            req_type='get',
            path='/projects/{}'.format(project_id),
            log_error=log_error
        )

        try:
            response_json = response.json()
        except Exception:
            try:
                logger.exception('Failed to parse response content: {}'.format(response.text))
            except Exception:
                logger.exception('Failed to print response content')
            raise

        if success:
            project = entities.Project.from_json(
                client_api=self._client_api,
                _json=response_json
            )
        else:
            # raise PlatformException(response)
            # TODO because of a bug in gate wrong error is returned so for now manually raise not found
            raise exceptions.PlatformException(error="404", message="Project not found")
        return project

    def __get_by_name(self, project_name: str):
        """
        :param project_name:
        """
        project_name = quote(project_name.encode("utf-8"))
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/name'.format(project_name))
        if success:
            projects = [entities.Project.from_json(client_api=self._client_api,
                                                   _json=project_json) for project_json in response.json()]
        else:
            # TODO because of a bug in gate wrong error is returned so for now manually raise not found
            raise exceptions.PlatformException(error="404", message="Project not found")
        return projects

    def __get_by_identifier(self, identifier=None) -> entities.Project:
        """
        :param identifier:
        """
        projects = self.list()
        projects_by_name = [project for project in projects if identifier in project.id or identifier in project.name]
        if len(projects_by_name) == 1:
            return projects_by_name[0]
        elif len(projects_by_name) > 1:
            raise Exception('Multiple projects with this name/identifier exist')
        else:
            raise Exception("Project not found")

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects")

    def open_in_web(self,
                    project_name: str = None,
                    project_id: str = None,
                    project: entities.Project = None):
        """
        Open the project in our web platform.

        **Prerequisites**: All users can open a project in the web.

        :param str project_name: The Name of the project
        :param str project_id: The Id of the project
        :param dtlpy.entities.project.Project project: project object

        **Example**:

        .. code-block:: python

            dl.projects.open_in_web(project_id='project_id')
        """
        if project_name is not None:
            project = self.get(project_name=project_name)
        if project is not None:
            project.open_in_web()
        elif project_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(project_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def checkout(self,
                 identifier: str = None,
                 project_name: str = None,
                 project_id: str = None,
                 project: entities.Project = None):
        """
        Checkout (switch) to a project to work on.

        **Prerequisites**: All users can open a project in the web.

        You must provide at least ONE of the following params: project_id, project_name.

        :param str identifier: project name or partial id that you wish to switch
        :param str project_name: The Name of the project
        :param str project_id: The Id of the project
        :param dtlpy.entities.project.Project project: project object

        **Example**:

        .. code-block:: python

            dl.projects.checkout(project_id='project_id')
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
        if project_id:
            url = '/projects/{}/mail'.format(project_id)
        else:
            url = '/outbox'
        assert isinstance(title, str)
        assert isinstance(content, str)
        if self._client_api.token is not None:
            sender = jwt.decode(self._client_api.token, algorithms=['HS256'],
                                verify=False, options={'verify_signature': False})['email']
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

    @_api_reference.add(path='/projects/{projectId}/members/{userId}', method='post')
    def add_member(self, email: str, project_id: str, role: entities.MemberRole = entities.MemberRole.DEVELOPER):
        """
        Add a member to the project.

        **Prerequisites**: You must be in the role of an *owner* to add a member to a project.

        :param str email: member email
        :param str project_id: The Id of the project
        :param role: The required role for the user. Use the enum dl.MemberRole
        :return: dict that represent the user
        :rtype: dict

        **Example**:

        .. code-block:: python

            user_json = dl.projects.add_member(project_id='project_id', email='user@dataloop.ai', role=dl.MemberRole.DEVELOPER)
        """
        url_path = '/projects/{}/members/{}'.format(project_id, email)
        payload = dict(role=role)

        if role not in list(entities.MemberRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(list(entities.MemberRole))))

        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    @_api_reference.add(path='/projects/{projectId}/members/{userId}', method='patch')
    def update_member(self, email: str, project_id: str, role: entities.MemberRole = entities.MemberRole.DEVELOPER):
        """
        Update member's information/details in the project.

        **Prerequisites**: You must be in the role of an *owner* to update a member.

        :param str email: member email
        :param str project_id: The Id of the project
        :param role: The required role for the user. Use the enum dl.MemberRole
        :return: dict that represent the user
        :rtype: dict

        **Example**:

        .. code-block:: python

            user_json = = dl.projects.update_member(project_id='project_id', email='user@dataloop.ai', role=dl.MemberRole.DEVELOPER)
        """
        url_path = '/projects/{}/members/{}'.format(project_id, email)
        payload = dict(role=role)

        if role not in list(entities.MemberRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(list(entities.MemberRole))))

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    @_api_reference.add(path='/projects/{projectId}/members/{userId}', method='delete')
    def remove_member(self, email: str, project_id: str):
        """
        Remove a member from the project.

        **Prerequisites**: You must be in the role of an *owner* to delete a member from a project.

        :param str email: member email
        :param str project_id: The Id of the project
        :return: dict that represents the user
        :rtype: dict

        **Example**:

        .. code-block:: python

            user_json = dl.projects.remove_member(project_id='project_id', email='user@dataloop.ai')
        """
        url_path = '/projects/{}/members/{}'.format(project_id, email)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()

    @_api_reference.add(path='/projects/{projectId}/members', method='get')
    def list_members(self, project: entities.Project, role: entities.MemberRole = None):
        """
        Get a list of the project members.

        **Prerequisites**: You must be in the role of an *owner* to list project members.

        :param dtlpy.entities.project.Project project: Project object
        :param role: The required role for the user. Use the enum dl.MemberRole
        :return: list of the project members
        :rtype: list

        **Example**:

        .. code-block:: python

            users_jsons_list = dl.projects.list_members(project_id='project_id', role=dl.MemberRole.DEVELOPER)
        """
        url_path = '/projects/{}/members'.format(project.id)

        if role is not None and role not in list(entities.MemberRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(list(entities.MemberRole))))

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

    @_api_reference.add(path='/projects', method='get')
    def list(self) -> miscellaneous.List[entities.Project]:
        """
        Get the user's project list

        **Prerequisites**: You must be a **superuser** to list all users' projects.

        :return: List of Project objects

        **Example**:

        .. code-block:: python

            projects = dl.projects.list()
        """
        if self._org is None:
            url_path = '/projects'
        else:
            url_path = '/orgs/{}/projects'.format(self._org.id)
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)

        if success:
            pool = self._client_api.thread_pools(pool_name='entity.create')
            projects_json = response.json()
            jobs = [None for _ in range(len(projects_json))]
            # return triggers list
            for i_project, project in enumerate(projects_json):
                jobs[i_project] = pool.submit(entities.Project._protected_from_json,
                                              **{'client_api': self._client_api,
                                                 '_json': project})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            projects = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.error('Platform error getting projects')
            raise exceptions.PlatformException(response)
        return projects

    @_api_reference.add(path='/projects/{projectId}', method='get')
    def get(self,
            project_name: str = None,
            project_id: str = None,
            checkout: bool = False,
            fetch: bool = None,
            log_error=True) -> entities.Project:
        """
        Get a Project object.

        **Prerequisites**: You must be in the role of an *owner* to get a project object.

        You must check out to a project or provide at least one of the following params: project_id, project_name

        :param str project_name: optional - search by name
        :param str project_id: optional - search by id
        :param bool checkout: set the project as a default project object (cookies)
        :param bool fetch: optional - fetch entity from platform (True), default taken from cookie
        :param bool log_error: optional - show the logs errors
        :return: Project object
        :rtype: dtlpy.entities.project.Project

        **Example**:

        .. code-block:: python

            project = dl.projects.get(project_id='project_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if project_id is None and project_name is None:
            project = self.__get_from_cache()
            if project is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Project was found. You must checkout to a project or provide an identifier in inputs')
        elif fetch:
            if project_id is not None:
                if not isinstance(project_id, str):
                    raise exceptions.PlatformException(
                        error='400',
                        message='project_id must be strings')

                project = self.__get_by_id(project_id, log_error=log_error)
                # verify input project name is same as the given id
                if project_name is not None and project.name != project_name:
                    logger.warning(
                        "Mismatch found in projects.get: project_name is different then project.name:"
                        " {!r} != {!r}".format(
                            project_name,
                            project.name))
            elif project_name is not None:
                if not isinstance(project_name, str):
                    raise exceptions.PlatformException(
                        error='400',
                        message='project_name must be strings')

                projects = self.__get_by_name(project_name)
                if len(projects) > 1:
                    # more than one matching project
                    raise exceptions.PlatformException(
                        error='404',
                        message='More than one project with same name. Please "get" by id')
                else:
                    project = projects[0]
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

    @_api_reference.add(path='/projects/{projectId}', method='delete')
    def delete(self,
               project_name: str = None,
               project_id: str = None,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete a project forever!

        **Prerequisites**: You must be in the role of an *owner* to delete a project.

        :param str project_name: optional - search by name
        :param str project_id: optional - search by id
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: True if success, error if not
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = dl.projects.delete(project_id='project_id', sure=True, really=True)
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

    @_api_reference.add(path='/projects/{projectId}', method='patch')
    def update(self,
               project: entities.Project,
               system_metadata: bool = False) -> entities.Project:
        """
        Update a project information (e.g., name, member roles, etc.).

        **Prerequisites**: You must be in the role of an *owner* to add a member to a project.

        :param dtlpy.entities.project.Project project: project object
        :param bool system_metadata: optional - True, if you want to change metadata system
        :return: Project object
        :rtype: dtlpy.entities.project.Project

        **Example**:

        .. code-block:: python

            project = dl.projects.delete(project='project_entity')
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

    @_api_reference.add(path='/projects', method='post')
    def create(self,
               project_name: str,
               checkout: bool = False) -> entities.Project:
        """
        Create a new project.

        **Prerequisites**: Any user can create a project.

        :param str project_name: The Name of the project
        :param bool checkout: set the project as a default project object (cookies)
        :return: Project object
        :rtype: dtlpy.entities.project.Project

        **Example**:

        .. code-block:: python

            project = dl.projects.create(project_name='project_name')
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
