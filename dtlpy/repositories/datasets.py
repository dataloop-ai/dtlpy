"""
Datasets Repository
"""

import os
import sys
import time
import copy
import tqdm
import logging
import zipfile
import json
from typing import Union, Generator, Optional

from .. import entities, repositories, miscellaneous, exceptions, services, PlatformException, _api_reference
from ..services.api_client import ApiClient
from ..entities.dataset import OutputExportType, ExportType

logger = logging.getLogger(name='dtlpy')

MAX_ITEMS_PER_SUBSET = 50000

class Datasets:
    """
    Datasets Repository

    The Datasets class allows the user to manage datasets. Read more about datasets in our `documentation <https://dataloop.ai/docs/dataset>`_ and `SDK documentation <https://developers.dataloop.ai/tutorials/data_management/manage_datasets/chapter/>`_.
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
            filters = entities.Filters()
            filters._user_query = 'false'
        if not folder_path.startswith('/'):
            folder_path = '/' + folder_path
        filters.add(field='dir', values=folder_path, method=entities.FiltersMethod.OR)
        if not folder_path.endswith('*'):
            if not folder_path.endswith('/'):
                folder_path += '/'
            filters.add(field='dir', values=folder_path + '*', method=entities.FiltersMethod.OR)
        return filters

    def _get_binaries_dataset(self):
        filters = entities.Filters(resource=entities.FiltersResource.DATASET)
        filters.add(field='name', values='Binaries')
        filters.system_space = True
        datasets = self.list(filters=filters)
        if len(datasets) == 0:
            # empty list
            raise exceptions.PlatformException('404', 'Dataset not found. Name: "Binaries"')
            # dataset = None
        elif len(datasets) > 1:
            raise exceptions.PlatformException('400', 'More than one dataset with same name.')
        else:
            dataset = datasets[0]
        return dataset

    def _resolve_dataset_id(self, dataset, dataset_name, dataset_id):
        if dataset is None and dataset_name is None and dataset_id is None:
            raise ValueError('Must provide dataset, dataset name or dataset id')
        if dataset_id is None:
            if dataset is None:
                dataset = self.get(dataset_name=dataset_name)
            dataset_id = dataset.id
        return dataset_id

    @staticmethod
    def _build_payload(filters, include_feature_vectors, include_annotations,
                       export_type, annotation_filters, feature_vector_filters, dataset_lock, lock_timeout_sec, export_summary):
        valid_list = [e.value for e in entities.ExportType]
        valid_types = ', '.join(valid_list)
        if export_type not in ['json', 'zip']:
            raise ValueError('export_type must be one of the following: {}'.format(valid_types))
        payload = {'exportType': export_type}
        if filters is None:
            filters = entities.Filters()

        if isinstance(filters, entities.Filters):
            payload['itemsQuery'] = {'filter': filters.prepare()['filter'], 'join': filters.prepare().get("join", {})}
        elif isinstance(filters, dict):
            payload['itemsQuery'] = filters
        else:
            raise exceptions.BadRequest(message='filters must be of type dict or Filters', status_code=500)

        payload['itemsVectorQuery'] = {}
        if include_feature_vectors:
            payload['includeItemVectors'] = True
            payload['itemsVectorQuery']['select'] = {"datasetId": 1, 'featureSetId': 1, 'value': 1}

        if feature_vector_filters is not None:
            payload['itemsVectorQuery']['filter'] = feature_vector_filters.prepare()['filter']

        payload['annotations'] = {"include": include_annotations, "convertSemantic": False}

        if annotation_filters is not None:
            payload['annotationsQuery'] = annotation_filters.prepare()

        if dataset_lock:
            payload['datasetLock'] = dataset_lock

        if export_summary:
            payload['summary'] = export_summary

        if lock_timeout_sec:
            payload['lockTimeoutSec'] = lock_timeout_sec

        return payload

    def _download_exported_item(self, item_id, export_type, local_path=None, unzip=True):
        logger.debug(f"start downloading exported item {item_id} with export_type {export_type} and local_path {local_path} and unzip {unzip}")
        export_item = repositories.Items(client_api=self._client_api).get(item_id=item_id)
        export_item_path = export_item.download(local_path=local_path)        

        # Common validation check for both JSON and other export types
        if isinstance(export_item_path, list) or not os.path.isfile(export_item_path):
            raise exceptions.PlatformException(
                error='404',
                message='error downloading annotation zip file. see above for more information. item id: {!r}'.format(
                    export_item.id))

        result = None
        if unzip is False or export_type == entities.ExportType.JSON:
            result = export_item_path
        else:
            try:
                miscellaneous.Zipping.unzip_directory(zip_filename=export_item_path,
                                                        to_directory=local_path)
                result = local_path
            except Exception as e:
                logger.warning("Failed to extract zip file error: {}".format(e))
            finally:
                # cleanup only for zip files to avoid removing needed results
                if isinstance(export_item_path, str) and os.path.isfile(export_item_path):
                    os.remove(export_item_path)
        logger.debug(f"end downloading, result {result}")
        return result

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
            self._client_api._open_in_web(url=f'{self.platform_url}/{dataset_id}/items')
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

    @_api_reference.add(path='/datasets/query', method='post')
    def list(self, name=None, creator=None, filters: entities.Filters = None) -> miscellaneous.List[entities.Dataset]:
        """
        List all datasets.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param str name: list by name
        :param str creator: list by
        :param dtlpy.entities.filters.Filters filters: Filters entity containing filters parameters
        :return: List of datasets
        :rtype: list

        **Example**:

        .. code-block:: python
            filters = dl.Filters(resource='datasets')
            filters.add(field='readonly', values=False)
            datasets = project.datasets.list(filters=filters)
        """
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.DATASET)
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.DATASET:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.DATASET. Got: {!r}'.format(filters.resource))

        url = '/datasets/query'

        if name is not None:
            filters.add(field='name', values=name)
        if creator is not None:
            filters.add(field='creator', values=creator)
        if self._project is not None:
            filters.context = {"projects": [self._project.id]}
        filters.page_size = 1000
        filters.page = 0
        datasets = list()
        while True:
            success, response = self._client_api.gen_request(req_type='POST',
                                                             json_req=filters.prepare(),
                                                             path=url,
                                                             headers={'user_query': filters._user_query})
            if success:
                pool = self._client_api.thread_pools('entity.create')
                datasets_json = response.json()['items']
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
                datasets.extend([r[1] for r in results if r[0] is True])
                if response.json()['hasNextPage'] is True:
                    filters.page += 1
                else:
                    break
            else:
                raise exceptions.PlatformException(response)
        datasets = miscellaneous.List(datasets)
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

    @_api_reference.add(path='/datasets/{id}/unlock', method='patch')
    def unlock(self, dataset: entities.Dataset ) -> entities.Dataset:
        """
        Unlock dataset.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :return: Dataset object
        :rtype: dtlpy.entities.dataset.Dataset

        **Example**:

        .. code-block:: python

            dataset = project.datasets.unlock(dataset='dataset_entity')
        """
        url_path = '/datasets/{}/unlock'.format(dataset.id)

        success, response = self._client_api.gen_request(req_type='patch', path=url_path)
        if success:
            logger.info('Dataset was unlocked successfully')
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
        dataset_id = self._resolve_dataset_id(dataset, dataset_name, dataset_id)

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
              clone_name: str = None,
              filters: entities.Filters = None,
              with_items_annotations: bool = True,
              with_metadata: bool = True,
              with_task_annotations_status: bool = True,
              dst_dataset_id: str = None,
              target_directory: str = None):
        """
        Clone a dataset. Read more about cloning datatsets and items in our `documentation <https://dataloop.ai/docs/clone-merge-dataset#cloned-dataset>`_ and `SDK documentation <https://developers.dataloop.ai/tutorials/data_management/data_versioning/chapter/>`_.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str dataset_id: id of the dataset you wish to clone
        :param str clone_name: new dataset name
        :param dtlpy.entities.filters.Filters filters: Filters entity or a query dict
        :param bool with_items_annotations: true to clone with items annotations
        :param bool with_metadata: true to clone with metadata
        :param bool with_task_annotations_status: true to clone with task annotations' status
        :param str dst_dataset_id: destination dataset id
        :param str target_directory: target directory
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
        if clone_name is None and dst_dataset_id is None:
            raise exceptions.PlatformException('400', 'Must provide clone name or destination dataset id')
        if filters is None:
            filters = entities.Filters()
            filters._user_query = 'false'
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(
                error='400',
                message='"filters" must be a dl.Filters entity. got: {!r}'.format(type(filters)))

        copy_filters = copy.deepcopy(filters)
        if copy_filters.has_field('hidden'):
            copy_filters.pop('hidden')

        if target_directory is not None and not target_directory.startswith('/'):
            target_directory = '/' + target_directory

        payload = {
            "name": clone_name,
            "filter": copy_filters.prepare(),
            "cloneDatasetParams": {
                "withItemsAnnotations": with_items_annotations,
                "withMetadata": with_metadata,
                "withTaskAnnotationsStatus": with_task_annotations_status,
                "targetDirectory": target_directory
            }
        }
        if dst_dataset_id is not None:
            payload['cloneDatasetParams']['targetDatasetId'] = dst_dataset_id
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/clone'.format(dataset_id),
                                                         json_req=payload,
                                                         headers={'user_query': filters._user_query})

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

    def _export_recursive(
        self,
        dataset: entities.Dataset = None,
        dataset_name: str = None,
        dataset_id: str = None,
        local_path: str = None,
        filters: Union[dict, entities.Filters] = None,
        annotation_filters: entities.Filters = None,
        feature_vector_filters: entities.Filters = None,
        include_feature_vectors: bool = False,
        include_annotations: bool = False,
        timeout: int = 0,
        dataset_lock: bool = False,
        lock_timeout_sec: int = None,
        export_summary: bool = False,
        max_items_per_subset: int = MAX_ITEMS_PER_SUBSET,
        export_type: ExportType = ExportType.JSON,
        output_export_type: OutputExportType = OutputExportType.JSON,
    ) -> Generator[str, None, None]:
        """
        Export dataset items recursively by splitting large datasets into smaller subsets.

        Args:
            dataset (entities.Dataset, optional): Dataset entity to export
            dataset_name (str, optional): Name of the dataset to export
            dataset_id (str, optional): ID of the dataset to export
            local_path (str, optional): Local path to save the exported data
            filters (Union[dict, entities.Filters], optional): Filters to apply on the items
            annotation_filters (entities.Filters, optional): Filters to apply on the annotations
            feature_vector_filters (entities.Filters, optional): Filters to apply on the feature vectors
            include_feature_vectors (bool, optional): Whether to include feature vectors in export. Defaults to False
            include_annotations (bool, optional): Whether to include annotations in export. Defaults to False
            timeout (int, optional): Timeout in seconds for the export operation. Defaults to 0
            dataset_lock (bool, optional): Whether to lock the dataset during export. Defaults to False
            lock_timeout_sec (int, optional): Timeout for dataset lock in seconds. Defaults to None
            export_summary (bool, optional): Whether to include export summary. Defaults to False
            max_items_per_subset (int, optional): Maximum items per subset for recursive export. Defaults to MAX_ITEMS_PER_SUBSET
            export_type (ExportType, optional): Type of export (JSON or ZIP). Defaults to ExportType.JSON
            output_export_type (OutputExportType, optional): Output format type. Defaults to OutputExportType.JSON

        Returns:
            Generator[str, None, None]: Generator yielding export paths

        Raises:
            NotImplementedError: If ZIP export type is used with JSON output type
            exceptions.PlatformException: If API request fails or command response is invalid
        """
        logger.debug(f"exporting dataset with export_type {export_type} and output_export_type {output_export_type}")
        if export_type == ExportType.ZIP and output_export_type == OutputExportType.JSON:
            raise NotImplementedError(
                "Zip export type is not supported for JSON output type.\n"
                "If Json output is required, please use the export_type = JSON"
            )

        # Get dataset entity for recursive filtering
        dataset_entity = self.get(dataset_id=self._resolve_dataset_id(dataset, dataset_name, dataset_id))
        if export_type != ExportType.JSON:
            filters_list = [filters]
        else:
            # Generate filter subsets using recursive_get_filters
            filters_list = entities.Filters._get_split_filters(
                dataset=dataset_entity, filters=filters, max_items=max_items_per_subset
            )
        # First loop: Make all API requests without waiting
        commands = []
        logger.debug("start making all API requests without waiting")
        for filter_i in filters_list:
            # Build payload for this subset
            payload = self._build_payload(
                filters=filter_i,
                include_feature_vectors=include_feature_vectors,
                include_annotations=include_annotations,
                export_type=export_type,
                annotation_filters=annotation_filters,
                feature_vector_filters=feature_vector_filters,
                dataset_lock=dataset_lock,
                lock_timeout_sec=lock_timeout_sec,
                export_summary=export_summary,
            )

            # Make API request for this subset
            success, response = self._client_api.gen_request(
                req_type='post', path=f'/datasets/{dataset_entity.id}/export', json_req=payload
            )

            if not success:
                logger.error(f"failed to make API request /datasets/{dataset_entity.id}/export with payload {payload} response {response}")
                raise exceptions.PlatformException(response)

            # Handle command execution
            commands.append( entities.Command.from_json(_json=response.json(), client_api=self._client_api))

        time.sleep(2)  # as the command have wrong progress in the beginning
        logger.debug("start waiting for all commands")
        # Second loop: Wait for all commands and process results
        for command in commands:
            command = command.wait(timeout=timeout)

            if 'outputItemId' not in command.spec:
                raise exceptions.PlatformException(
                    error='400', message="outputItemId key is missing in command response"
                )

            item_id = command.spec['outputItemId']
            # Download and process the exported item
            yield self._download_exported_item(
                item_id=item_id,
                export_type=export_type,
                local_path=local_path,
                unzip=output_export_type != OutputExportType.ZIP,
            )

    @_api_reference.add(path='/datasets/{id}/export', method='post')
    def export(
        self,
        dataset: entities.Dataset = None,
        dataset_name: str = None,
        dataset_id: str = None,
        local_path: str = None,
        filters: Union[dict, entities.Filters] = None,
        annotation_filters: entities.Filters = None,
        feature_vector_filters: entities.Filters = None,
        include_feature_vectors: bool = False,
        include_annotations: bool = False,
        export_type: ExportType = ExportType.JSON,
        timeout: int = 0,
        dataset_lock: bool = False,
        lock_timeout_sec: int = None,
        export_summary: bool = False,
        output_export_type: OutputExportType = None,
    ) -> Optional[str]:
        """
        Export dataset items and annotations.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset, dataset_name, dataset_id.

        **Export Behavior by Parameter Combination:**

        The behavior of this method depends on the combination of `export_type` and `output_export_type`:

        **When export_type = ExportType.JSON:**

        - **output_export_type = OutputExportType.JSON (default when None):**
          - Exports data in JSON format, split into subsets of max 500 items
          - Downloads all subset JSON files and concatenates them into a single `result.json` file
          - Returns the path to the concatenated JSON file
          - Cleans up individual subset files after concatenation

        - **output_export_type = OutputExportType.ZIP:**
          - Same as JSON export, but zips the final `result.json` file
          - Returns the path to the zipped file (`result.json.zip`)
          - Cleans up the unzipped JSON file after zipping

        - **output_export_type = OutputExportType.FOLDERS:**
          - Exports data in JSON format, split into subsets of max 500 items
          - Downloads all subset JSON files and creates individual JSON files for each item
          - Creates a folder structure mirroring the remote dataset structure
          - Returns the path to the base directory containing the folder structure
          - Each item gets its own JSON file named after the original filename

        **When export_type = ExportType.ZIP:**

        - **output_export_type = OutputExportType.ZIP:**
          - Exports data as a ZIP file containing the dataset
          - Returns the downloaded ZIP item directly
          - No additional processing or concatenation

        - **output_export_type = OutputExportType.JSON:**
          - **NOT SUPPORTED** - Raises NotImplementedError
          - Use export_type=ExportType.JSON instead for JSON output

        - **output_export_type = OutputExportType.FOLDERS:**
          - **NOT SUPPORTED** - Raises NotImplementedError
          - Use export_type=ExportType.JSON instead for folder output

        **When output_export_type = None (legacy behavior):**
        - Defaults to OutputExportType.JSON
        - Maintains backward compatibility with existing code

        :param dtlpy.entities.dataset.Dataset dataset: Dataset object
        :param str dataset_name: The name of the dataset
        :param str dataset_id: The ID of the dataset
        :param str local_path: Local path to save the exported dataset
        :param Union[dict, dtlpy.entities.filters.Filters] filters: Filters entity or a query dictionary
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for export
        :param dtlpy.entities.filters.Filters feature_vector_filters: Filters entity to filter feature vectors for export
        :param bool include_feature_vectors: Include item feature vectors in the export
        :param bool include_annotations: Include item annotations in the export
        :param bool dataset_lock: Make dataset readonly during the export
        :param bool export_summary: Get Summary of the dataset export
        :param int lock_timeout_sec: Timeout for locking the dataset during export in seconds
        :param entities.ExportType export_type: Type of export ('json' or 'zip')
        :param entities.OutputExportType output_export_type: Output format ('json', 'zip', or 'folders'). If None, defaults to 'json'
        :param int timeout: Maximum time in seconds to wait for the export to complete
        :return: Path to exported file/directory, or None if export result is empty
        :rtype: Optional[str]
        """
        export_result = list(
            self._export_recursive(
                dataset=dataset,
                dataset_name=dataset_name,
                dataset_id=dataset_id,
                local_path=local_path,
                filters=filters,
                annotation_filters=annotation_filters,
                feature_vector_filters=feature_vector_filters,
                include_feature_vectors=include_feature_vectors,
                include_annotations=include_annotations,
                timeout=timeout,
                dataset_lock=dataset_lock,
                lock_timeout_sec=lock_timeout_sec,
                export_summary=export_summary,
                export_type=export_type,
                output_export_type=output_export_type,
            )
        )
        if all(x is None for x in export_result):
            logger.error("export result is empty")
            return None

        if export_type == ExportType.ZIP:
            # if export type is zip, then return the _export_recursive result as it
            return export_result[0]

        # if user didn't provide output_export_type, keep the previous behavior
        if output_export_type is None:
            output_export_type = OutputExportType.JSON

        # export type is jsos :
        # Load all items from subset JSON files and clean them up
        all_items = []
        logger.debug("start loading all items from subset JSON files")
        for json_file in export_result:
            if json_file is None:
                continue
            if os.path.isfile(json_file):
                with open(json_file, 'r') as f:
                    items = json.load(f)                    
                    if isinstance(items, list):
                        all_items.extend(items)
                os.remove(json_file)

        base_dir = os.path.dirname(export_result[0])
        if output_export_type != OutputExportType.FOLDERS:
            dataset_id=self._resolve_dataset_id(dataset, dataset_name, dataset_id)
            result_file_name = f"{dataset_id}.json"
            result_file = os.path.join(base_dir, result_file_name)
            logger.debug(f"start writing all items to result file {result_file}")
            with open(result_file, 'w') as f:
                json.dump(all_items, f)
            if output_export_type == OutputExportType.ZIP:
                # Zip the result file
                zip_filename = result_file + '.zip'
                # Create zip file
                logger.debug(f"start zipping result file {zip_filename}")
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(result_file, arcname=os.path.basename(result_file))

                # Remove original json after zipping
                os.remove(result_file)
                result_file = zip_filename
            return result_file
        logger.debug("start building per-item JSON files under local_path mirroring remote structure")
        # Build per-item JSON files under local_path mirroring remote structure
        for item in all_items:
            rel_json_path = os.path.splitext(item.get('filename'))[0] + '.json'
            # Remove leading slash to make it a relative path
            if rel_json_path.startswith('/'):
                rel_json_path = rel_json_path[1:]
            out_path = os.path.join(base_dir, rel_json_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            try:
                with open(out_path, 'w') as outf:
                    json.dump(item, outf)
            except Exception:
                logger.exception(f'Failed writing export item JSON to {out_path}')
        logger.debug("end building per-item JSON files under local_path mirroring remote structure")
        return base_dir

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
        Merge a dataset. See our `SDK docs <https://developers.dataloop.ai/tutorials/data_management/data_versioning/chapter/>`_ for more information.

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
                             export_version=entities.ExportVersion.V1,
                             dataset_lock: bool = False, 
                             lock_timeout_sec: int = None,
                             export_summary: bool = False,              
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
        :param bool dataset_loc: optional - default = False to make the dataset readonly
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param str remote_path: DEPRECATED and ignored
        :param bool include_annotations_in_output: default - False , if export should contain annotations
        :param bool export_png_files: default - if True, semantic annotations should be exported as png files
        :param bool filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return: local_path of the directory where all the downloaded item
        :param bool dataset_lock: optional - default = False
        :param bool export_summary: optional - default = False
        :param int lock_timeout_sec: optional
        :rtype: str

        **Example**:

        .. code-block:: python

            file_path = project.datasets.download_annotations(dataset='dataset_entity',
                                                 local_path='local_path',
                                                 annotation_options=dl.ViewAnnotationOptions,
                                                 overwrite=False,
                                                 thickness=1,
                                                 with_text=False,
                                                 alpha=1,
                                                 dataset_lock=False,
                                                 lock_timeout_sec=300,
                                                 export_summary=False                                               
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
            filters = entities.Filters()
            filters._user_query = 'false'
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
                                        export_version=export_version,
                                        dataset_lock=dataset_lock,
                                        lock_timeout_sec=lock_timeout_sec,
                                        export_summary=export_summary                                      
                                        )
        if annotation_options:
            pages = dataset.items.list(filters=filters)
            if not isinstance(annotation_options, list):
                annotation_options = [annotation_options]
            # convert all annotations to annotation_options
            pool = dataset._client_api.thread_pools(pool_name='dataset.download')
            jobs = [None for _ in range(pages.items_count)]
            progress = tqdm.tqdm(total=pages.items_count,
                                 disable=dataset._client_api.verbose.disable_progress_bar_download_annotations,
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

        Example for remote_root_path: If the item filepath is "/a/b/item" and remote_root_path is "/a" - the start folder will be b instead of a

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
            filters = entities.Filters()
            filters._user_query = 'false'
        pages = dataset.items.list(filters=filters)
        total_items = pages.items_count
        pbar = tqdm.tqdm(total=total_items, disable=dataset._client_api.verbose.disable_progress_bar_upload_annotations,
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
        import warnings
        warnings.warn("`readonly` flag on dataset is deprecated, doing nothing.", DeprecationWarning)

    @_api_reference.add(path='/datasets/{id}/split', method='post')
    def split_ml_subsets(self,
                        dataset_id: str,
                        items_query: entities.filters,
                        ml_split_list: dict) -> bool:
        """
        Split dataset items into ML subsets.

        :param str dataset_id: The ID of the dataset.
        :param dict items_query: Query to select items.
        :param dict ml_split_list: Dictionary with 'train', 'validation', 'test' keys and integer percentages.
        :return: True if the split operation was successful.
        :rtype: bool
        :raises: PlatformException on failure and ValueError if percentages do not sum to 100 or invalid keys/values.
        """
        # Validate percentages
        if not ml_split_list:
            ml_split_list = {'train': 80, 'validation': 10, 'test': 10}

        if not items_query:
            items_query = entities.Filters()

        items_query_dict = items_query.prepare()
        required_keys = {'train', 'validation', 'test'}
        if set(ml_split_list.keys()) != required_keys:
            raise ValueError("MLSplitList must have exactly the keys 'train', 'validation', 'test'.")
        total = sum(ml_split_list.values())
        if total != 100:
            raise ValueError(
                "Please set the Train, Validation, and Test subsets percentages to add up to 100%. "
                "For example: 70, 15, 15."
            )
        for key, value in ml_split_list.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError("Percentages must be integers >= 0.")
        payload = {
            'itemsQuery': items_query_dict,
            'MLSplitList': ml_split_list
        }
        path = f'/datasets/{dataset_id}/split'
        success, response = self._client_api.gen_request(req_type='post',
                                                        path=path,
                                                        json_req=payload)
        if success:
            # Wait for the split operation to complete
            command = entities.Command.from_json(_json=response.json(),
                                                client_api=self._client_api)
            command.wait()
            return True
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/datasets/{id}/items/bulk-update-metadata', method='post')
    def bulk_update_ml_subset(self, dataset_id: str, items_query: dict, subset: str = None, deleteTag: bool = False) -> bool:
        """
        Bulk update ML subset assignment for selected items.
        If subset is None, remove subsets. Otherwise, assign the specified subset.

        :param str dataset_id: ID of the dataset
        :param dict items_query: DQLResourceQuery (filters) for selecting items
        :param str subset: 'train', 'validation', 'test' or None to remove all
        :return: True if success
        :rtype: bool
        """
        if items_query is None:
            items_query = entities.Filters()
        items_query_dict = items_query.prepare()
        if not deleteTag and subset not in ['train', 'validation', 'test']:
            raise ValueError("subset must be one of: 'train', 'validation', 'test'")
        # Determine tag values based on subset
        tags = {
            'train': True if subset == 'train' else None,
            'validation': True if subset == 'validation' else None,
            'test': True if subset == 'test' else None
        }

        payload = {
            "query": items_query_dict,
            "updateQuery": {
                "update": {
                    "metadata": {
                        "system": {
                            "tags": tags
                        }
                    }
                },
                "systemSpace": True
            }
        }

        success, response = self._client_api.gen_request(
            req_type='post',
            path=f'/datasets/{dataset_id}/items/bulk-update-metadata',
            json_req=payload
        )
        if success:
            # Similar to split operation, a command is returned
            command = entities.Command.from_json(_json=response.json(), client_api=self._client_api)
            command.wait()
            return True
        else:
            raise exceptions.PlatformException(response)
