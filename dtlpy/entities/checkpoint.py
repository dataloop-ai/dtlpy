from collections import namedtuple
import traceback
import logging
import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


@attr.s
class Checkpoint(entities.BaseEntity):
    """
    Checkpoint object
    """
    # platform
    id = attr.ib()
    project_id = attr.ib()
    dataset_id = attr.ib(repr=False)
    model_id = attr.ib(repr=False)
    parent_checkpoint_id = attr.ib(repr=False)
    artifacts_id = attr.ib()

    name = attr.ib()
    version = attr.ib()
    query = attr.ib(repr=False)

    url = attr.ib(repr=False)
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    creator = attr.ib()

    # sdk
    _model = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, project, model, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param dataset:
        :return:
        """
        try:
            checkpoint = Checkpoint.from_json(_json=_json,
                                              client_api=client_api,
                                              project=project,
                                              model=model,
                                              is_fetched=is_fetched)
            status = True
        except Exception:
            checkpoint = traceback.format_exc()
            status = False
        return status, checkpoint

    @classmethod
    def from_json(cls, _json, client_api, project, model, is_fetched=True):
        """
        Turn platform representation of checkpoint into a checkpoint entity

        :param _json: platform representation of checkpoint
        :param client_api:
        :param project:
        :param model:
        :param is_fetched: is Entity fetched from Platform
        :return: Checkpoint entity
        """
        inst = cls(
            project_id=_json.get('projectId', None),
            dataset_id=_json.get('datasetId', None),
            model_id=_json.get('modelId', None),
            parent_checkpoint_id=_json.get('parentCheckpointId', None),
            artifacts_id=_json.get('artifactId', None),
            query=_json.get('query', None),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            client_api=client_api,
            name=_json.get('name', None),
            url=_json.get('url', None),
            project=project,
            model=model,
            id=_json.get('id', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Checkpoint entity into a platform representation of Checkpoint

        :return: platform json of checkpoint
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Checkpoint)._project,
                                                        attr.fields(Checkpoint)._model,
                                                        attr.fields(Checkpoint)._repositories,
                                                        attr.fields(Checkpoint)._client_api,
                                                        attr.fields(Checkpoint).model_id,
                                                        attr.fields(Checkpoint).parent_checkpoint_id,
                                                        attr.fields(Checkpoint).project_id,
                                                        attr.fields(Checkpoint).dataset_id,
                                                        attr.fields(Checkpoint).artifacts_id,
                                                        ))

        _json['projectId'] = self.project_id
        _json['datasetId'] = self.dataset_id
        _json['parentCheckpointId'] = self.parent_checkpoint_id
        _json['artifactId'] = self.artifacts_id
        _json['modelId'] = self.model_id
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

    @property
    def model(self):
        if self._model is None:
            self._model = self.models.get(model_id=self.model_id)
        assert isinstance(self._model, entities.Model)
        return self._model

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'checkpoints', 'models'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 checkpoints=repositories.Checkpoints(client_api=self._client_api,
                                                      project=self._project,
                                                      project_id=self.project_id,
                                                      model=self.model),
                 models=repositories.Models(client_api=self._client_api, project=self._project))
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

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Checkpoint changes to platform

        :return: Checkpoint entity
        """
        return self.checkpoints.update(checkpoint=self)

    def download(self, local_path):
        """
        Download artifacts from checkpoint
        """
        return self.checkpoints.download(checkpoint=self, local_path=local_path)

    def delete(self):
        """
        Delete Checkpoint object

        :return: True
        """
        return self.checkpoints.delete(checkpoint=self)
