from collections import namedtuple
from enum import Enum
import traceback
import logging
from typing import List

import attr

from .. import repositories, entities, services

logger = logging.getLogger(name=__name__)


# TODO: Consider using DataPartition as a new name
class SnapshotPartitionType(str, Enum):
    """Available types for snapshot_partition"""
    TRAIN = 'train'
    VALIDATION = 'validation'
    TEST = 'test'


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
    bucket = attr.ib()
    name = attr.ib()
    description = attr.ib()
    version = attr.ib()
    is_global = attr.ib()
    ontology_id = attr.ib(repr=False)
    labels = attr.ib()
    status = attr.ib()
    tags = attr.ib()
    configuration = attr.ib()

    # name change
    model_id = attr.ib(repr=False)
    project_id = attr.ib()
    org_id = attr.ib()
    dataset_id = attr.ib(repr=False)

    # sdk
    _project = attr.ib(repr=False)
    _model = attr.ib(repr=False)
    _dataset = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)
    _ontology = attr.ib(repr=False, default=None)

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

        if "bucket" in _json:
            bucket = entities.Bucket.from_json(_json=_json.get('bucket'),
                                               client_api=client_api,
                                               project=project)
        else:
            bucket = None
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
            bucket=bucket,
            ontology_id=ontology_spec.ontology_id,
            labels=ontology_spec.labels,
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            version=_json.get('version', None),
            creator=_json.get('creator', None),
            client_api=client_api,
            name=_json.get('name', None),
            project=project,
            model=model,
            dataset=None,
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
                                                        attr.fields(Snapshot)._dataset,
                                                        attr.fields(Snapshot)._repositories,
                                                        attr.fields(Snapshot)._client_api,
                                                        attr.fields(Snapshot).model_id,
                                                        attr.fields(Snapshot).org_id,
                                                        attr.fields(Snapshot).project_id,
                                                        attr.fields(Snapshot).dataset_id,
                                                        attr.fields(Snapshot).labels,
                                                        attr.fields(Snapshot).ontology_id,
                                                        attr.fields(Snapshot).bucket,
                                                        ))

        _json['modelId'] = self.model_id
        _json['orgId'] = self.org_id
        _json['projectId'] = self.project_id
        _json['datasetId'] = self.dataset_id
        if self.bucket is not None:
            _json['bucket'] = self.bucket.to_json()
        _json['ontologySpec'] = entities.OntologySpec(ontology_id=self.ontology_id,
                                                      labels=self.labels).to_json()

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
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def ontology(self):
        if self._ontology is None:
            self._ontology = self.ontologies.get(ontology_id=self.ontology_id)
        assert isinstance(self._ontology, entities.Ontology)
        return self._ontology

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'datasets', 'snapshots', 'models', 'ontologies'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 datasets=repositories.Datasets(client_api=self._client_api,
                                                project=self._project),
                 snapshots=repositories.Snapshots(client_api=self._client_api,
                                                  project=self._project,
                                                  project_id=self.project_id,
                                                  model=self._model),
                 models=repositories.Models(client_api=self._client_api, project=self._project),
                 ontologies=repositories.Ontologies(client_api=self._client_api,
                                                    project=self._project,
                                                    dataset=self._dataset))
        return r

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def snapshots(self):
        assert isinstance(self._repositories.snapshots, repositories.Snapshots)
        return self._repositories.snapshots

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def label_map(self):
        if 'label_map' not in self.configuration:
            # default
            self.configuration['label_map'] = {ont.tag: i for i, ont in enumerate(self.ontology.labels)}
        return self.configuration['label_map']

    @label_map.setter
    def label_map(self, mapping: dict):
        self.configuration['label_map'] = mapping

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Snapshot changes to platform

        :return: Snapshot entity
        """
        return self.snapshots.update(snapshot=self)

    def delete(self):
        """
        Delete Snapshot object

        :return: True
        """
        return self.snapshots.delete(snapshot=self)

    def download_from_bucket(self,
                             remote_paths=None,
                             local_path=None,
                             overwrite=False,
                             ):
        """

        Download binary file from bucket.

        :param remote_paths: list of items to download
        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        return self.bucket.download(local_path=local_path,
                                    remote_paths=remote_paths,
                                    overwrite=overwrite)

    def upload_to_bucket(self,
                         # what to upload
                         local_path,
                         # add information
                         overwrite=False):
        """

        Upload binary file to bucket. get by name, id or type.
        If bucket exists - overwriting binary
        Else and if create==True a new bucket will be created and uploaded

        :param overwrite: optional - default = False
        :param local_path: local binary file or folder to upload
        :return:
        """
        return self.bucket.upload(local_path=local_path,
                                  overwrite=overwrite)

    def download_partition(self, partition, local_path=None, filters: entities.Filters = None):
        """
        Download a specific partition of the dataset to local_path

        This function is commonly used with dl.ModelAdapter which implements thc convert to specific model structure

        :param partition: `dl.SnapshotPartitionType` name of the partition
        :param local_path: local path directory to download the data
        :param filters:  dl.entities.Filters to add the specific partitions constraint to
        :return List `str` of the new downloaded path of each item
        """
        return self.dataset.download_partition(partition=partition,
                                               local_path=local_path,
                                               filters=filters)

    def set_partition(self, partition, filters=None):
        """
        Updates all items returned by filters in the dataset to specific partition

        :param partition:  `dl.entities.SnapshotPartitionType` to set to
        :param filters:  dl.entities.Filters to add the specific partitions constraint to
        :return:  dl.PagedEntities
        """
        self.dataset.set_partition(partition, filters=filters)

    def get_partitions(self, partitions, filters: entities.Filters = None):
        """
        Returns PagedEntity of items from one or more partitions

        :param partitions: `dl.entities.SnapshotPartitionType` or a list. Name of the partitions
        :param filters:  dl.Filters to add the specific partitions constraint to
        :return: `dl.PagedEntities` of `dl.Item`  preforms items.list()
        """
        return self.dataset.get_partitions(partitions=partitions, filters=filters)

    def add_metric_samples(self, samples):
        """
        Adds samples to the `TimeSeries` DB to be used for metric performance
        :param samples: list of dict - must contain: `item_id`, `gt_id`, `prd_id`, and 'score`
        :return:
        """

        for sample in samples:
            _sample = {
                'snapshotId': self.id,
                'output_type': self.model.output_type,
                'frozen_datasetId': self.dataset.id,
                'frozen_itemId': sample['item_id'],
                'prediction_id': sample['prd_id'],
                'acutal_id': sample['gt_id'],
                'score': sample['score']  # for 'box' type it's iou
            }
            self.project.times_series.add_samples(_sample)
