import json
from collections import namedtuple
from enum import Enum
import traceback
import logging

import attr

from .. import repositories, entities
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class DatasetSubsetType(str, Enum):
    """Available types for dataset subsets"""
    TRAIN = 'train'
    VALIDATION = 'validation'
    TEST = 'test'


class PlotSample:
    def __init__(self, figure, legend, x, y):
        """
        Create a single metric sample for Model

        :param figure: figure name identifier
        :param legend: line name identifier
        :param x: x value for the current sample
        :param y: y value for the current sample
        """
        self.figure = figure
        self.legend = legend
        self.x = x
        self.y = y

    def to_json(self) -> dict:
        _json = {'figure': self.figure,
                 'legend': self.legend,
                 'data': {'x': self.x,
                          'y': self.y}}
        return _json


# class MatrixSample:
#     def __init__(self, figure, legend, x, y):
#         """
#         Create a single metric sample for Model
#
#         :param figure: figure name identifier
#         :param legend: line name identifier
#         :param x: x value for the current sample
#         :param y: y value for the current sample
#         """
#         self.figure = figure
#         self.legend = legend
#         self.x = x
#         self.y = y
#
#     def to_json(self) -> dict:
#         _json = {'figure': self.figure,
#                  'legend': self.legend,
#                  'data': {'x': self.x,
#                           'y': self.y}}
#         return _json


@attr.s
class Model(entities.BaseEntity):
    """
    Model object
    """
    # platform
    id = attr.ib()
    creator = attr.ib()
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    model_artifacts = attr.ib()
    name = attr.ib()
    description = attr.ib()
    ontology_id = attr.ib(repr=False)
    labels = attr.ib()
    status = attr.ib()
    tags = attr.ib()
    configuration = attr.ib()
    metadata = attr.ib()
    input_type = attr.ib()
    output_type = attr.ib()
    module_name = attr.ib()

    url = attr.ib()
    scope = attr.ib()
    version = attr.ib()
    context = attr.ib()

    # name change
    package_id = attr.ib(repr=False)
    project_id = attr.ib()
    dataset_id = attr.ib(repr=False)

    # sdk
    _project = attr.ib(repr=False)
    _package = attr.ib(repr=False)
    _dataset = attr.ib(repr=False)
    _client_api = attr.ib(type=ApiClient, repr=False)
    _repositories = attr.ib(repr=False)
    _ontology = attr.ib(repr=False, default=None)

    @staticmethod
    def _protected_from_json(_json, client_api, project, package, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform representation of Model
        :param client_api: ApiClient entity
        :param project: project that owns the model
        :param package: package entity of the model
        :param is_fetched: is Entity fetched from Platform
        :return: Model entity
        """
        try:
            model = Model.from_json(_json=_json,
                                    client_api=client_api,
                                    project=project,
                                    package=package,
                                    is_fetched=is_fetched)
            status = True
        except Exception:
            model = traceback.format_exc()
            status = False
        return status, model

    @classmethod
    def from_json(cls, _json, client_api, project, package, is_fetched=True):
        """
        Turn platform representation of model into a model entity

        :param _json: platform representation of model
        :param client_api: ApiClient entity
        :param project: project that owns the model
        :param package: package entity of the model
        :param is_fetched: is Entity fetched from Platform
        :return: Model entity
        """
        if project is not None:
            if project.id != _json.get('context', {}).get('project', None):
                logger.warning('Model has been fetched from a project that is not in it projects list')
                project = None

        if package is not None:
            if package.id != _json.get('packageId', None):
                logger.warning('Model has been fetched from a model that is not in it projects list')
                model = None

        model_artifacts = [entities.Artifact.from_json(_json=artifact,
                                                       client_api=client_api,
                                                       project=project)
                           for artifact in _json.get('artifacts', list())]

        inst = cls(
            configuration=_json.get('configuration', None),
            description=_json.get('description', None),
            status=_json.get('status', None),
            tags=_json.get('tags', None),
            metadata=_json.get('metadata', dict()),
            project_id=_json.get('context', {}).get('project', None),
            dataset_id=_json.get('datasetId', None),
            package_id=_json.get('packageId', None),
            model_artifacts=model_artifacts,
            labels=_json.get('labels', None),
            ontology_id=_json.get('ontology_id', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            creator=_json.get('context', {}).get('creator', None),
            client_api=client_api,
            name=_json.get('name', None),
            project=project,
            package=package,
            dataset=None,
            id=_json.get('id', None),
            url=_json.get('url', None),
            scope=_json.get('scope', entities.EntityScopeLevel.PROJECT),
            version=_json.get('version', '1.0.0'),
            context=_json.get('context', {}),
            input_type=_json.get('inputType', None),
            output_type=_json.get('outputType', None),
            module_name = _json.get('moduleName', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Get the dict of Model

        :return: platform json of model
        :rtype: dict
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Model)._project,
                                                        attr.fields(Model)._package,
                                                        attr.fields(Model)._dataset,
                                                        attr.fields(Model)._ontology,
                                                        attr.fields(Model)._repositories,
                                                        attr.fields(Model)._client_api,
                                                        attr.fields(Model).package_id,
                                                        attr.fields(Model).project_id,
                                                        attr.fields(Model).dataset_id,
                                                        attr.fields(Model).ontology_id,
                                                        attr.fields(Model).model_artifacts,
                                                        attr.fields(Model).created_at,
                                                        attr.fields(Model).updated_at,
                                                        attr.fields(Model).input_type,
                                                        attr.fields(Model).output_type,
                                                        ))
        _json['packageId'] = self.package_id
        _json['datasetId'] = self.dataset_id
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        _json['inputType'] = self.input_type
        _json['outputType'] = self.output_type
        _json['moduleName'] = self.module_name

        model_artifacts = list()
        for artifact in self.model_artifacts:
            if artifact.type in ['file', 'dir']:
                artifact = {'type': 'item',
                            'itemId': artifact.id}
            else:
                artifact = artifact.to_json(as_artifact=True)
            model_artifacts.append(artifact)
        _json['artifacts'] = model_artifacts
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
    def package(self):
        if self._package is None:
            try:
                self._package = self.packages.get(package_id=self.package_id)
            except Exception as e:
                error = e
                try:
                    self._package = self.dpks.get(dpk_id=self.package_id)
                except Exception:
                    raise error
            self._repositories = self.set_repositories()  # update the repos with the new fetched entity
        assert isinstance(self._package, (entities.Package, entities.Dpk))
        return self._package

    @property
    def dataset(self):
        if self._dataset is None:
            if self.dataset_id is None:
                raise RuntimeError("Model {!r} has no dataset. Can be used only for inference".format(self.id))
            self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
            self._repositories = self.set_repositories()  # update the repos with the new fetched entity
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def ontology(self):
        if self._ontology is None:
            if self.ontology_id is None:
                raise RuntimeError("Model {!r} has no ontology.".format(self.id))
            self._ontology = self.ontologies.get(ontology_id=self.ontology_id)
        assert isinstance(self._ontology, entities.Ontology)
        return self._ontology

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['projects', 'datasets', 'packages', 'models', 'ontologies', 'artifacts',
                                       'metrics', 'dpks', 'services'])

        r = reps(projects=repositories.Projects(client_api=self._client_api),
                 datasets=repositories.Datasets(client_api=self._client_api,
                                                project=self._project),
                 models=repositories.Models(client_api=self._client_api,
                                            project=self._project,
                                            project_id=self.project_id,
                                            package=self._package),
                 packages=repositories.Packages(client_api=self._client_api,
                                                project=self._project),
                 ontologies=repositories.Ontologies(client_api=self._client_api,
                                                    project=self._project,
                                                    dataset=self._dataset),
                 artifacts=repositories.Artifacts(client_api=self._client_api,
                                                  project=self._project,
                                                  project_id=self.project_id,
                                                  model=self),
                 metrics=repositories.Metrics(client_api=self._client_api,
                                              model=self),
                 dpks=repositories.Dpks(client_api=self._client_api),
                 services=repositories.Services(client_api=self._client_api,
                                                project=self._project,
                                                project_id=self.project_id),
                 )
        return r

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/model/{}".format(self.project_id, self.id))

    @property
    def projects(self):
        assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def models(self):
        assert isinstance(self._repositories.models, repositories.Models)
        return self._repositories.models

    @property
    def packages(self):
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    @property
    def dpks(self):
        assert isinstance(self._repositories.dpks, repositories.Dpks)
        return self._repositories.dpks

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def artifacts(self):
        assert isinstance(self._repositories.artifacts, repositories.Artifacts)
        return self._repositories.artifacts

    @property
    def metrics(self):
        assert isinstance(self._repositories.metrics, repositories.Metrics)
        return self._repositories.metrics

    @property
    def services(self):
        assert isinstance(self._repositories.services, repositories.Services)
        return self._repositories.services

    @property
    def id_to_label_map(self):
        if 'id_to_label_map' not in self.configuration:
            # default
            if self.ontology_id == 'null' or self.ontology_id is None:
                self.configuration['id_to_label_map'] = {int(idx): lbl for idx, lbl in enumerate(self.labels)}
            else:
                self.configuration['id_to_label_map'] = {int(idx): lbl.tag for idx, lbl in
                                                         enumerate(self.ontology.labels)}
        else:
            self.configuration['id_to_label_map'] = {int(idx): lbl for idx, lbl in
                                                     self.configuration['id_to_label_map'].items()}
        return self.configuration['id_to_label_map']

    @id_to_label_map.setter
    def id_to_label_map(self, mapping: dict):
        self.configuration['id_to_label_map'] = {int(idx): lbl for idx, lbl in mapping.items()}

    @property
    def label_to_id_map(self):
        if 'label_to_id_map' not in self.configuration:
            self.configuration['label_to_id_map'] = {v: int(k) for k, v in self.id_to_label_map.items()}
        return self.configuration['label_to_id_map']

    @label_to_id_map.setter
    def label_to_id_map(self, mapping: dict):
        self.configuration['label_to_id_map'] = {v: int(k) for k, v in mapping.items()}

    ###########
    # methods #
    ###########

    def add_subset(self, subset_name: str, subset_filter: entities.Filters):
        """
        Adds a subset for the model, specifying a subset of the model's dataset that could be used for training or
        validation.

        :param str subset_name: the name of the subset
        :param dtlpy.entities.Filters subset_filter: the filtering operation that this subset performs in the dataset.

        **Example**

        .. code-block:: python

            model.add_subset(subset_name='train', subset_filter=dtlpy.Filters(field='dir', values='/train'))
            model.metadata['system']['subsets']
                {'train': <dtlpy.entities.filters.Filters object at 0x1501dfe20>}

        """
        self.models.add_subset(self, subset_name, subset_filter)

    def delete_subset(self, subset_name: str):
        """
        Removes a subset from the model's metadata.

        :param str subset_name: the name of the subset

        **Example**

        .. code-block:: python

            model.add_subset(subset_name='train', subset_filter=dtlpy.Filters(field='dir', values='/train'))
            model.metadata['system']['subsets']
                {'train': <dtlpy.entities.filters.Filters object at 0x1501dfe20>}
            models.delete_subset(subset_name='train')
            metadata['system']['subsets']
                {}

        """
        self.models.delete_subset(self, subset_name)

    def update(self, system_metadata=False):
        """
        Update Models changes to platform

        :param bool system_metadata: bool - True, if you want to change metadata system
        :return: Models entity
        """
        return self.models.update(model=self,
                                  system_metadata=system_metadata)

    def open_in_web(self):
        """
        Open the model in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def delete(self):
        """
        Delete Model object

        :return: True
        """
        return self.models.delete(model=self)

    def clone(self,
              model_name: str,
              dataset: entities.Dataset = None,
              configuration: dict = None,
              status=None,
              scope=None,
              project_id: str = None,
              labels: list = None,
              description: str = None,
              tags: list = None,
              train_filter: entities.Filters = None,
              validation_filter: entities.Filters = None,
              ):
        """
        Clones and creates a new model out of existing one

        :param str model_name: `str` new model name
        :param str dataset: dataset object for the cloned model
        :param dict configuration: `dict` (optional) if passed replaces the current configuration
        :param str status: `str` (optional) set the new status
        :param str scope: `str` (optional) set the new scope. default is "project"
        :param str project_id: `str` specify the project id to create the new model on (if other than the source model)
        :param list labels:  `list` of `str` - label of the model
        :param str description: `str` description of the new model
        :param list tags:  `list` of `str` - label of the model
        :param dtlpy.entities.filters.Filters train_filter: Filters entity or a dictionary to define the items' scope in the specified dataset_id for the model train
        :param dtlpy.entities.filters.Filters validation_filter: Filters entity or a dictionary to define the items' scope in the specified dataset_id for the model validation

        :return: dl.Model which is a clone version of the existing model
        """
        return self.models.clone(from_model=self,
                                 model_name=model_name,
                                 project_id=project_id,
                                 dataset=dataset,
                                 scope=scope,
                                 status=status,
                                 configuration=configuration,
                                 labels=labels,
                                 description=description,
                                 tags=tags,
                                 train_filter=train_filter,
                                 validation_filter=validation_filter,
                                 )

    def train(self, service_config=None):
        """
        Train the model in the cloud. This will create a service and will run the adapter's train function as an execution

        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :return:
        """
        return self.models.train(model_id=self.id, service_config=service_config)

    def evaluate(self, dataset_id, filters: entities.Filters = None, service_config=None):
        """
        Evaluate Model, provide data to evaluate the model on You can also provide specific config for the deployed service

        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :param str dataset_id: ID of the dataset to evaluate
        :param entities.Filters filters: dl.Filter entity to run the predictions on
        :return:
        """
        return self.models.evaluate(model_id=self.id,
                                    dataset_id=dataset_id,
                                    filters=filters,
                                    service_config=service_config)

    def predict(self, item_ids):
        """
        Run model prediction with items

        :param item_ids: a list of item id to run the prediction.
        :return:
        """
        return self.models.predict(model=self, item_ids=item_ids)

    def deploy(self, service_config=None) -> entities.Service:
        """
        Deploy a trained model. This will create a service that will execute predictions

        :param dict service_config : Service object as dict. Contains the spec of the default service to create.

        :return: dl.Service: The deployed service
        """
        return self.models.deploy(model_id=self.id, service_config=service_config)

    def log(self,
            service=None,
            size=None,
            checkpoint=None,
            start=None,
            end=None,
            follow=False,
            text=None,
            execution_id=None,
            function_name=None,
            replica_id=None,
            system=False,
            view=True,
            until_completed=True,
            model_operation: str = None,
            ):
        """
        Get service logs

        :param service: service object
        :param int size: size
        :param dict checkpoint: the information from the lst point checked in the service
        :param str start: iso format time
        :param str end: iso format time
        :param bool follow: if true, keep stream future logs
        :param str text: text
        :param str execution_id: execution id
        :param str function_name: function name
        :param str replica_id: replica id
        :param bool system: system
        :param bool view: if true, print out all the logs
        :param bool until_completed: wait until completed
        :param str model_operation: model operation action
        :return: ServiceLog entity
        :rtype: ServiceLog

        **Example**:

        .. code-block:: python

            service_log = service.log()
        """
        return self.services.log(service=service,
                                 size=size,
                                 checkpoint=checkpoint,
                                 start=start,
                                 end=end,
                                 follow=follow,
                                 execution_id=execution_id,
                                 function_name=function_name,
                                 replica_id=replica_id,
                                 system=system,
                                 text=text,
                                 view=view,
                                 until_completed=until_completed,
                                 model_id=self.id,
                                 model_operation=model_operation,
                                 project_id=self.project_id)
