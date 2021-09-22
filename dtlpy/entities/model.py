from collections import namedtuple
from enum import Enum
import traceback
import logging
import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


class ModelInputType(str, Enum):
    VIDEO = 'video'
    IMAGE = 'image'
    TEXT = 'text'
    AUDIO = 'audio'


class ModelOutputType(str, Enum):
    BOX = entities.Box.type
    CLASSIFICATION = entities.Classification.type
    COMPARISON = entities.Comparison.type
    ELLIPSE = entities.Ellipse.type
    POINT = entities.Point.type
    POLYGON = entities.Polygon.type
    SEGMENTATION = entities.Segmentation.type
    SUBTITLE = entities.Subtitle.type
    TEXT = entities.Text.type


@attr.s
class Model(entities.BaseEntity):
    """
    Model object
    """
    # platform
    id = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()
    name = attr.ib()
    url = attr.ib(repr=False)
    codebase = attr.ib(type=entities.Codebase)
    description = attr.ib()
    version = attr.ib()
    tags = attr.ib()

    # name change
    is_global = attr.ib()
    project_id = attr.ib()
    org_id = attr.ib()
    entry_point = attr.ib()
    class_name = attr.ib()
    input_type = attr.ib()
    output_type = attr.ib()

    # revisions
    _revisions = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)
    _codebases = attr.ib(default=None)
    _artifacts = attr.ib(default=None)

    @property
    def revisions(self):
        if self._revisions is None:
            self._revisions = self.models.revisions(model=self)
        return self._revisions

    @staticmethod
    def _protected_from_json(_json, client_api, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform representation of model
        :param client_api: ApiClient entity
        :param project: project entity
        :param is_fetched: is Entity fetched from Platform
        :return:
        """
        try:
            model = Model.from_json(_json=_json,
                                    client_api=client_api,
                                    project=project,
                                    is_fetched=is_fetched)
            status = True
        except Exception:
            model = traceback.format_exc()
            status = False
        return status, model

    @classmethod
    def from_json(cls, _json, client_api, project, is_fetched=True):
        """
        Turn platform representation of model into a model entity

        :param _json: platform representation of model
        :param client_api: ApiClient entity
        :param project: project entity
        :param is_fetched: is Entity fetched from Platform
        :return: Model entity
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Model has been fetched from a project that is not in it projects list')
                project = None

        if 'codebase' in _json:
            codebase = entities.Codebase.from_json(_json=_json['codebase'],
                                                   client_api=client_api)
        else:
            codebase = None

        inst = cls(
            project_id=_json.get('projectId', None),
            codebase=codebase,
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            description=_json.get('description', None),
            creator=_json.get('creator', None),
            entry_point=_json.get('entryPoint', None),
            class_name=_json.get('className', 'ModelAdapter'),
            client_api=client_api,
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            id=_json.get('id', None),
            org_id=_json.get('orgId', None),
            output_type=_json.get('outputType', None),
            input_type=_json.get('inputType', None),
            is_global=_json.get('global', None),
            revisions=_json.get('revisions', None),
            tags=_json.get('tags', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Model entity into a platform representation of Model

        :return: platform json of model
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Model)._project,
                                                        attr.fields(Model)._repositories,
                                                        attr.fields(Model)._codebases,
                                                        attr.fields(Model)._revisions,
                                                        attr.fields(Model).is_global,
                                                        attr.fields(Model)._artifacts,
                                                        attr.fields(Model).org_id,
                                                        attr.fields(Model).input_type,
                                                        attr.fields(Model).output_type,
                                                        attr.fields(Model)._client_api,
                                                        attr.fields(Model).codebase,
                                                        attr.fields(Model).entry_point,
                                                        attr.fields(Model).class_name,
                                                        attr.fields(Model).project_id,
                                                        ))

        _json['global'] = self.is_global
        _json['orgId'] = self.org_id
        _json['inputType'] = self.input_type
        _json['outputType'] = self.output_type
        _json['projectId'] = self.project_id
        _json['entryPoint'] = self.entry_point
        _json['className'] = self.class_name
        _json['codebase'] = self.codebase.to_json()

        return _json

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            self._project = self.projects.get(project_id=self.project_id, fetch=None)
        assert isinstance(self._project, entities.Project)
        return self._project

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'models', 'snapshots', 'buckets'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 models=repositories.Models(client_api=self._client_api,
                                            project=self._project),
                 snapshots=repositories.Snapshots(client_api=self._client_api,
                                                  project=self._project,
                                                  model=self),
                 buckets=repositories.Buckets(client_api=self._client_api,
                                              project=self._project,
                                              project_id=self.project_id)
                 )
        return r

    @property
    def codebases(self):
        if self._codebases is None:
            self._codebases = repositories.Codebases(
                client_api=self._client_api,
                project=self._project,
                project_id=self.project_id
            )
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    @property
    def artifacts(self):
        if self._artifacts is None:
            self._artifacts = repositories.Artifacts(
                client_api=self._client_api,
                project=self._project,
                project_id=self.project_id,
                model=self
            )
        assert isinstance(self._artifacts, repositories.Artifacts)
        return self._artifacts

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def snapshots(self):
        assert isinstance(self._repositories.snapshots, repositories.Snapshots)
        return self._repositories.snapshots

    @property
    def buckets(self):
        assert isinstance(self._repositories.buckets, repositories.Buckets)
        return self._repositories.buckets

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    ##############
    # properties #
    ##############
    @property
    def git_status(self):
        status = 'Git status unavailable'
        try:
            if self.codebase.type == entities.PackageCodebaseType.ITEM:
                if 'git' in self.codebase.item.metadata:
                    status = self.codebase.item.metadata['git'].get('status', status)
        except Exception:
            logging.debug('Error getting codebase')
        return status

    @property
    def git_log(self):
        log = 'Git log unavailable'
        try:
            if self.codebase.type == entities.PackageCodebaseType.ITEM:
                if 'git' in self.codebase.item.metadata:
                    log = self.codebase.item.metadata['git'].get('log', log)
        except Exception:
            logging.debug('Error getting codebase')
        return log

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Model changes to platform

        :return: Model entity
        """
        return self.models.update(model=self)

    def checkout(self):
        """
        Checkout as model

        :return:
        """
        return self.models.checkout(model=self)

    def delete(self):
        """
        Delete Model object

        :return: True
        """
        return self.models.delete(model=self)

    def push(self,
             src_path: str = None,
             entry_point: str = None,
             codebase: entities.ItemCodebase = None):
        """
        Upload codebase to Model

        :param src_path: codebase location. if None pwd will be taken
        :param entry_point: location on the ModelAdapter class
        :param codebase: if none new will be created from src_path
        :return:
        """
        return self.project.models.push(model=self,
                                        entry_point=entry_point,
                                        codebase=codebase,
                                        src_path=src_path)

    def build(self, local_path=None, from_local=None, log_level='INFO'):
        """
        Push local model

        :param local_path: local path where the model code should be.
                           if model is downloaded - this will be the point it will be downloaded
                           (if from_local=False - codebase will be downloaded)
        :param from_local: bool. use current directory to build
        :param log_level: log level
        :return: ModelAdapter (dl.BaseModelAdapter)
        """
        return self.models.build(model=self,
                                 local_path=local_path,
                                 from_local=from_local,
                                 log_level=log_level)

    def generate_adapter(self, local_path=None, overwrite=False):
        """
        Creates a local model_adapter file with virtual functions to be implemented
        :param local_path: `str` path to save the adapter (if None uses current working dir)
        :param overwrite:  `bool` whether to over write an existing file (default False)
        """
        self.models.generate(src_path=local_path, entry_point=self.entry_point, overwrite=overwrite)
