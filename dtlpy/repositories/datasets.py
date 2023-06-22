"""
Datasets Repository
"""

import os
import sys
import copy
import tqdm
import logging
from urllib.parse import urlencode

from .. import entities, repositories, miscellaneous, exceptions, services, PlatformException, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Datasets:
    """
    Datasets Repository

    The Datasets class allows the user to manage datasets. Read more about datasets in our `documentation <https://dataloop.ai/docs/dataset>`_ and `SDK documentation <https://dataloop.ai/docs/sdk-create-dataset>`_.
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # try get checkout
            project = self._client_api.state_io.get('project')
            if project is not None:
                self._project = entities.Project.from_json(_json=project, client_api=self._client_api)
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Project entity in Datasets repository.'
                        ' Please checkout or set a project')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ###########
    # methods #
    ###########
    def __get_from_cache(self) -> entities.Dataset:
        dataset = self._client_api.state_io.get('dataset')
        if dataset is not None:
            dataset = entities.Dataset.from_json(_json=dataset,
                                                 client_api=self._client_api,
                                                 datasets=self,
                                                 project=self._project)
        return dataset

    def __get_by_id(self, dataset_id) -> entities.Dataset:
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/datasets/{}'.format(dataset_id))
        if dataset_id is None or dataset_id == '':
            raise exceptions.PlatformException('400', 'Please checkout a dataset')

        if success:
            dataset = entities.Dataset.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 datasets=self,
                                                 project=self._project)
        else:
            raise exceptions.PlatformException(response)
        return dataset

    def __get_by_identifier(self, identifier=None) -> entities.Dataset:
        datasets = self.list()
        datasets_by_name = [dataset for dataset in datasets if identifier in dataset.name or identifier in dataset.id]
        if len(datasets_by_name) == 1:
            return datasets_by_name[0]
        elif len(datasets_by_name) > 1:
            raise Exception('Multiple datasets with this name exist')
        else:
            raise Exception("Dataset not found")

    def _bulid_folder_filter(self, folder_path, filters=None):
        if filters is None:
            filters = entities.Filters(user_query=False)
        if not folder_path.startswith('/'):
            folder_path = '/' + folder_path
        filters.add(field='dir', values=folder_path + '*')
        return filters

    @property
    def platform_url(self):
        return self._client_api._get_resource_url("projects/{}/datasets".format(self.project.id))

    def open_in_web(self,
                    dataset_name: str = None,
                    dataset_id: str = None,
                    dataset: entities.Dataset = None):
        """
        Open the dataset in web platform.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str dataset_name: The Name of the dataset
        :param str dataset_id: The Id of the dataset
        :param dtlpy.entities.dataset.Dataset dataset: dataset object

        **Example**:

        .. code-block:: python

            project.datasets.open_in_web(dataset_id='dataset_id')
        """
        if dataset_name is not None:
            dataset = self.get(dataset_name=dataset_name)
        if dataset is not None:
            dataset.open_in_web()
        elif dataset_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(dataset_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def checkout(self,
                 identifier: str = None,
                 dataset_name: str = None,
                 dataset_id: str = None,
                 dataset: entities.Dataset = None):
        """
        Checkout (switch) to a dataset to work on it.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset_id, dataset_name.

        :param str identifier: project name or partial id that you wish to switch
        :param str dataset_name: The Name of the dataset
        :param str dataset_id: The Id of the dataset
        :param dtlpy.entities.dataset.Dataset dataset: dataset object

        **Example**:

        .. code-block:: python

            project.datasets.checkout(dataset_id='dataset_id')
        """
        if dataset is None:
            if dataset_id is not None or dataset_name is not None:
                try:
                    dataset = self.project.datasets.get(dataset_name=dataset_name, dataset_id=dataset_id)
                except exceptions.MissingEntity:
                    dataset = self.get(dataset_id=dataset_id, dataset_name=dataset_name)
            elif identifier is not None:
                dataset = self.__get_by_identifier(identifier=identifier)
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Must provide partial/full id/name to checkout')
        self._client_api.state_io.put('dataset', dataset.to_json())
        logger.info('Checked out to dataset {}'.format(dataset.name))

    @_api_reference.add(path='/datasets', method='get')
    def list(self, name=None, creator=None) -> miscellaneous.List[entities.Dataset]:
        """
        List all datasets.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str name: list by name
        :param str creator: list by creator
        :return: List of datasets
        :rtype: list

        **Example**:

        .. code-block:: python

            datasets = project.datasets.list(name='name')
        """
        url = '/datasets'

        query_params = {
            'name': name,
            'creator': creator
        }

        if self._project is not None:
            query_params['projects'] = self.project.id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if success:
            pool = self._client_api.thread_pools('entity.create')
            datasets_json = response.json()
            jobs = [None for _ in range(len(datasets_json))]
            # return triggers list
            for i_dataset, dataset in enumerate(datasets_json):
                jobs[i_dataset] = pool.submit(entities.Dataset._protected_from_json,
                                              **{'client_api': self._client_api,
                                                 '_json': dataset,
                                                 'datasets': self,
                                                 'project': self.project})

            # get all results
            results = [j.result() for j in jobs]
            # log errors
            _ = [logger.warning(r[1]) for r in results if r[0] is False]
            # return good jobs
            datasets = miscellaneous.List([r[1] for r in results if r[0] is True])
        else:
            raise exceptions.PlatformException(response)
        return datasets

    @_api_reference.add(path='/datasets/{id}', method='get')
    def get(self,
            dataset_name: str = None,
            dataset_id: str = None,
            checkout: bool = False,
            fetch: bool = None
            ) -> entities.Dataset:
        """
        Get dataset by name or id.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset_id, dataset_name.

        :param str dataset_name: optional - search by name
        :param str dataset_id: optional - search by id
        :param bool checkout: set the dataset as a default dataset object (cookies)
        :param bool fetch: optional - fetch entity from platform (True), default taken from cookie
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = project.datasets.get(dataset_id='dataset_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if dataset_id is None and dataset_name is None:
            dataset = self.__get_from_cache()
            if dataset is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='No checked-out Dataset was found, must checkout or provide an identifier in inputs')
        elif fetch:
            if dataset_id is not None and dataset_id != '':
                dataset = self.__get_by_id(dataset_id)
                # verify input dataset name is same as the given id
                if dataset_name is not None and dataset.name != dataset_name:
                    logger.warning(
                        "Mismatch found in datasets.get: dataset_name is different then dataset.name: "
                        "{!r} != {!r}".format(
                            dataset_name,
                            dataset.name))
            elif dataset_name is not None:
                datasets = self.list(name=dataset_name)
                if not datasets:
                    # empty list
                    raise exceptions.PlatformException('404', 'Dataset not found. Name: {!r}'.format(dataset_name))
                    # dataset = None
                elif len(datasets) > 1:
                    raise exceptions.PlatformException('400', 'More than one dataset with same name.')
                else:
                    dataset = datasets[0]
            else:
                raise exceptions.PlatformException(
                    error='404',
                    message='No input and no checked-out found')
        else:
            dataset = entities.Dataset.from_json(_json={'id': dataset_id,
                                                        'name': dataset_id},
                                                 client_api=self._client_api,
                                                 datasets=self,
                                                 project=self._project,
                                                 is_fetched=False)
        assert isinstance(dataset, entities.Dataset)
        if checkout:
            self.checkout(dataset=dataset)
        return dataset

    @_api_reference.add(path='/datasets/{id}', method='delete')
    def delete(self,
               dataset_name: str = None,
               dataset_id: str = None,
               sure: bool = False,
               really: bool = False):
        """
        Delete a dataset forever!

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        **Example**:

        .. code-block:: python

            is_deleted = project.datasets.delete(dataset_id='dataset_id', sure=True, really=True)

        :param str dataset_name: optional - search by name
        :param str dataset_id: optional - search by id
        :param bool sure: Are you sure you want to delete?
        :param bool really: Really really sure?
        :return: True is success
        :rtype: bool
        """
        if sure and really:
            dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/datasets/{}'.format(dataset.id))
            if not success:
                raise exceptions.PlatformException(response)
            logger.info('Dataset {!r} was deleted successfully'.format(dataset.name))
            return True
        else:
            raise exceptions.PlatformException(
                error='403',
                message='Cant delete dataset from SDK. Please login to platform to delete')

    @_api_reference.add(path='/datasets/{id}', method='patch')
    def update(self,
               dataset: entities.Dataset,
               system_metadata: bool = False,
               patch: dict = None
               ) -> entities.Dataset:
        """
        Update dataset field.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :param bool system_metadata: True, if you want to change metadata system
        :param dict patch: Specific patch request
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = project.datasets.update(dataset='dataset_entity')
        """
        url_path = '/datasets/{}'.format(dataset.id)
        if system_metadata:
            url_path += '?system=true'

        if patch is None:
            patch = dataset.to_json()

        success, response = self._client_api.gen_request(req_type='patch',
                                                         path=url_path,
                                                         json_req=patch)
        if success:
            logger.info('Dataset was updated successfully')
            return dataset
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/datasets/{id}/directoryTree', method='get')
    def directory_tree(self,
                       dataset: entities.Dataset = None,
                       dataset_name: str = None,
                       dataset_id: str = None):
        """
        Get dataset's directory tree.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset, dataset_name, dataset_id.

        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :param str dataset_name: The Name of the dataset
        :param str dataset_id: The Id of the dataset
        :return: DirectoryTree

        **Example**:

        .. code-block:: python
            directory_tree = dataset.directory_tree
            directory_tree = project.datasets.directory_tree(dataset='dataset_entity')
        """
        if dataset is None and dataset_name is None and dataset_id is None:
            raise exceptions.PlatformException('400', 'Must provide dataset, dataset name or dataset id')
        if dataset_id is None:
            if dataset is None:
                dataset = self.get(dataset_name=dataset_name)
            dataset_id = dataset.id

        url_path = '/datasets/{}/directoryTree'.format(dataset_id)

        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url_path)

        if success:
            return entities.DirectoryTree(_json=response.json())
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/datasets/{id}/clone', method='post')
    def clone(self,
              dataset_id: str,
              clone_name: str,
              filters: entities.Filters = None,
              with_items_annotations: bool = True,
              with_metadata: bool = True,
              with_task_annotations_status: bool = True):
        """
        Clone a dataset. Read more about cloning datatsets and items in our `documentation <https://dataloop.ai/docs/clone-merge-dataset#cloned-dataset>`_ and `SDK documentation <https://dataloop.ai/docs/sdk-create-dataset#clone-dataset>`_.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str dataset_id: id of the dataset you wish to clone
        :param str clone_name: new dataset name
        :param dtlpy.entities.filters.Filters filters: Filters entity or a query dict
        :param bool with_items_annotations: true to clone with items annotations
        :param bool with_metadata: true to clone with metadata
        :param bool with_task_annotations_status: true to clone with task annotations' status
        :return: dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = project.datasets.clone(dataset_id='dataset_id',
                                  clone_name='dataset_clone_name',
                                  with_metadata=True,
                                  with_items_annotations=False,
                                  with_task_annotations_status=False)
        """
        if filters is None:
            filters = entities.Filters(user_query=False)
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(
                error='400',
                message='"filters" must be a dl.Filters entity. got: {!r}'.format(type(filters)))

        copy_filters = copy.deepcopy(filters)
        if copy_filters.has_field('hidden'):
            copy_filters.pop('hidden')

        payload = {
            "name": clone_name,
            "filter": copy_filters.prepare(),
            "cloneDatasetParams": {
                "withItemsAnnotations": with_items_annotations,
                "withMetadata": with_metadata,
                "withTaskAnnotationsStatus": with_task_annotations_status
            }
        }
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/clone'.format(dataset_id),
                                                         json_req=payload,
                                                         headers={'user_query': filters.user_query})

        if not success:
            raise exceptions.PlatformException(response)

        command = entities.Command.from_json(_json=response.json(),
                                             client_api=self._client_api)
        command = command.wait()

        if 'returnedModelId' not in command.spec:
            raise exceptions.PlatformException(error='400',
                                               message="returnedModelId key is missing in command response: {!r}"
                                               .format(response))
        return self.get(dataset_id=command.spec['returnedModelId'])

    @_api_reference.add(path='/datasets/merge', method='post')
    def merge(self,
              merge_name: str,
              dataset_ids: list,
              project_ids: str,
              with_items_annotations: bool = True,
              with_metadata: bool = True,
              with_task_annotations_status: bool = True,
              wait: bool = True):
        """
        Merge a dataset. See our `SDK docs <https://dataloop.ai/docs/sdk-create-dataset#merge-datasets>`_ for more information.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str merge_name: new dataset name
        :param list dataset_ids: list id's of the datatsets you wish to merge
        :param str project_ids: the project id that include the datasets
        :param bool with_items_annotations: true to merge with items annotations
        :param bool with_metadata: true to merge with metadata
        :param bool with_task_annotations_status: true to merge with task annotations' status
        :param bool wait: wait for the command to finish
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = project.datasets.merge(dataset_ids=['dataset_id1','dataset_id2'],
                                  merge_name='dataset_merge_name',
                                  with_metadata=True,
                                  with_items_annotations=False,
                                  with_task_annotations_status=False)
        """
        payload = {
            "name": merge_name,
            "datasetsIds": dataset_ids,
            "projectIds": project_ids,
            "mergeDatasetParams": {
                "withItemsAnnotations": with_items_annotations,
                "withMetadata": with_metadata,
                "withTaskAnnotationsStatus": with_task_annotations_status
            },
            'asynced': wait
        }
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/merge',
                                                         json_req=payload)

        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if 'mergeDatasetsConfiguration' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="mergeDatasetsConfiguration key is missing in command response: {}"
                                                   .format(response))
            return True
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/datasets/{id}/sync', method='post')
    def sync(self, dataset_id: str, wait: bool = True):
        """
        Sync dataset with external storage.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str dataset_id: The Id of the dataset to sync
        :param bool wait: wait for the command to finish
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = project.datasets.sync(dataset_id='dataset_id')
        """

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/sync'.format(dataset_id))

        if success:
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=self._client_api)
            if not wait:
                return command
            command = command.wait(timeout=0)
            if 'datasetId' not in command.spec:
                raise exceptions.PlatformException(error='400',
                                                   message="datasetId key is missing in command response: {}"
                                                   .format(response))
            return True
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/datasets', method='post')
    def create(self,
               dataset_name: str,
               labels=None,
               attributes=None,
               ontology_ids=None,
               driver: entities.Driver = None,
               driver_id: str = None,
               checkout: bool = False,
               expiration_options: entities.ExpirationOptions = None,
               index_driver: entities.IndexDriver = None,
               recipe_id: str = None
               ) -> entities.Dataset:
        """
        Create a new dataset

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str dataset_name: The Name of the dataset
        :param list labels: dictionary of {tag: color} or list of label entities
        :param list attributes: dataset's ontology's attributes
        :param list ontology_ids: optional - dataset ontology
        :param dtlpy.entities.driver.Driver driver: optional - storage driver Driver object or driver name
        :param str driver_id: optional - driver id
        :param bool checkout: set the dataset as a default dataset object (cookies)
        :param ExpirationOptions expiration_options: dl.ExpirationOptions object that contain definitions for dataset like MaxItemDays
        :param str index_driver: dl.IndexDriver, dataset driver version
        :param str recipe_id: optional - recipe id
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = project.datasets.create(dataset_name='dataset_name', ontology_ids='ontology_ids')
        """
        create_default_recipe = True
        if any([labels, attributes, ontology_ids, recipe_id]):
            create_default_recipe = False

        # labels to list
        if labels is not None:
            if not isinstance(labels, list):
                labels = [labels]
            if not all(isinstance(label, entities.Label) for label in labels):
                labels = entities.Dataset.serialize_labels(labels)
        else:
            labels = list()

        # get creator from token
        payload = {'name': dataset_name,
                   'projects': [self.project.id],
                   'createDefaultRecipe': create_default_recipe
                   }

        if driver_id is None and driver is not None:
            if isinstance(driver, entities.Driver):
                driver_id = driver.id
            elif isinstance(driver, str):
                driver_id = self.project.drivers.get(driver_name=driver).id
            else:
                raise exceptions.PlatformException(
                    error=400,
                    message='Input arg "driver" must be Driver object or a string driver name. got type: {!r}'.format(
                        type(driver)))
        if driver_id is not None:
            payload['driver'] = driver_id

        if expiration_options:
            payload['expirationOptions'] = expiration_options.to_json()
        if index_driver is not None:
            payload['indexDriver'] = index_driver

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets',
                                                         json_req=payload)
        if success:
            dataset = entities.Dataset.from_json(client_api=self._client_api,
                                                 _json=response.json(),
                                                 datasets=self,
                                                 project=self.project)
            # create ontology and recipe
            if not create_default_recipe:
                if recipe_id is not None:
                    dataset.switch_recipe(recipe_id=recipe_id)
                else:
                    dataset = dataset.recipes.create(ontology_ids=ontology_ids,
                                                     labels=labels,
                                                     attributes=attributes).dataset
        else:
            raise exceptions.PlatformException(response)
        logger.info('Dataset was created successfully. Dataset id: {!r}'.format(dataset.id))
        assert isinstance(dataset, entities.Dataset)
        if checkout:
            self.checkout(dataset=dataset)
        return dataset

    @staticmethod
    def _convert_single(downloader,
                        item,
                        img_filepath,
                        local_path,
                        overwrite,
                        annotation_options,
                        annotation_filters,
                        thickness,
                        with_text,
                        progress,
                        alpha,
                        export_version):
        # this is to convert the downloaded json files to any other annotation type
        try:
            if entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE in annotation_options:
                if img_filepath is None:
                    img_filepath = item.download()
            downloader._download_img_annotations(item=item,
                                                 img_filepath=img_filepath,
                                                 local_path=local_path,
                                                 overwrite=overwrite,
                                                 annotation_options=annotation_options,
                                                 annotation_filters=annotation_filters,
                                                 thickness=thickness,
                                                 alpha=alpha,
                                                 with_text=with_text,
                                                 export_version=export_version
                                                 )
        except Exception:
            logger.error('Failed to download annotation for item: {!r}'.format(item.name))
        progress.update()

    @staticmethod
    def download_annotations(dataset: entities.Dataset,
                             local_path: str = None,
                             filters: entities.Filters = None,
                             annotation_options: entities.ViewAnnotationOptions = None,
                             annotation_filters: entities.Filters = None,
                             overwrite: bool = False,
                             thickness: int = 1,
                             with_text: bool = False,
                             remote_path: str = None,
                             include_annotations_in_output: bool = True,
                             export_png_files: bool = False,
                             filter_output_annotations: bool = False,
                             alpha: float = None,
                             export_version=entities.ExportVersion.V1
                             ) -> str:
        """
        Download dataset's annotations by filters.

        You may filter the dataset both for items and for annotations and download annotations.
        
        Optional -- download annotations as: mask, instance, image mask of the item.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :param str local_path: local folder or filename to save to.
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param list annotation_options: type of download annotations: list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False to overwrite the existing files
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param str remote_path: DEPRECATED and ignored
        :param bool include_annotations_in_output: default - False , if export should contain annotations
        :param bool export_png_files: default - if True, semantic annotations should be exported as png files
        :param bool filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return: local_path of the directory where all the downloaded item
        :rtype: str

        **Example**:

        .. code-block:: python

            file_path = project.datasets.download_annotations(dataset='dataset_entity',
                                                 local_path='local_path',
                                                 annotation_options=dl.ViewAnnotationOptions,
                                                 overwrite=False,
                                                 thickness=1,
                                                 with_text=False,
                                                 alpha=1
                                                 )
        """
        if annotation_options is None:
            annotation_options = list()
        elif not isinstance(annotation_options, list):
            annotation_options = [annotation_options]
        for ann_option in annotation_options:
            if not isinstance(ann_option, entities.ViewAnnotationOptions):
                if ann_option not in list(entities.ViewAnnotationOptions):
                    raise PlatformException(
                        error='400',
                        message='Unknown annotation download option: {}, please choose from: {}'.format(
                            ann_option, list(entities.ViewAnnotationOptions)))

        if remote_path is not None:
            logger.warning(
                '"remote_path" is ignored. Use "filters=dl.Filters(field="dir, values={!r}"'.format(remote_path))
        if local_path is None:
            if dataset.project is None:
                # by dataset name
                local_path = os.path.join(
                    services.service_defaults.DATALOOP_PATH,
                    "datasets",
                    "{}_{}".format(dataset.name, dataset.id),
                )
            else:
                # by dataset and project name
                local_path = os.path.join(
                    services.service_defaults.DATALOOP_PATH,
                    "projects",
                    dataset.project.name,
                    "datasets",
                    dataset.name,
                )

        if filters is None:
            filters = entities.Filters(user_query=False)
        if annotation_filters is not None:
            for annotation_filter_and in annotation_filters.and_filter_list:
                filters.add_join(field=annotation_filter_and.field,
                                 values=annotation_filter_and.values,
                                 operator=annotation_filter_and.operator,
                                 method=entities.FiltersMethod.AND)
            for annotation_filter_or in annotation_filters.or_filter_list:
                filters.add_join(field=annotation_filter_or.field,
                                 values=annotation_filter_or.values,
                                 operator=annotation_filter_or.operator,
                                 method=entities.FiltersMethod.OR)

        downloader = repositories.Downloader(items_repository=dataset.items)
        downloader.download_annotations(dataset=dataset,
                                        filters=filters,
                                        annotation_filters=annotation_filters,
                                        local_path=local_path,
                                        overwrite=overwrite,
                                        include_annotations_in_output=include_annotations_in_output,
                                        export_png_files=export_png_files,
                                        filter_output_annotations=filter_output_annotations,
                                        export_version=export_version
                                        )
        if annotation_options:
            pages = dataset.items.list(filters=filters)
            if not isinstance(annotation_options, list):
                annotation_options = [annotation_options]
            # convert all annotations to annotation_options
            pool = dataset._client_api.thread_pools(pool_name='dataset.download')
            jobs = [None for _ in range(pages.items_count)]
            progress = tqdm.tqdm(total=pages.items_count,
                                 disable=dataset._client_api.verbose.disable_progress_bar,
                                 file=sys.stdout, desc='Download Annotations')
            i_item = 0
            for page in pages:
                for item in page:
                    jobs[i_item] = pool.submit(
                        Datasets._convert_single,
                        **{
                            'downloader': downloader,
                            'item': item,
                            'img_filepath': None,
                            'local_path': local_path,
                            'overwrite': overwrite,
                            'annotation_options': annotation_options,
                            'annotation_filters': annotation_filters,
                            'thickness': thickness,
                            'with_text': with_text,
                            'progress': progress,
                            'alpha': alpha,
                            'export_version': export_version
                        }
                    )
                    i_item += 1
            # get all results
            _ = [j.result() for j in jobs]
            progress.close()
        return local_path

    def _upload_single_item_annotation(self, item, file, pbar):
        try:
            item.annotations.upload(file)
        except Exception as err:
            raise err
        finally:
            pbar.update()

    def upload_annotations(self,
                           dataset,
                           local_path,
                           filters: entities.Filters = None,
                           clean=False,
                           remote_root_path='/',
                           export_version=entities.ExportVersion.V1
                           ):
        """
        Upload annotations to dataset. 
        
        Example for remote_root_path: If the item filepath is a/b/item and
        remote_root_path is /a the start folder will be b instead of a

        **Prerequisites**: You must have a dataset with items that are related to the annotations. The relationship between the dataset and annotations is shown in the name. You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.dataset.Dataset dataset: dataset to upload to
        :param str local_path: str - local folder where the annotations files are
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param bool clean: True to remove the old annotations
        :param str remote_root_path: the remote root path to match remote and local items
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames

        **Example**:

        .. code-block:: python

            project.datasets.upload_annotations(dataset='dataset_entity',
                                                 local_path='local_path',
                                                 clean=False,
                                                 export_version=dl.ExportVersion.V1
                                                 )
        """
        if filters is None:
            filters = entities.Filters(user_query=False)
        pages = dataset.items.list(filters=filters)
        total_items = pages.items_count
        pbar = tqdm.tqdm(total=total_items, disable=dataset._client_api.verbose.disable_progress_bar,
                         file=sys.stdout, desc='Upload Annotations')
        pool = self._client_api.thread_pools('annotation.upload')
        annotations_uploaded_count = 0
        for item in pages.all():
            if export_version == entities.ExportVersion.V1:
                _, ext = os.path.splitext(item.filename)
                filepath = item.filename.replace(ext, '.json')
            else:
                filepath = item.filename + '.json'
            # make the file path ignore the hierarchy of the files that in remote_root_path
            filepath = os.path.relpath(filepath, remote_root_path)
            json_file = os.path.join(local_path, filepath)
            if not os.path.isfile(json_file):
                pbar.update()
                continue
            annotations_uploaded_count += 1
            if item.annotated and clean:
                item.annotations.delete(filters=entities.Filters(resource=entities.FiltersResource.ANNOTATION))
            pool.submit(self._upload_single_item_annotation, **{'item': item,
                                                                'file': json_file,
                                                                'pbar': pbar})
        pool.shutdown()
        if annotations_uploaded_count == 0:
            logger.warning(msg="No annotations uploaded to dataset! ")
        else:
            logger.info(msg='Found and uploaded {} annotations.'.format(annotations_uploaded_count))

    def set_readonly(self, state: bool, dataset: entities.Dataset):
        """
        Set dataset readonly mode.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param bool state: state to update readonly mode
        :param dtlpy.entities.dataset.Dataset dataset: dataset object

        **Example**:

        .. code-block:: python

            project.datasets.set_readonly(dataset='dataset_entity', state=True)
        """
        if dataset.readonly != state:
            patch = {'readonly': state}
            self.update(dataset=dataset,
                        patch=patch)
            dataset._readonly = state
        else:
            logger.warning('Dataset is already "readonly={}". Nothing was done'.format(state))
