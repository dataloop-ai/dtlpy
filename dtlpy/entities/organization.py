from collections import namedtuple
from enum import Enum
import traceback
import logging
import attr

from .. import repositories, entities
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class PodType(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    HIGH = "high"


class CacheAction(str, Enum):
    APPLY = "apply"
    DESTROY = "destroy"


class OrganizationsPlans(str, Enum):
    PREMIUM = "premium"
    FREEMIUM = "freemium"


class MemberOrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    WORKER = "worker"


@attr.s()
class Organization(entities.BaseEntity):
    """
    Organization entity
    """

    members = attr.ib(type=list)
    groups = attr.ib(type=list)
    account = attr.ib(type=dict)
    created_at = attr.ib()
    updated_at = attr.ib()
    id = attr.ib(repr=False)
    name = attr.ib(repr=False)
    logo_url = attr.ib(repr=False)
    plan = attr.ib(repr=False)
    owner = attr.ib(repr=False)
    creator = attr.ib(repr=False)

    # api
    _client_api = attr.ib(type=ApiClient, repr=False)

    # repositories
    _repositories = attr.ib(repr=False)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def createdBy(self):
        return self.creator

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['organizations', 'projects', 'integrations', 'services', 'settings'])

        r = reps(projects=repositories.Projects(client_api=self._client_api, org=self),
                 organizations=repositories.Organizations(client_api=self._client_api),
                 integrations=repositories.Integrations(client_api=self._client_api, org=self),
                 services=repositories.Services(client_api=self._client_api),
                 settings=repositories.Settings(client_api=self._client_api,
                                                org=self,
                                                resource=self,
                                                resource_type=entities.PlatformEntityType.ORG)
                 )
        return r

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("iam/{}/members".format(self.id))

    @property
    def accounts(self):
        return [self.account]

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def settings(self):
        assert isinstance(self._repositories.settings, repositories.Settings)
        return self._repositories.settings

    @property
    def organizations(self):
        assert isinstance(self._repositories.organizations, repositories.Organizations)
        return self._repositories.organizations

    @property
    def integrations(self):
        assert isinstance(self._repositories.integrations, repositories.Integrations)
        return self._repositories.integrations

    @staticmethod
    def _protected_from_json(_json, client_api):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity

        :return: update status: bool, Organization entity
        """
        try:
            organization = Organization.from_json(_json=_json,
                                                  client_api=client_api)
            status = True
        except Exception:
            organization = traceback.format_exc()
            status = False
        return status, organization

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Project entity object from a json

        :param bool is_fetched: is Entity fetched from Platform
        :param dict _json: _json response from host
        :param dl.ApiClient client_api: ApiClient entity
        :return: Organization object
        :rtype: dtlpy.entities.organization.Organization
        """
        inst = cls(members=_json.get('members', None),
                   groups=_json.get('groups', None),
                   account=_json.get('account', None),
                   created_at=_json.get('createdAt', None),
                   updated_at=_json.get('updatedAt', None),
                   id=_json.get('id', None),
                   name=_json.get('name', None),
                   logo_url=_json.get('logoUrl', None),
                   plan=_json.get('plan', None),
                   owner=_json.get('owner', None),
                   creator=_json.get('creator', None),
                   client_api=client_api)
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        output_dict = attr.asdict(self,
                                  filter=attr.filters.exclude(attr.fields(Organization)._client_api,
                                                              attr.fields(Organization)._repositories,
                                                              attr.fields(Organization).created_at,
                                                              attr.fields(Organization).updated_at,
                                                              attr.fields(Organization).creator,
                                                              ))
        output_dict['members'] = self.members
        output_dict['groups'] = self.groups
        output_dict['account'] = self.account
        output_dict['accounts'] = self.accounts
        output_dict['createdAt'] = self.created_at
        output_dict['updatedAt'] = self.updated_at
        output_dict['id'] = self.id
        output_dict['name'] = self.name
        output_dict['logo_url'] = self.logo_url
        output_dict['plan'] = self.plan
        output_dict['owner'] = self.owner
        output_dict['creator'] = self.creator

        return output_dict

    def list_groups(self):
        """
        List all organization groups (groups that were created within the organization).

        Prerequisites: You must be an organization "owner" to use this method.

        :return: groups list
        :rtype: list

        """
        return self.organizations.list_groups(organization=self)

    def list_members(self, role: MemberOrgRole = None):
        """
        List all organization members.

        Prerequisites: You must be an organization "owner" to use this method.

        :param str role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :return: projects list
        :rtype: list
        """
        return self.organizations.list_members(organization=self, role=role)

    def update(self, plan: str):
        """
        Update Organization.

        Prerequisities: You must be an Organization **superuser** to update an organization.

        :param str plan: OrganizationsPlans.FREEMIUM, OrganizationsPlans.PREMIUM

        :return: organization object
        """
        return self.organizations.update(organization=self, plan=plan)

    def add_member(self, email, role: MemberOrgRole = MemberOrgRole):
        """
        Add members to your organization. Read about members and groups [here](https://dataloop.ai/docs/org-members-groups).

        Prerequisities: To add members to an organization, you must be in the role of an "owner" in that organization.

        :param str email: the member's email
        :param str role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :return: True if successful or error if unsuccessful
        :rtype: bool
        """
        return self.organizations.add_member(organization=self, email=email, role=role)

    def delete_member(self, user_id: str, sure: bool = False, really: bool = False):
        """
        Delete member from the Organization.

        Prerequisites: Must be an organization "owner" to delete members.

        :param str user_id: user id
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: True if success and error if not
        :rtype: bool
        """
        return self.organizations.delete_member(organization=self, user_id=user_id, sure=sure, really=really)

    def update_member(self, email: str, role: MemberOrgRole = MemberOrgRole.MEMBER):
        """
        Update member role.

        Prerequisities: You must be an organization "owner" to update a member's role.

        :param str email: the member's email
        :param str role: MemberOrgRole.ADMIN, MemberOrgRole.OWNER, MemberOrgRole.MEMBER, MemberOrgRole.WORKER
        :return: json of the member fields
        :rtype: dict
        """
        return self.organizations.update_member(organization=self, email=email, role=role)

    def open_in_web(self):
        """
        Open the organizations in web platform

        """
        self._client_api._open_in_web(url=self.platform_url)

    def cache_action(self, mode=CacheAction.APPLY, pod_type=PodType.SMALL):
        """
        Open the organizations in web platform

        :param str mode: dl.CacheAction.APPLY or dl.CacheAction.DESTROY
        :param dl.PodType pod_type:  dl.PodType.SMALL, dl.PodType.MEDIUM, dl.PodType.HIGH
        :return: True if success
        :rtype: bool
        """
        return self.services._cache_action(organization=self, mode=mode, pod_type=pod_type)
