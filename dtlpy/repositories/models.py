import importlib.util
import logging
import os
from shutil import copyfile
from typing import Union, List

from .. import entities, repositories, exceptions, miscellaneous, assets, services

logger = logging.getLogger(name=__name__)

DEFAULT_ENTRY_POINT = 'adapter_model.py'


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

        :param checkout:
        :param model_id:
        :param model_name:
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
            jobs[i_service] = pool.apply_async(entities.Model._protected_from_json,
                                               kwds={'client_api': self._client_api,
                                                     '_json': service,
                                                     'project': self._project})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        url = '/query/machine-learning'
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
        :return:
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.MODEL)
        if self._project is not None:
            filters.add(field='projectId', values=self._project.id)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=filters.page,
                                       page_size=filters.page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    def build(self, model: entities.Model, local_path=None, from_local=None):
        """
        :param model: Model entity
        :param from_local: bool. use current directory to build
        :param local_path: local path of the model (if from_local=False - codebase will be downloaded)

        :return:
        """
        if model.codebase is None or model.codebase.type != entities.PackageCodebaseType.ITEM:
            raise NotImplementedError('This method is not implemented for {} codebase yet'.format(model.codebase.type))

        if from_local is None:
            from_local = False

        if from_local:
            # no need to download codebase
            if local_path is None:
                path = os.getcwd()
            else:
                path = local_path

        else:
            # download codebase locally
            if local_path is None:
                local_path = os.path.join(
                    services.service_defaults.DATALOOP_PATH,
                    "models",
                    model.name)

            codebase_id = model.codebase.codebase_id
            project = self._project if self._project is not None else model.project
            path = project.codebases.unpack(codebase_id=codebase_id, local_path=local_path)

        # load module from path
        entry_point = os.path.join(path, model.entry_point)
        spec = importlib.util.spec_from_file_location("AdapterModel", entry_point)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        adapter_model = foo.AdapterModel
        return adapter_model(model_entity=model)

    def push(
            self,
            model: entities.Model,
            src_path: str = None,
            entry_point: str = DEFAULT_ENTRY_POINT,
            codebase: entities.ItemCodebase = None,
    ):
        """
        Uploads and updates codebase to Model

        :param model: Model entity
        :param src_path: codebase location (path to directory of the code). if None pwd will be taken
        :param entry_point: relative path to the module where `AdapterModel` class is defined
        :param codebase: `dl.PackageCodebase' object - representing the model code  if None new will be created from src_path
        :return:
        """

        # get or create codebase
        if codebase is None:
            if isinstance(model.codebase.type, entities.PackageCodebaseType.ITEM):
                raise exceptions.PlatformException(
                    error='400',
                    message='Cant change codebase type implicitly. Please use codebase argument with dl.ItemCodebase')
            if src_path is None:
                src_path = os.getcwd()
                logger.warning('No src_path is given, getting model information from cwd: {}'.format(src_path))
            if not os.path.isfile(os.path.join(src_path, entry_point)):
                raise ValueError('entry point not found. filepath: {}'.format(os.path.join(src_path, entry_point)))
            codebase_id = model.codebases.pack(directory=src_path).id
            codebase = entities.ItemCodebase(codebase_id=codebase_id)

        model.codebase = codebase
        return model.update()

    def create(self,
               # offline mode
               model_name: str,
               description: str = None,
               output_type: str = None,
               input_type: str = None,
               is_global: bool = None,
               checkout: bool = False,
               tags: List[str] = None,
               # online mode
               codebase: Union[entities.GitCodebase,
                               entities.ItemCodebase,
                               entities.FilesystemCodebase,
                               entities.LocalCodebase] = None,
               src_path: str = None,
               entry_point: str = None,
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
        :param entry_point: location on the AdapterModel class

        :return: Model Entity
        """

        if self._project is None:
            raise exceptions.PlatformException('400', 'Repository must have a project to perform this action')

        if self._project.org is not None:
            org_id = self._project.org['id']
        else:
            raise exceptions.PlatformException('Cannot create model in a project without an org')

        payload = dict(
            orgId=org_id,
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
            payload['is_global'] = is_global

        if codebase is None:
            if src_path is None:
                src_path = os.getcwd()
            codebase = entities.LocalCodebase(local_path=src_path)

        payload['codebase'] = codebase.to_json()
        payload['entryPoint'] = entry_point if entry_point is not None else DEFAULT_ENTRY_POINT

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
    def generate(src_path=None):
        """
        Generate new model environment

        :return:
        """
        # src path
        if src_path is None:
            src_path = os.getcwd()
        if not os.path.isfile(os.path.join(src_path, '.gitignore')):
            copyfile(assets.paths.ASSETS_GITIGNORE_FILEPATH, os.path.join(src_path, '.gitignore'))
        copyfile(assets.paths.ASSETS_ADAPTER_MODEL_FILEPATH, os.path.join(src_path, assets.paths.ADAPTER_MODEL))
        logger.info('Successfully generated model')

    def __get_from_cache(self):
        model = self._client_api.state_io.get('model')
        if model is not None:
            model = entities.Model.from_json(_json=model, client_api=self._client_api, project=self._project)
        return model

    def checkout(self, model: entities.Model = None, model_id=None, model_name=None):
        """
        Checkout as model

        :param model_id:
        :param model:
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
