import time
from typing import List
import logging

from .. import entities, repositories, exceptions, miscellaneous
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')

MIN_INTERVAL = 1
BACKOFF_FACTOR = 1.2
MAX_INTERVAL = 12


class Models:
    """
    Models Repository
    """

    def __init__(self,
                 client_api: ApiClient,
                 package: entities.Package = None,
                 project: entities.Project = None,
                 project_id: str = None):
        self._client_api = client_api
        self._project = project
        self._package = package
        self._project_id = project_id

        if self._project is not None:
            self._project_id = self._project.id

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            if self._project_id is not None:
                projects = repositories.Projects(client_api=self._client_api)
                self._project = projects.get(project_id=self._project_id)
        if self._project is None:
            if self._package is not None:
                if self._package._project is not None:
                    self._project = self._package._project
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.models repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def package(self) -> entities.Package:
        if self._package is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Package entity in {} repository.'.format(
                    self.__class__.__name__) +
                        ' Please use package.models or set a model')
        assert isinstance(self._package, entities.Package)
        return self._package

    ###########
    # methods #
    ###########
    def get(self, model_name=None, model_id=None) -> entities.Model:
        """
        Get model object
        :param model_name:
        :param model_id:
        :return: dl.Model object
        """

        if model_id is not None:
            success, response = self._client_api.gen_request(req_type="get",
                                                             path="/ml/models/{}".format(model_id))
            if not success:
                raise exceptions.PlatformException(response)
            model = entities.Model.from_json(client_api=self._client_api,
                                             _json=response.json(),
                                             project=self._project,
                                             package=self._package)
            # verify input model name is same as the given id
            if model_name is not None and model.name != model_name:
                logger.warning(
                    "Mismatch found in models.get: model_name is different then model.name:"
                    " {!r} != {!r}".format(
                        model_name,
                        model.name))
        elif model_name is not None:

            filters = entities.Filters(
                resource=entities.FiltersResource.MODEL,
                field='name',
                values=model_name
            )

            project_id = None

            if self._project is not None:
                project_id = self._project.id
            elif self._project_id is not None:
                project_id = self._project_id

            if project_id is not None:
                filters.add(field='projectId', values=project_id)

            if self._package is not None:
                filters.add(field='packageId', values=self._package.id)

            models = self.list(filters=filters)

            if models.items_count == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message='Model not found. Name: {}'.format(model_name))
            elif models.items_count > 1:
                raise exceptions.PlatformException(
                    error='400',
                    message='More than one Model found by the name of: {}. Try "get" by id or "list()".'.format(
                        model_name))
            model = models.items[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='No checked-out Model was found, must checkout or provide an identifier in inputs')

        return model

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Model]:
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, service in enumerate(response_items):
            jobs[i_service] = pool.submit(entities.Model._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': service,
                                             'package': self._package,
                                             'project': self._project})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path='/ml/models/query',
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project model

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.MODEL)
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)
        if self._package is not None:
            filters.add(field='packageId', values=self._package.id)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))

        if filters.resource != entities.FiltersResource.MODEL:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.MODEL. Got: {!r}'.format(filters.resource))

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def _set_model_filter(self,
                          metadata: dict,
                          train_filter: entities.Filters = None,
                          validation_filter: entities.Filters = None):
        if metadata is None:
            metadata = {}
        if 'system' not in metadata:
            metadata['system'] = {}
        if 'subsets' not in metadata['system']:
            metadata['system']['subsets'] = {}
        if train_filter is not None:
            metadata['system']['subsets']['train'] = train_filter.prepare() if isinstance(train_filter,
                                                                                          entities.Filters) else train_filter
        if validation_filter is not None:
            metadata['system']['subsets']['validation'] = validation_filter.prepare() if isinstance(validation_filter,
                                                                                                    entities.Filters) else validation_filter
        return metadata

    @staticmethod
    def add_subset(model: entities.Model, subset_name: str, subset_filter: entities.Filters):
        """
        Adds a subset for a model, specifying a subset of the model's dataset that could be used for training or
        validation.

        :param dtlpy.entities.Model model: the model to which the subset should be added
        :param str subset_name: the name of the subset
        :param dtlpy.entities.Filters subset_filter: the filtering operation that this subset performs in the dataset.

        **Example**

        .. code-block:: python

            project.models.add_subset(model=model_entity, subset_name='train', subset_filter=dtlpy.Filters(field='dir', values='/train'))
            model_entity.metadata['system']['subsets']
                {'train': <dtlpy.entities.filters.Filters object at 0x1501dfe20>}

        """
        if 'system' not in model.metadata:
            model.metadata['system'] = dict()
        if 'subsets' not in model.metadata['system']:
            model.metadata['system']['subsets'] = dict()
        model.metadata['system']['subsets'][subset_name] = subset_filter.prepare()
        model.update(system_metadata=True)

    @staticmethod
    def delete_subset(model: entities.Model, subset_name: str):
        """
        Removes a subset from a model's metadata.

        :param dtlpy.entities.Model model: the model to which the subset should be added
        :param str subset_name: the name of the subset

        **Example**

        .. code-block:: python

            project.models.add_subset(model=model_entity, subset_name='train', subset_filter=dtlpy.Filters(field='dir', values='/train'))
            model_entity.metadata['system']['subsets']
                {'train': <dtlpy.entities.filters.Filters object at 0x1501dfe20>}
            project.models.delete_subset(model=model_entity, subset_name='train')
            model_entity.metadata['system']['subsets']
                {}

        """
        if model.metadata.get("system", dict()).get("subsets", dict()).get(subset_name) is None:
            logger.error(f"Model system metadata incomplete, could not delete subset {subset_name}.")
        else:
            _ = model.metadata['system']['subsets'].pop(subset_name)
            model.update(system_metadata=True)

    def create(
            self,
            model_name: str,
            dataset_id: str = None,
            labels: list = None,
            ontology_id: str = None,
            description: str = None,
            model_artifacts: List[entities.Artifact] = None,
            project_id=None,
            tags: List[str] = None,
            package: entities.Package = None,
            configuration: dict = None,
            status: str = None,
            scope: entities.EntityScopeLevel = entities.EntityScopeLevel.PROJECT,
            version: str = '1.0.0',
            input_type=None,
            output_type=None,
            train_filter: entities.Filters = None,
            validation_filter: entities.Filters = None,
            app: entities.App = None
    ) -> entities.Model:
        """
        Create a Model entity

        :param str model_name: name of the model
        :param str dataset_id: dataset id
        :param list labels: list of labels from ontology (must mach ontology id) can be a subset
        :param str ontology_id: ontology to connect to the model
        :param str description: description
        :param model_artifacts: optional list of dl.Artifact. Can be ItemArtifact, LocaArtifact or LinkArtifact
        :param str project_id: project that owns the model
        :param list tags: list of string tags
        :param package: optional - Package object
        :param dict configuration: optional - model configuration - dict
        :param str status: `str` of the optional values of
        :param str scope: the scope level of the model dl.EntityScopeLevel
        :param str version: version of the model
        :param str input_type: the file type the model expect as input (image, video, txt, etc)
        :param str output_type: dl.AnnotationType - the type of annotations the model produces (class, box segment, text, etc)
        :param dtlpy.entities.filters.Filters train_filter: Filters entity or a dictionary to define the items' scope in the specified dataset_id for the model train
        :param dtlpy.entities.filters.Filters validation_filter: Filters entity or a dictionary to define the items' scope in the specified dataset_id for the model validation
        :param dtlpy.entities.App app: App entity to connect the model to
        :return: Model Entity

        **Example**:

        .. code-block:: python

            project.models.create(model_name='model_name', dataset_id='dataset_id', labels=['label1', 'label2'], train_filter={filter: {$and: [{dir: "/10K short videos"}]},page: 0,pageSize: 1000,resource: "items"}})

        """

        if ontology_id is not None:
            # take labels from ontology
            ontologies = repositories.Ontologies(client_api=self._client_api)
            labels = [label.tag for label in ontologies.get(ontology_id=ontology_id).labels]

        if labels is None:
            # dont have to have labels. can use an empty list
            labels = list()

        if input_type is None:
            input_type = 'image'

        if output_type is None:
            output_type = entities.AnnotationType.CLASSIFICATION

        if package is None and self._package is None:
            raise exceptions.PlatformException('Must provide a Package or create from package.models')
        elif package is None:
            package = self._package

        # TODO need to remove the entire project id user interface - need to take it from dataset id (in BE)
        if project_id is None:
            if self._project is None:
                raise exceptions.PlatformException('Please provide project_id')
            project_id = self._project.id
        else:
            if project_id != self._project_id:
                if (isinstance(package, entities.Package) and not package.is_global) or \
                        (isinstance(package, entities.Dpk) and not package.scope != 'public'):
                    logger.warning(
                        "Note! you are specified project_id {!r} which is different from repository context: {!r}".format(
                            project_id, self._project_id))

        if model_artifacts is None:
            model_artifacts = []

        if not isinstance(model_artifacts, list):
            raise ValueError('`model_artifacts` must be a list of dl.Artifact entities')

        # create payload for request
        payload = {
            'packageId': package.id,
            'name': model_name,
            'projectId': project_id,
            'datasetId': dataset_id,
            'labels': labels,
            'artifacts': [artifact.to_json(as_artifact=True) for artifact in model_artifacts],
            'scope': scope,
            'version': version,
            'inputType': input_type,
            'outputType': output_type,
        }

        if app is not None:
            if not isinstance(package, entities.Dpk):
                raise ValueError('package must be a Dpk entity')
            if app.dpk_name != package.name or app.dpk_version != package.version:
                raise ValueError('App and package must be the same')
            component_name = None
            compute_config = None
            for model in package.components.models:
                if model['name'] == model_name:
                    component_name = model['name']
                    compute_config = model.get('computeConfigs', None)
                    break
            if component_name is None:
                raise ValueError('Model name not found in package')
            payload['app'] = {
                "id": app.id,
                "componentName": component_name,
                "dpkName": package.name,
                "dpkVersion": package.version
            }
            if compute_config is not None:
                payload['app']['computeConfig'] = compute_config

        if configuration is not None:
            payload['configuration'] = configuration

        if tags is not None:
            payload['tags'] = tags

        if description is not None:
            payload['description'] = description

        if status is not None:
            payload['status'] = status

        if train_filter or validation_filter:
            metadata = self._set_model_filter(metadata={},
                                              train_filter=train_filter,
                                              validation_filter=validation_filter)
            payload['metadata'] = metadata

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/ml/models',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        model = entities.Model.from_json(_json=response.json(),
                                         client_api=self._client_api,
                                         project=self._project,
                                         package=package)

        return model

    def clone(self,
              from_model: entities.Model,
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
              wait=True,
              ) -> entities.Model:
        """
        Clones and creates a new model out of existing one

        :param from_model: existing model to clone from
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
        :param bool wait: `bool` wait for model to be ready
        :return: dl.Model which is a clone version of the existing model
        """
        from_json = {"name": model_name,
                     "packageId": from_model.package_id,
                     "configuration": from_model.configuration,
                     "outputType": from_model.output_type,
                     "inputType": from_model.input_type}
        if project_id is None:
            if dataset is not None:
                # take dataset project
                project_id = dataset.project.id
            else:
                # take model's project
                project_id = self.project.id
        from_json['projectId'] = project_id
        if dataset is not None:
            if labels is None:
                labels = list(dataset.labels_flat_dict.keys())
            from_json['datasetId'] = dataset.id
        if labels is not None:
            from_json['labels'] = labels
            # if there are new labels - pop the mapping from the original
            _ = from_json['configuration'].pop('id_to_label_map', None)
            _ = from_json['configuration'].pop('label_to_id_map', None)
        if configuration is not None:
            from_json['configuration'].update(configuration)
        if description is not None:
            from_json['description'] = description
        if tags is not None:
            from_json['tags'] = tags
        if scope is not None:
            from_json['scope'] = scope
        if status is not None:
            from_json['status'] = status

        metadata = self._set_model_filter(metadata={},
                                          train_filter=train_filter if train_filter is not None else from_model.metadata.get(
                                              'system', {}).get('subsets', {}).get('train', None),
                                          validation_filter=validation_filter if validation_filter is not None else from_model.metadata.get(
                                              'system', {}).get('subsets', {}).get('validation', None))
        if metadata:
            from_json['metadata'] = metadata
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/ml/models/{}/clone'.format(from_model.id),
                                                         json_req=from_json)
        if not success:
            raise exceptions.PlatformException(response)
        new_model = entities.Model.from_json(_json=response.json(),
                                             client_api=self._client_api,
                                             project=self._project,
                                             package=from_model._package)
        if wait:
            new_model = self.wait_for_model_ready(model=new_model)
        return new_model

    def wait_for_model_ready(self, model: entities.Model):
        """
        Wait for model to be ready

        :param model: Model entity
        """
        sleep_time = MIN_INTERVAL
        while model.status == entities.ModelStatus.CLONING:
            model = self.get(model_id=model.id)
            time.sleep(sleep_time)
            sleep_time = min(sleep_time * BACKOFF_FACTOR, MAX_INTERVAL)
            time.sleep(sleep_time)
        return model

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/models".format(self.project.id))

    def open_in_web(self, model=None, model_id=None):
        """
        Open the model in web platform

        :param model: model entity
        :param str model_id: model id
        """
        if model is not None:
            model.open_in_web()
        elif model_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(model_id) + '/main')
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def delete(self, model: entities.Model = None, model_name=None, model_id=None):
        """
        Delete Model object

        :param model: Model entity to delete
        :param str model_name: delete by model name
        :param str model_id: delete by model id
        :return: True
        :rtype: bool
        """
        # get id and name
        if model_id is None:
            if model is not None:
                model_id = model.id
            elif model_name is not None:
                model = self.get(model_name=model_name)
                model_id = model.id
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Must input at least one parameter to models.delete')

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/ml/models/{}".format(model_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self,
               model: entities.Model,
               system_metadata: bool = False) -> entities.Model:
        """
        Update Model changes to platform

        :param model: Model entity
        :param bool system_metadata: True, if you want to change metadata system
        :return: Model entity
        """
        # payload
        payload = model.to_json()

        # url
        url_path = '/ml/models/{}'.format(model.id)
        if system_metadata:
            url_path += '?system=true'

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Model.from_json(_json=response.json(),
                                        client_api=self._client_api,
                                        project=self._project,
                                        package=model._package)

    def train(self, model_id: str, service_config=None):
        """
        Train the model in the cloud. This will create a service and will run the adapter's train function as an execution

        :param model_id: id of the model to train
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :return:
        """
        payload = dict()
        if service_config is not None:
            payload['serviceConfig'] = service_config
        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model_id}/train",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        return entities.Execution.from_json(_json=response.json(),
                                            client_api=self._client_api,
                                            project=self._project)

    def evaluate(self, model_id: str, dataset_id: str, filters: entities.Filters = None, service_config=None):
        """
        Evaluate Model, provide data to evaluate the model on You can also provide specific config for the deployed service

        :param str model_id: Model id to predict
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :param str dataset_id: ID of the dataset to evaluate
        :param entities.Filters filters: dl.Filter entity to run the predictions on
        :return:
        """

        payload = {'input': {'datasetId': dataset_id}}
        if service_config is not None:
            payload['config'] = {'serviceConfig': service_config}
        if filters is None:
            filters = entities.Filters()
        if filters is not None:
            payload['input']['datasetQuery'] = filters.prepare()
        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model_id}/evaluate",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        return entities.Execution.from_json(_json=response.json(),
                                            client_api=self._client_api,
                                            project=self._project)

    def predict(self, model, item_ids, dataset_id=None):
        """
        Run model prediction with items

        :param model: dl.Model entity to run the prediction.
        :param item_ids: a list of item id to run the prediction.
        :param dataset_id: a dataset id to run the prediction.
        :return:
        """
        if len(model.metadata['system'].get('deploy', {}).get('services', [])) == 0:
            # no services for model
            raise ValueError("Model doesnt have any associated services. Need to deploy before predicting")
        if item_ids is None and dataset_id is None:
            raise ValueError("Need to provide either item_ids or dataset_id")
        payload_input = {}
        if item_ids is not None:
            payload_input['itemIds'] = item_ids
        if dataset_id is not None:
            payload_input['datasetId'] = dataset_id
        payload = {'input': payload_input,
                   'config': {'serviceId': model.metadata['system']['deploy']['services'][0]}}

        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model.id}/predict",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        return entities.Execution.from_json(_json=response.json(),
                                            client_api=self._client_api,
                                            project=self._project)

    def embed(self, model, item_ids=None, dataset_id=None):
        """
        Run model embed with items

        :param model: dl.Model entity to run the prediction.
        :param item_ids: a list of item id to run the embed.
        :param dataset_id: a dataset id to run the embed.
        :return: Execution
        :rtype: dtlpy.entities.execution.Execution
        """
        if len(model.metadata['system'].get('deploy', {}).get('services', [])) == 0:
            # no services for model
            raise ValueError("Model doesnt have any associated services. Need to deploy before predicting")
        if item_ids is None and dataset_id is None:
            raise ValueError("Need to provide either item_ids or dataset_id")
        payload_input = {}
        if item_ids is not None:
            payload_input['itemIds'] = item_ids
        if dataset_id is not None:
            payload_input['datasetId'] = dataset_id
        payload = {'input': payload_input,
                   'config': {'serviceId': model.metadata['system']['deploy']['services'][0]}}

        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model.id}/embed",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        return entities.Execution.from_json(_json=response.json(),
                                            client_api=self._client_api,
                                            project=self._project)

    def embed_datasets(self, model, dataset_ids, attach_trigger=False):
        """
        Run model embed with datasets

        :param model: dl.Model entity to run the prediction.
        :param dataset_ids: a list of dataset id to run the embed.
        :param attach_trigger: bool, if True will activate the trigger
        :return:
        """
        if len(model.metadata['system'].get('deploy', {}).get('services', [])) == 0:
            # no services for model
            raise ValueError("Model doesnt have any associated services. Need to deploy before predicting")
        if dataset_ids is None:
            raise ValueError("Need to provide either dataset_id")
        payload = {'datasetIds': dataset_ids,
                   'config': {'serviceId': model.metadata['system']['deploy']['services'][0]},
                   'attachTrigger': attach_trigger
                   }

        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model.id}/embed/datasets",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)
        command = entities.Command.from_json(_json=response.json(),
                                             client_api=self._client_api)
        command = command.wait()
        return command

    def deploy(self, model_id: str, service_config=None) -> entities.Service:
        """
        Deploy a trained model. This will create a service that will execute predictions

        :param model_id: id of the model to deploy
        :param dict service_config : Service object as dict. Contains the spec of the default service to create.
        :return: dl.Service: the deployed service
        """
        payload = dict()
        if service_config is not None:
            payload['serviceConfig'] = service_config
        success, response = self._client_api.gen_request(req_type="post",
                                                         path=f"/ml/models/{model_id}/deploy",
                                                         json_req=payload)
        if not success:
            raise exceptions.PlatformException(response)

        return entities.Service.from_json(_json=response.json(),
                                          client_api=self._client_api,
                                          project=self._project,
                                          package=self._package)


class Metrics:
    def __init__(self, client_api, model=None, model_id=None):
        self._client_api = client_api
        self._model_id = model_id
        self._model = model

    @property
    def model(self):
        return self._model

    def create(self, samples, dataset_id) -> bool:
        """
        Add Samples for model analytics and metrics

        :param samples: list of dl.PlotSample - must contain: model_id, figure, legend, x, y
        :param model_id: model id to save samples on
        :param dataset_id:
        :return: bool: True if success
        """
        if not isinstance(samples, list):
            samples = [samples]

        payload = list()
        for sample in samples:
            _json = sample.to_json()
            _json['modelId'] = self.model.id
            _json['datasetId'] = dataset_id
            payload.append(_json)
        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/ml/metrics/publish',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return True

    def _list(self, filters: entities.Filters):
        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path='/ml/metrics/query',
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Model]:
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, sample in enumerate(response_items):
            jobs[i_service] = pool.submit(entities.PlotSample,
                                          **{'x': sample.get('data', dict()).get('x', None),
                                             'y': sample.get('data', dict()).get('y', None),
                                             'legend': sample.get('legend', ''),
                                             'figure': sample.get('figure', '')})

        # get all results
        results = [j.result() for j in jobs]
        # return good jobs
        return miscellaneous.List(results)

    def list(self, filters=None) -> entities.PagedEntities:
        """
        List Samples for model analytics and metrics

        :param filters: dl.Filter query entity
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.METRICS)
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.METRICS:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.METRICS. Got: {!r}'.format(filters.resource))
        if self._model is not None:
            filters.add(field='modelId', values=self._model.id)
        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged
