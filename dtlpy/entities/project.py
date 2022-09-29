from collections import namedtuple
from enum import Enum
import traceback
import logging
import attr

from .. import repositories, miscellaneous, services, entities

logger = logging.getLogger(name='dtlpy')


class MemberRole(str, Enum):
    OWNER = "owner"
    DEVELOPER = "engineer"
    ANNOTATOR = "annotator"
    ANNOTATION_MANAGER = "annotationManager"


@attr.s()
class Project(entities.BaseEntity):
    """
    Project entity
    """

    _contributors = attr.ib(repr=False)
    created_at = attr.ib()
    creator = attr.ib()
    id = attr.ib()
    name = attr.ib()
    org = attr.ib(repr=False)
    updated_at = attr.ib(repr=False)
    role = attr.ib(repr=False)
    account = attr.ib(repr=False)
    is_blocked = attr.ib(repr=False)

    # name change
    feature_constraints = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)

    # repositories
    _repositories = attr.ib(repr=False)

    @property
    def isBlocked(self):
        return self.is_blocked

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple(
            'repositories',
            'projects triggers datasets items recipes packages codebases artifacts times_series services '
            'executions assignments tasks bots webhooks models analytics ontologies '
            'drivers pipelines feature_sets features integrations settings'
        )
        datasets = repositories.Datasets(client_api=self._client_api, project=self)
        return reps(
            projects=repositories.Projects(client_api=self._client_api),
            webhooks=repositories.Webhooks(client_api=self._client_api, project=self),
            items=repositories.Items(client_api=self._client_api, datasets=datasets, project=self),
            recipes=repositories.Recipes(client_api=self._client_api, project=self, project_id=self.id),
            datasets=datasets,
            executions=repositories.Executions(client_api=self._client_api, project=self),
            triggers=repositories.Triggers(client_api=self._client_api, project=self),
            packages=repositories.Packages(project=self, client_api=self._client_api),
            models=repositories.Models(project=self, client_api=self._client_api),
            codebases=repositories.Codebases(project=self, client_api=self._client_api),
            artifacts=repositories.Artifacts(project=self, client_api=self._client_api),
            times_series=repositories.TimesSeries(project=self, client_api=self._client_api),
            services=repositories.Services(client_api=self._client_api, project=self),
            assignments=repositories.Assignments(project=self, client_api=self._client_api),
            tasks=repositories.Tasks(client_api=self._client_api, project=self),
            bots=repositories.Bots(client_api=self._client_api, project=self),
            analytics=repositories.Analytics(client_api=self._client_api, project=self),
            ontologies=repositories.Ontologies(client_api=self._client_api, project=self),
            drivers=repositories.Drivers(client_api=self._client_api, project=self),
            pipelines=repositories.Pipelines(client_api=self._client_api, project=self),
            feature_sets=repositories.FeatureSets(client_api=self._client_api, project=self),
            features=repositories.Features(client_api=self._client_api, project=self),
            integrations=repositories.Integrations(client_api=self._client_api, project=self),
            settings=repositories.Settings(client_api=self._client_api,
                                           project=self,
                                           resource=self,
                                           resource_type=entities.PlatformEntityType.PROJECT)
        )

    @property
    def drivers(self):
        assert isinstance(self._repositories.drivers, repositories.Drivers)
        return self._repositories.drivers

    @property
    def integrations(self):
        assert isinstance(self._repositories.integrations, repositories.Integrations)
        return self._repositories.integrations

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}".format(self.id))

    @property
    def triggers(self):
        assert isinstance(self._repositories.triggers, repositories.Triggers)
        return self._repositories.triggers

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

    @property
    def recipes(self):
        assert isinstance(self._repositories.recipes, repositories.Recipes)
        return self._repositories.recipes

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def executions(self):
        assert isinstance(self._repositories.executions, repositories.Executions)
        return self._repositories.executions

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def pipelines(self):
        assert isinstance(self._repositories.pipelines, repositories.Pipelines)
        return self._repositories.pipelines

    @property
    def packages(self):
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    @property
    def codebases(self):
        assert isinstance(self._repositories.codebases, repositories.Codebases)
        return self._repositories.codebases

    @property
    def webhooks(self):
        assert isinstance(self._repositories.webhooks, repositories.Webhooks)
        return self._repositories.webhooks

    @property
    def artifacts(self):
        assert isinstance(self._repositories.artifacts, repositories.Artifacts)
        return self._repositories.artifacts

    @property
    def times_series(self):
        assert isinstance(self._repositories.times_series, repositories.TimesSeries)
        return self._repositories.times_series

    @property
    def assignments(self):
        assert isinstance(self._repositories.assignments, repositories.Assignments)
        return self._repositories.assignments

    @property
    def tasks(self):
        assert isinstance(self._repositories.tasks, repositories.Tasks)
        return self._repositories.tasks

    @property
    def bots(self):
        assert isinstance(self._repositories.bots, repositories.Bots)
        return self._repositories.bots

    @property
    def analytics(self):
        assert isinstance(self._repositories.analytics, repositories.Analytics)
        return self._repositories.analytics

    @property
    def feature_sets(self):
        assert isinstance(self._repositories.feature_sets, repositories.FeatureSets)
        return self._repositories.feature_sets

    @property
    def features(self):
        assert isinstance(self._repositories.features, repositories.Features)
        return self._repositories.features

    @property
    def settings(self):
        assert isinstance(self._repositories.settings, repositories.Settings)
        return self._repositories.settings

    @property
    def contributors(self):
        return miscellaneous.List([entities.User.from_json(_json=_json,
                                                           client_api=self._client_api,
                                                           project=self) for _json in self._contributors])

    @staticmethod
    def _protected_from_json(_json, client_api):
        """
        Same as from_json but with try-except to catch if error

        :param dict _json: platform json
        :param dl.ApiClient client_api: ApiClient entity
        :return:
        """
        try:
            project = Project.from_json(_json=_json,
                                        client_api=client_api)
            status = True
        except Exception:
            project = traceback.format_exc()
            status = False
        return status, project

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Project entity object from a json

        :param bool is_fetched: is Entity fetched from Platform
        :param dict _json: _json response from host
        :param dl.ApiClient client_api: ApiClient entity
        :return: Project object
        :rtype: dtlpy.entities.project.Project
        """
        inst = cls(feature_constraints=_json.get('featureConstraints', None),
                   contributors=_json.get('contributors', None),
                   is_blocked=_json.get('isBlocked', None),
                   created_at=_json.get('createdAt', None),
                   updated_at=_json.get('updatedAt', None),
                   creator=_json.get('creator', None),
                   account=_json.get('account', None),
                   name=_json.get('name', None),
                   role=_json.get('role', None),
                   org=_json.get('org', None),
                   id=_json.get('id', None),
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
                                  filter=attr.filters.exclude(attr.fields(Project)._client_api,
                                                              attr.fields(Project)._repositories,
                                                              attr.fields(Project).feature_constraints,
                                                              attr.fields(Project)._contributors,
                                                              attr.fields(Project).created_at,
                                                              attr.fields(Project).updated_at,
                                                              attr.fields(Project).is_blocked,
                                                              ))
        output_dict['contributors'] = self._contributors
        output_dict['featureConstraints'] = self.feature_constraints
        output_dict['createdAt'] = self.created_at
        output_dict['updatedAt'] = self.updated_at
        output_dict['isBlocked'] = self.is_blocked

        return output_dict

    def delete(self, sure=False, really=False):
        """
        Delete the project forever!

        :param bool sure: are you sure you want to delete?
        :param bool really: really really?
        :return: True
        :rtype: bool
        """
        return self.projects.delete(project_id=self.id,
                                    sure=sure,
                                    really=really)

    def update(self, system_metadata=False):
        """
        Update the project

        :param bool system_metadata: to update system metadata
        :return: Project object
        :rtype: dtlpy.entities.project.Project
        """
        return self.projects.update(project=self, system_metadata=system_metadata)

    def checkout(self):
        """
        Checkout the project

        """
        self.projects.checkout(project=self)

    def open_in_web(self):
        """
        Open the project in web platform

        """
        self._client_api._open_in_web(url=self.platform_url)

    def add_member(self, email, role: MemberRole = MemberRole.DEVELOPER):
        """
        Add a member to the project.

        :param str email: member email
        ::param role: dl.MemberRole.OWNER, dl.MemberRole.DEVELOPER, dl.MemberRole.ANNOTATOR, dl.MemberRole.ANNOTATION_MANAGER
        :return: dict that represent the user
        :rtype: dict
        """
        return self.projects.add_member(email=email, role=role, project_id=self.id)

    def update_member(self, email, role: MemberRole = MemberRole.DEVELOPER):
        """
        Update member's information/details from the project.

        :param str email: member email
        :param role: dl.MemberRole.OWNER, dl.MemberRole.DEVELOPER, dl.MemberRole.ANNOTATOR, dl.MemberRole.ANNOTATION_MANAGER
        :return: dict that represent the user
        :rtype: dict
        """
        return self.projects.update_member(email=email, role=role, project_id=self.id)

    def remove_member(self, email):
        """
        Remove a member from the project.

        :param str email: member email
        :return: dict that represent the user
        :rtype: dict
        """
        return self.projects.remove_member(email=email, project_id=self.id)

    def list_members(self, role: MemberRole = None):
        """
        List the project members.

        :param role: dl.MemberRole.OWNER, dl.MemberRole.DEVELOPER, dl.MemberRole.ANNOTATOR, dl.MemberRole.ANNOTATION_MANAGER
        :return: list of the project members
        :rtype: list
        """
        return self.projects.list_members(project=self, role=role)
