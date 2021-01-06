from collections import namedtuple
import traceback
import logging
from typing import List

import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


class OntologySpec:

    def __init__(self, ontology_id: str, labels: List[str] = None):
        self.labels = labels if labels is not None else list()
        self.ontology_id = ontology_id

    def to_json(self) -> dict:
        _json = {
            'labels': self.labels,
            'ontologyId': self.ontology_id
        }

        return _json

    @classmethod
    def from_json(cls, _json: dict):
        return cls(
            ontology_id=_json.get('ontologyId'),
            labels=_json.get('labels')
        )


@attr.s
class Snapshot(entities.BaseEntity):
    """
    Snapshot object
    """
    # platform
    id = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib(repr=False)
    artifact = attr.ib()
    name = attr.ib()
    description = attr.ib()
    version = attr.ib()
    is_global = attr.ib()
    ontology_spec = attr.ib()
    status = attr.ib()
    tags = attr.ib()
    configuration = attr.ib()

    # name change
    model_id = attr.ib(repr=False)
    project_id = attr.ib()
    org_id = attr.ib()
    dataset_id = attr.ib(repr=False)

    # sdk
    _model = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    @staticmethod
    def _protected_from_json(_json, client_api, project, model, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform representation of snapshot
        :param client_api: ApiClient entity
        :param project: project that owns the snapshot
        :param model: model entity of the snapshot
        :param is_fetched: is Entity fetched from Platform
        :return: Snapshot entity
        """
        try:
            snapshot = Snapshot.from_json(_json=_json,
                                          client_api=client_api,
                                          project=project,
                                          model=model,
                                          is_fetched=is_fetched)
            status = True
        except Exception:
            snapshot = traceback.format_exc()
            status = False
        return status, snapshot

    @classmethod
    def from_json(cls, _json, client_api, project, model, is_fetched=True):
        """
        Turn platform representation of snapshot into a snapshot entity

        :param _json: platform representation of snapshot
        :param client_api: ApiClient entity
        :param project: project that owns the snapshot
        :param model: model entity of the snapshot
        :param is_fetched: is Entity fetched from Platform
        :return: Snapshot entity
        """
        if project is not None:
            if project.id != _json.get('projectId', None):
                logger.warning('Snapshot has been fetched from a project that is not in it projects list')
                project = None

        if model is not None:
            if model.id != _json.get('modelId', None):
                logger.warning('Snapshot has been fetched from a model that is not in it projects list')
                model = None

        artifact = entities.PackageCodebase.from_json(_json=_json.get('artifact'))
        ontology_spec = OntologySpec.from_json(_json=_json.get('ontologySpec'))
                
        inst = cls(
            configuration=_json.get('configuration', None),
            is_global=_json.get('global', None),
            org_id=_json.get('orgId', None),
            description=_json.get('description', None),
            status=_json.get('status', None),
            tags=_json.get('tags', None),
            project_id=_json.get('projectId', None),
            dataset_id=_json.get('datasetId', None),
            model_id=_json.get('modelId', None),
            artifact=artifact,
            ontology_spec=ontology_spec,
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            client_api=client_api,
            name=_json.get('name', None),
            project=project,
            model=model,
            id=_json.get('id', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Turn Snapshot entity into a platform representation of Snapshot

        :return: platform json of snapshot
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Snapshot)._project,
                                                        attr.fields(Snapshot)._model,
                                                        attr.fields(Snapshot)._repositories,
                                                        attr.fields(Snapshot)._client_api,
                                                        attr.fields(Snapshot).model_id,
                                                        attr.fields(Snapshot).org_id,
                                                        attr.fields(Snapshot).project_id,
                                                        attr.fields(Snapshot).dataset_id,
                                                        attr.fields(Snapshot).ontology_spec,
                                                        attr.fields(Snapshot).artifact,
                                                        ))

        _json['modelId'] = self.model_id
        _json['orgId'] = self.org_id
        _json['projectId'] = self.project_id
        _json['datasetId'] = self.dataset_id
        _json['artifact'] = self.artifact.to_json()
        _json['ontologySpec'] = self.ontology_spec.to_json()

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

    @property
    def ontology_id(self):
        if self.ontology_spec:
            if self.ontology_spec.ontology_id:
                return self.ontology_spec.ontology_id

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'snapshots', 'models'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 snapshots=repositories.Snapshots(client_api=self._client_api,
                                                  project=self._project,
                                                  project_id=self.project_id,
                                                  model=self._model),
                 models=repositories.Models(client_api=self._client_api, project=self._project))
        return r

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def snapshots(self):
        assert isinstance(self._repositories.snapshots, repositories.Snapshots)
        return self._repositories.snapshots

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Snapshot changes to platform

        :return: Snapshot entity
        """
        return self.snapshots.update(snapshot=self)

    def upload(self, local_path, overwrite=True):
        """
        Upload files to existing Snapshot

        :return: Snapshot entity
        """
        return self.snapshots.upload(snapshot=self, local_path=local_path, overwrite=overwrite)

    def download(self, local_path):
        """
        Download artifacts from snapshot
        """
        return self.snapshots.download(snapshot=self, local_path=local_path)

    def download_data(self, local_path):
        """
        Download Frozen Dataset from snapshot, by Model format
        """
        return self.snapshots.download_data(snapshot=self, local_path=local_path)


    def delete(self):
        """
        Delete Snapshot object

        :return: True
        """
        return self.snapshots.delete(snapshot=self)
