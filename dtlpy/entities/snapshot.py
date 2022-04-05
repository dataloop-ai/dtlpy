from collections import namedtuple
from enum import Enum
import traceback
import logging
import warnings
from typing import List

import attr

from .. import repositories, entities, services, exceptions

logger = logging.getLogger(name='dtlpy')


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
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    bucket = attr.ib()
    name = attr.ib()
    description = attr.ib()
    is_global = attr.ib()
    ontology_id = attr.ib(repr=False)
    labels = attr.ib()
    status = attr.ib()
    tags = attr.ib()
    configuration = attr.ib()

    # name change
    model_id = attr.ib(repr=False)
    project_id = attr.ib()
    dataset_id = attr.ib(repr=False)

    # sdk
    _project = attr.ib(repr=False)
    _model = attr.ib(repr=False)
    _dataset = attr.ib(repr=False)
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)
    _ontology = attr.ib(repr=False, default=None)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

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
            description=_json.get('description', None),
            status=_json.get('status', None),
            tags=_json.get('tags', None),
            project_id=_json.get('projectId', None),
            dataset_id=_json.get('datasetId', None),
            model_id=_json.get('modelId', None),
            bucket=bucket,
            ontology_id=ontology_spec.ontology_id,
            labels=ontology_spec.labels,
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
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
        :rtype: dict
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Snapshot)._project,
                                                        attr.fields(Snapshot)._model,
                                                        attr.fields(Snapshot)._dataset,
                                                        attr.fields(Snapshot)._ontology,
                                                        attr.fields(Snapshot)._repositories,
                                                        attr.fields(Snapshot)._client_api,
                                                        attr.fields(Snapshot).model_id,
                                                        attr.fields(Snapshot).project_id,
                                                        attr.fields(Snapshot).dataset_id,
                                                        attr.fields(Snapshot).labels,
                                                        attr.fields(Snapshot).ontology_id,
                                                        attr.fields(Snapshot).bucket,
                                                        attr.fields(Snapshot).created_at,
                                                        attr.fields(Snapshot).updated_at,
                                                        ))

        _json['modelId'] = self.model_id
        _json['projectId'] = self.project_id
        _json['datasetId'] = self.dataset_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
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
            self._repositories = self.set_repositories()  # update the repos with the new fetched entity
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def model(self):
        if self._model is None:
            self._model = self.models.get(model_id=self.model_id)
            self._repositories = self.set_repositories()  # update the repos with the new fetched entity
        assert isinstance(self._model, entities.Model)
        return self._model

    @property
    def dataset(self):
        if self._dataset is None:
            if self.dataset_id is None:
                raise RuntimeError("Snapshot {!r} has no dataset. Can be used only for inference".format(self.id))
            self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
            self._repositories = self.set_repositories()  # update the repos with the new fetched entity
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
                          field_names=['projects', 'datasets', 'snapshots', 'models', 'ontologies', 'buckets'])

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
                                                    dataset=self._dataset),
                 buckets=repositories.Buckets(client_api=self._client_api,
                                              project=self._project,
                                              project_id=self.project_id,
                                              snapshot=self)
                 )

        return r

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/snapshots/{}/main".format(self.project_id, self.id))

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
    def buckets(self):
        assert isinstance(self._repositories.buckets, repositories.Buckets)
        return self._repositories.buckets

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def id_to_label_map(self):
        if 'id_to_label_map' not in self.configuration:
            # default
            if self.ontology_id == 'null' or self.ontology_id is None:
                self.configuration['id_to_label_map'] = {idx: lbl for idx, lbl in enumerate(self.labels)}
            else:
                self.configuration['id_to_label_map'] = {idx: lbl.tag for idx, lbl in enumerate(self.ontology.labels)}

        return self.configuration['id_to_label_map']

    @id_to_label_map.setter
    def id_to_label_map(self, mapping: dict):
        self.configuration['id_to_label_map'] = mapping

    ###########
    # methods #
    ###########
    def update(self):
        """
        Update Snapshot changes to platform

        :return: Snapshot entity
        """
        return self.snapshots.update(snapshot=self)

    def open_in_web(self):
        """
        Open the snapshot in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def delete(self):
        """
        Delete Snapshot object

        :return: True
        """
        return self.snapshots.delete(snapshot=self)

    def download_from_bucket(self,
                             local_path=None,
                             overwrite=False,
                             ):
        """
        Download binary file from bucket.

        :param local_path: local binary file or folder to upload
        :param overwrite: optional - default = False
        :return:
        """
        return self.bucket.download(local_path=local_path,
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

        :param local_path: local binary file or folder to upload
        :param overwrite: optional - default = False
        :return:
        """
        return self.bucket.upload(local_path=local_path,
                                  overwrite=overwrite)

    def clone(self,
              snapshot_name,
              bucket=None,  #: entities.Bucket = None,
              dataset_id: str = None,
              configuration: dict = None,
              project_id: str = None,
              labels: list = None,
              description: str = None,
              tags: list = None,
              ):
        """
        Clones and creates a new snapshot out of existing one

        :param snapshot_name: `str` new snapshot name
        :param bucket: optional - `dl.Bucket` if passed replaces the current bucket
        :param dataset_id: optional - dataset_id for the cloned snapshot
        :param configuration: optional - `dict` if passed replaces the current configuration
        :param project_id: `str` specify the project id to create the new snapshot on (if other the the source snapshot)
        :param labels:  `list` of `str` - label of the snapshot
        :param description: `str` description of the new snapshot
        :param tags:  `list` of `str` - label of the snapshot

        :return: dl.Snapshot which is a clone version of the existing snapshot
        """
        return self.snapshots.clone(from_snapshot=self,
                                    snapshot_name=snapshot_name,
                                    project_id=project_id,
                                    bucket=bucket,
                                    dataset_id=dataset_id,
                                    configuration=configuration,
                                    labels=labels,
                                    description=description,
                                    tags=tags
                                    )

    def download_partition(self, partition, local_path=None, filters: entities.Filters = None, annotation_options=None):
        """
        Download a specific partition of the dataset to local_path
        This function is commonly used with dl.ModelAdapter which implements thc convert to specific model structure

        :param partition: `dl.SnapshotPartitionType` name of the partition
        :param local_path: local path directory to download the data
        :param dtlpy.entities.filters.Filters filters:  dl.entities.Filters to add the specific partitions constraint to

        :return List `str` of the new downloaded path of each item
        """
        return self.dataset.download_partition(partition=partition,
                                               local_path=local_path,
                                               filters=filters,
                                               annotation_options=annotation_options)

    def set_partition(self, partition, filters=None):
        """
        Updates all items returned by filters in the dataset to specific partition

        :param partition:  `dl.entities.SnapshotPartitionType` to set to
        :param dtlpy.entities.filters.Filters filters:  dl.entities.Filters to add the specific partitions constraint to
        :return:  dl.PagedEntities
        """
        self.dataset.set_partition(partition, filters=filters)

    def get_partitions(self, partitions, filters: entities.Filters = None, batch_size: int = None):
        """
        Returns PagedEntity of items from one or more partitions

        :param partitions: `dl.entities.SnapshotPartitionType` or a list. Name of the partitions
        :param dtlpy.entities.filters.Filters filters:  dl.Filters to add the specific partitions constraint to
        :param batch_size: `int` how many items per page
        :return: `dl.PagedEntities` of `dl.Item`  preforms items.list()
        """
        return self.dataset.get_partitions(partitions=partitions, filters=filters, batch_size=batch_size)

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
                'actual_id': sample['gt_id'],
                'score': sample['score']  # for 'box' type it's iou
            }
            self.project.times_series.add_samples(_sample)
