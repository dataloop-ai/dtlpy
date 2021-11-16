import importlib.util
import logging
import os
import sys
from shutil import copyfile
from typing import Union, List

from .. import entities, repositories, exceptions, miscellaneous, assets, services, ml

logger = logging.getLogger(name=__name__)

DEFAULT_ENTRY_POINT = 'model_adapter.py'
DEFAULT_CLASS_NAME = 'ModelAdapter'


class Models:
    """
    Models Repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self._client_api).get()
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "project". need to set a Project entity or use project.models repository')
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def get(self, model_name=None, model_id=None, checkout=False, fetch=None) -> entities.Model:
        """
        Get model object

        :param model_name:
        :param model_id:
        :param checkout: bool
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :return: model object
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if model_name is None and model_id is None:
            model = self.__get_from_cache()
            if model is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Model was found, must checkout or provide an identifier in inputs')
        elif fetch:
            if model_id is not None:
                success, response = self._client_api.gen_request(
                    req_type="get",
                    path="/models/{}".format(model_id))
                if not success:
                    raise exceptions.PlatformException(response)
                model = entities.Model.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 project=self._project)
                # verify input model name is same as the given id
                if model_name is not None and model.name != model_name:
                    logger.warning(
                        "Mismatch found in models.get: model_name is different then model.name: {!r} != {!r}".format(
                            model_name,
                            model.name))
            elif model_name is not None:
                models = self.list(entities.Filters(resource=entities.FiltersResource.MODEL,
                                                    field='name',
                                                    values=model_name))
                if models.items_count == 0:
                    raise exceptions.PlatformException(
                        error='404',
                        message='Model not found. Name: {}'.format(model_name))
                elif models.items_count > 1:
                    raise exceptions.PlatformException(
                        error='400',
                        message='More than one file found by the name of: {}'.format(model_name))
                model = models.items[0]
            else:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Model was found, must checkout or provide an identifier in inputs')
        else:
            model = entities.Model.from_json(_json={'id': model_id,
                                                    'name': model_name},
                                             client_api=self._client_api,
                                             project=self._project,
                                             is_fetched=False)

        if checkout:
            self.checkout(model=model)
        return model

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Model]:
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, service in enumerate(response_items):
            jobs[i_service] = pool.submit(entities.Model._protected_from_json,
                                          **{'client_api': self._client_api,
                                             '_json': service,
                                             'project': self._project})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        url = '/models/query'
        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None) -> entities.PagedEntities:
        """
        List project models
        :param filters: Filters entity or a dictionary containing filters parameters
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.MODEL)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.MODEL:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.MODEL. Got: {!r}'.format(filters.resource))
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def build(self, model: entities.Model, local_path=None, from_local=None) -> ml.BaseModelAdapter:
        """
        :param model: Model entity
        :param local_path: local path of the model (if from_local=False - codebase will be downloaded)
        :param from_local: bool. use current directory to build

        :return:dl.BaseModelAdapter
        """

        if model.codebase is None:
            raise exceptions.PlatformException(error='2001',
                                               message="Model {!r} has no codebase. unable to build adapter".format(
                                                   model.name))

        if from_local is None:
            from_local = model.codebase.is_local

        if local_path is None:
            if model.codebase.is_local:
                local_path = model.codebase.local_path
            else:
                local_path = os.path.join(services.service_defaults.DATALOOP_PATH, "models")

        if not from_local:
            # Not local => download codebase
            if model.codebase.is_local:
                raise RuntimeError("using local codebase: {}. Can not use from_local=False".
                                   format(model.codebase.to_json()))
            if isinstance(model.codebase, entities.ItemCodebase):
                codebase_id = model.codebase.item_id
                project = self._project if self._project is not None else model.project
                local_path = project.codebases.unpack(codebase_id=codebase_id,
                                                      local_path=local_path)
            elif isinstance(model.codebase, entities.GitCodebase):
                local_path = model.codebases.unpack(codebase=model.codebase,
                                                    local_path=local_path)
            else:
                raise NotImplementedError(
                    'download not implemented for {} codebase yet. Build failed'.format(model.codebase.type))

        sys.path.append(local_path)  # TODO: is it the best way to use the imports?
        # load module from path
        entry_point = os.path.join(local_path, model.entry_point)
        class_name = model.class_name
        if not os.path.isfile(entry_point):
            raise ValueError('Model entry point file is missing: {}'.format(entry_point))
        spec = importlib.util.spec_from_file_location(class_name, entry_point)
        if spec is None:
            raise ValueError('Cant load class ModelAdapter from entry point: {}'.format(entry_point))
        adapter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter_module)
        model_adapter_cls = getattr(adapter_module, class_name)
        model_adapter = model_adapter_cls(model_entity=model)
        logger.info('Model adapter loaded successfully!')
        return model_adapter

    def push(
            self,
            model: entities.Model,
            src_path: str = None,
            entry_point: str = DEFAULT_ENTRY_POINT,
            class_name: str = DEFAULT_CLASS_NAME,
            codebase: entities.ItemCodebase = None,
    ):
        """
        Uploads and updates codebase to Model

        :param model: Model entity
        :param src_path: codebase location (path to directory of the code). if None pwd will be taken
        :param entry_point: relative path to the module where model adapter class is defined
        :param class_name: name of the adapter class in entry point. default: ModelAdapter
        :param codebase: `dl.Codebase` object - representing the model code  if None new will be created from src_path

        :return:
        """

        # get or create codebase
        if codebase is None:
            if isinstance(model.codebase, entities.ItemCodebase):
                raise exceptions.PlatformException(
                    error='400',
                    message='Cant change codebase type implicitly. Please use codebase argument with dl.ItemCodebase')
            if src_path is None:
                src_path = os.getcwd()
                logger.warning('No src_path is given, getting model information from cwd: {}'.format(src_path))
            # sanity checks
            if not os.path.isfile(os.path.join(src_path, entry_point)):
                raise exceptions.PlatformException(
                    error='400',
                    message='Entry point not found. filepath: {}'.format(os.path.join(src_path, entry_point)))
            codebase = model.codebases.pack(directory=src_path)

        model.codebase = codebase
        return self.update(model)

    def create(self,
               # offline mode
               model_name: str,
               description: str = None,
               output_type: entities.ModelOutputType = None,
               input_type: entities.ModelInputType = None,
               is_global: bool = None,
               checkout: bool = False,
               tags: List[str] = None,
               # online mode
               codebase: Union[entities.GitCodebase,
                               entities.ItemCodebase,
                               entities.FilesystemCodebase,
                               entities.LocalCodebase] = None,
               src_path: str = None,
               entry_point: str = DEFAULT_ENTRY_POINT,
               class_name: str = DEFAULT_CLASS_NAME,
               ) -> entities.Model:
        """
        Create and return a Model entity in platform
        If "model" is given - default values will be taken from model information
        Passed params will override default values
        If any of the "online mode" params are entered - codebase will be pushed after creation

        For offline mode:
        :param model_name: name of model
        :param description: model description
        :param output_type: model output type (annotation type)
        :param input_type: model input mimetype
        :param is_global: is model global
        :param checkout: checkout model to local state
        :param tags: list of string tags
        For online mode
        :param codebase: optional - model codebase
        :param src_path: codebase location. if None no codebase will be pushed
        :param entry_point: location of the model adapter class
        :param class_name: Name of the model adapter class, default is ModelAdapter

        :return: Model Entity
        """

        if self._project is None:
            raise exceptions.PlatformException('400', 'Repository must have a project to perform this action')

        payload = dict(
            projectId=self._project.id,
            name=model_name
        )

        if input_type is not None:
            payload['inputType'] = input_type

        if output_type is not None:
            payload['outputType'] = output_type

        if description is not None:
            payload['description'] = description

        if tags is not None:
            payload['tags'] = tags

        if is_global is not None:
            payload['global'] = is_global

        if codebase is None:
            if src_path is None:
                src_path = os.getcwd()
            codebase = entities.LocalCodebase(local_path=src_path)

        payload['codebase'] = codebase.to_json()
        payload['entryPoint'] = entry_point
        payload['className'] = class_name

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/models',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        model = entities.Model.from_json(_json=response.json(),
                                         client_api=self._client_api,
                                         project=self._project)

        if checkout:
            self.checkout(model=model)
        # return entity
        return model

    def delete(self, model: entities.Model = None, model_name=None, model_id=None):
        """
        Delete Model object

        :param model:
        :param model_name:
        :param model_id:
        :return: True
        """
        # get id and name
        if model_name is None or model_id is None:
            if model is None:
                model = self.get(model_id=model_id, model_name=model_name)
            model_id = model.id

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/models/{}".format(model_id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, model: entities.Model) -> entities.Model:
        """
        Update Model changes to platform

        :param model:
        :return: Model entity
        """
        # payload
        payload = model.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/models/{}'.format(model.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Model.from_json(_json=response.json(),
                                        client_api=self._client_api,
                                        project=self._project)

    @staticmethod
    def generate(src_path=None,
                 entry_point=DEFAULT_ENTRY_POINT,
                 overwrite=False):
        """
        Generate new model adapter file
        :param src_path: `str` path where to create te model_adapter file (if None uses current working dir)
        :param entry_point: `str` name of the python module to create (if None uses model_adapter.py as default)
        :param overwrite:  `bool` whether to over write an existing file (default False)

        :return: path where the adapter was created
        """
        # src path
        if src_path is None:
            src_path = os.getcwd()

        local_path = os.path.join(src_path, entry_point)
        if os.path.exists(local_path):
            if overwrite:
                logger.warning("Overwriting {} with a blank template".format(local_path))
            else:
                logger.error("can not overwrite existing model adapter at {}".format(local_path))
                return None

        if not os.path.isfile(os.path.join(src_path, '.gitignore')):
            copyfile(assets.paths.ASSETS_GITIGNORE_FILEPATH, os.path.join(src_path, '.gitignore'))
        copyfile(assets.paths.ASSETS_MODEL_ADAPTER_FILEPATH, local_path)
        logger.info('Successfully generated model adapter at {}'.format(local_path))
        return local_path

    def __get_from_cache(self):
        model = self._client_api.state_io.get('model')
        if model is not None:
            model = entities.Model.from_json(_json=model, client_api=self._client_api, project=self._project)
        return model

    def checkout(self, model: entities.Model = None, model_id=None, model_name=None):
        """
        Checkout as model
        :param model:
        :param model_id:
        :param model_name:
        :return:
        """
        if model is None:
            model = self.get(model_id=model_id, model_name=model_name)
        self._client_api.state_io.put('model', model.to_json())
        logger.info("Checked out to model {}".format(model.name))

    def revisions(self, model: entities.Model = None, model_id=None):
        """
        Get model revisions history

        :param model: Package entity
        :param model_id: package id
        """
        if model is None and model_id is None:
            raise exceptions.PlatformException(
                error='400',
                message='must provide an identifier in inputs: "model" or "model_id"')

        if model is not None:
            model_id = model.id

        success, response = self._client_api.gen_request(
            req_type="get",
            path="/models/{}/revisions".format(model_id))

        if not success:
            raise exceptions.PlatformException(response)
        return response.json()
