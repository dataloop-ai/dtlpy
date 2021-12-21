import logging
from enum import Enum

from .. import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name=__name__)


class Organizations:
    """
    organizations repository
    """

    def __init__(self, client_api: services.ApiClient):
        self._client_api = client_api

    def create(self, organization_json) -> entities.Organization:
        """
        Create a new pipeline
        :param organization_json: json contain the Organization fields
        :return: Pipeline object
        """

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/orgs',
                                                         json_req=organization_json)
        if success:
            organization = entities.Organization.from_json(client_api=self._client_api,
                                                           _json=response.json())
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(organization, entities.Organization)
        return organization

    def list_groups(self, organization: entities.Organization = None,
                    organization_id: str = None,
                    organization_name: str = None):
        """
        list all organization groups
        :param organization:
        :param organization_id:
        :param organization_name:
        :return groups list:
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/groups'.format(organization.id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        groups = miscellaneous.List(response.json())
        return groups

    def list_integrations(self, organization: entities.Organization = None,
                          organization_id: str = None,
                          organization_name: str = None,
                          only_available=False):
        """
        list all organization integrations
        :param organization:
        :param organization_id:
        :param organization_name:
        :param only_available: bool - if True list only the available integrations
        :return groups list:
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if only_available:
            url_path = '/orgs/{}/availableIntegrations'.format(organization.id)
        else:
            url_path = '/orgs/{}/integrations'.format(organization.id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        available_integrations = miscellaneous.List(response.json())
        return available_integrations

    def list_members(self, organization: entities.Organization = None,
                     organization_id: str = None,
                     organization_name: str = None,
                     role: entities.MemberOrgRole = None):
        """
        list all organization members
        :param organization:
        :param organization_id:
        :param organization_name:
        :param role: MemberOrgRole.ADMIN ,MemberOrgRole.OWNER ,MemberOrgRole.MEMBER
        :return projects list:
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/members'.format(organization.id)

        if role is not None and role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)
        if not success:
            raise exceptions.PlatformException(response)

        members = miscellaneous.List(
            [entities.User.from_json(_json=user, client_api=self._client_api, project=None) for user in
             response.json()])

        if role is not None:
            members = [member for member in members if member.role == role]

        return members

    def list(self) -> miscellaneous.List[entities.Organization]:
        """
        Get Organization's list.
        :return: List of Organization objects
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/orgs')

        if success:
            pool = self._client_api.thread_pools(pool_name='entity.create')
            organization_json = response.json()
            jobs = [None for _ in range(len(organization_json))]
            # return triggers list
            for i_organization, organization in enumerate(organization_json):
                jobs[i_organization] = pool.submit(entities.Organization._protected_from_json,
                                                   **{'client_api': self._client_api,
                                                      '_json': organization})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            organization = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            logger.error('Platform error getting organization')
            raise exceptions.PlatformException(response)
        return organization

    def get(self,
            organization_id: str = None,
            organization_name: str = None,
            fetch: bool = None) -> entities.Organization:
        """
        Get a Organization object
        :param organization_id: optional - search by id
        :param organization_name: optional - search by name
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: Organization object

        """
        if organization_name is None and organization_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if fetch is None:
            fetch = self._client_api.fetch_entities

        if fetch:
            if organization_id is not None:
                success, response = self._client_api.gen_request(req_type='get',
                                                                 path='/orgs/{}'.format(organization_id))
                if not success:
                    raise exceptions.PlatformException(response)
                organization = entities.Organization.from_json(
                    client_api=self._client_api,
                    _json=response.json()
                )
            else:
                organizations = self.list()
                organization = [organization for organization in organizations if
                                organization.name == organization_name]
                if not organization:
                    # list is empty
                    raise exceptions.PlatformException(error='404',
                                                       message='organization not found. Name: {}'.format(
                                                           organization_name))
                    # project = None
                elif len(organization) > 1:
                    # more than one matching project
                    raise exceptions.PlatformException(
                        error='404',
                        message='More than one project with same name. Please "get" by id')
                else:
                    organization = organization[0]
        else:
            organization = entities.Organization.from_json(
                _json={'id': organization_id,
                       'name': organization_name},
                client_api=self._client_api)

        return organization

    def update(self, plan: str,
               organization: entities.Organization = None,
               organization_id: str = None,
               organization_name: str = None) -> entities.Organization:
        """
        Update a organization
        :param plan: OrganizationsPlans.FREEMIUM, OrganizationsPlans.PREMIUM
        :param organization:
        :param organization_id:
        :param organization_name:
        :return: organization object
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if plan not in list(entities.OrganizationsPlans):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(plan,
                                                                                 ', '.join(list(
                                                                                     entities.OrganizationsPlans))))
        payload = {'plan': plan}
        url_path = '/orgs/{}/plan'.format(organization.id)
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if success:
            return organization
        else:
            raise exceptions.PlatformException(response)

    def add_member(self, email,
                   role: entities.MemberOrgRole = entities.MemberOrgRole.MEMBER,
                   organization_id: str = None,
                   organization_name: str = None,
                   organization: entities.Organization = None):
        """
        Add member to the Organization
        :param email:
        :param role: MemberOrgRole.ADMIN ,MemberOrgRole.OWNER ,MemberOrgRole.MEMBER
        :param organization_id:
        :param organization_name:
        :param organization:
        :return: True
        """

        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        if not isinstance(email, list):
            email = [email]

        if role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        url_path = '/orgs/{}/members'.format(organization.id)
        payload = {"emails": email, 'role': role}
        success, response = self._client_api.gen_request(req_type='post',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        else:
            return True

    def delete_member(self, user_id: str,
                      organization_id: str = None,
                      organization_name: str = None,
                      organization: entities.Organization = None,
                      sure: bool = False,
                      really: bool = False) -> bool:
        """
        delete member from the Organization
        :param user_id:
        :param organization_id:
        :param organization_name:
        :param organization:
        :param sure: are you sure you want to delete?
        :param really: really really?
        :return: True
        """
        if sure and really:
            if organization is None and organization_id is None and organization_name is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Must provide an identifier in inputs')

            if organization is None:
                organization = self.get(organization_id=organization_id, organization_name=organization_name)

            url_path = '/orgs/{}/members/{}'.format(organization.id, user_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path=url_path)
            if not success:
                raise exceptions.PlatformException(response)
            else:
                return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete member from SDK. Please login to platform to delete')

    def update_member(self, email: str,
                      role: entities.MemberOrgRole = entities.MemberOrgRole.MEMBER,
                      organization_id: str = None,
                      organization_name: str = None,
                      organization: entities.Organization = None):
        """
        Update the member role
        :param email:
        :param role: MemberOrgRole.ADMIN ,MemberOrgRole.OWNER ,MemberOrgRole.MEMBER
        :param organization_id:
        :param organization_name:
        :param organization:
        """
        if organization is None and organization_id is None and organization_name is None:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        if organization is None:
            organization = self.get(organization_id=organization_id, organization_name=organization_name)

        url_path = '/orgs/{}/members'.format(organization.id)
        payload = dict(role=role, email=email)

        if role not in list(entities.MemberOrgRole):
            raise ValueError('Unknown role {!r}, role must be one of: {}'.format(role,
                                                                                 ', '.join(
                                                                                     list(entities.MemberOrgRole))))

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()
