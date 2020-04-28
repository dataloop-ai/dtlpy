from collections import namedtuple
import logging
import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


@attr.s
class Model(entities.BaseEntity):
    """
    Model object
    """
    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    version = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    name = attr.ib()
    description = attr.ib()
    codebase_id = attr.ib()
    entry_point = attr.ib()
    creator = attr.ib()

    # name change
    project_id = attr.ib()

    # sdk
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @classmethod
    def from_json(cls, _json, client_api, project, is_fetched=True):
        """
        Turn platform representation of model into a model entity

        :param _json: platform representation of model
        :param client_api:
        :param project:
        :param is_fetched: is Entity fetched from Platform
        :return: Model entity
        """
        inst = cls(
            project_id=_json.get('projectId', None),
            codebase_id=_json.get('codebaseId', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            description=_json.get('description', None),
            creator=_json.get('creator', None),
            entry_point=_json.get('entryPoint', None),
            client_api=client_api,
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            id=_json.get('id', None)
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
                                                        attr.fields(Model)._client_api,
                                                        attr.fields(Model).codebase_id,
                                                        attr.fields(Model).entry_point,
                                                        attr.fields(Model).project_id,
                                                        ))

        _json['projectId'] = self.project_id
        _json['entryPoint'] = self.entry_point
        _json['codebaseId'] = self.codebase_id
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
                          field_names=['projects', 'models', 'checkpoints'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 models=repositories.Models(client_api=self._client_api, project=self._project),
                 checkpoints=repositories.Checkpoints(client_api=self._client_api,
                                                      project=self._project,
                                                      model=self),
                 )
        return r

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def checkpoints(self):
        assert isinstance(self._repositories.checkpoints, repositories.Checkpoints)
        return self._repositories.checkpoints

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
            codebase = self.project.codebases.get(codebase_id=self.codebase_id, version=self.version - 1)
            if 'git' in codebase.metadata:
                status = codebase.metadata['git'].get('status', status)
        except Exception:
            logging.debug('Error getting codebase')
        return status

    @property
    def git_log(self):
        log = 'Git log unavailable'
        try:
            codebase = self.project.codebases.get(codebase_id=self.codebase_id, version=self.version - 1)
            if 'git' in codebase.metadata:
                log = codebase.metadata['git'].get('log', log)
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

    def push(self, codebase_id=None, src_path=None, model_name=None, modules=None, checkout=False):
        """
         Push local model

        :param checkout:
        :param codebase_id:
        :param src_path:
        :param model_name:
        :param modules:
        :return:
        """
        return self.project.models.push(model_name=model_name if model_name is not None else self.name,
                                        codebase_id=codebase_id,
                                        src_path=src_path,
                                        modules=modules,
                                        checkout=checkout)

    def build(self, local_path=None, from_local=None):
        """
        Push local model

        :param local_path:
        :return:
        """
        return self.models.build(model=self,
                                 local_path=local_path,
                                 from_local=from_local)
