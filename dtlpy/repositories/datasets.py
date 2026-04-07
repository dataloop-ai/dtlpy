"""
Datasets Repository
"""

import base64
import copy
import datetime
import hashlib
import json
import logging
import os
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Generator, Optional, Union
from urllib.parse import urlparse

import tqdm

from .. import _api_reference, entities, exceptions, miscellaneous, PlatformException, repositories, services
from ..entities.dataset import ExportType, OutputExportType, DatasetExportVersion, ExportMode
from ..services import service_defaults
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')

MAX_ITEMS_PER_SUBSET = 50000
DOWNLOAD_ANNOTATIONS_MAX_ITEMS_PER_SUBSET = 1000

class Datasets:
    """
    Datasets Repository

    The Datasets class allows the user to manage datasets. Read more about datasets in our `documentation <https://dataloop.ai/docs/dataset>`_ and `SDK documentation <https://developers.dataloop.ai/tutorials/data_management/manage_datasets/chapter/>`_.
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
        self._client_api = client_api
        # Try to get checked out project if project is None
        if project is None:
            checked_out_project = client_api.state_io.get('project')
            if checked_out_project is not None:
                project = entities.Project.from_json(_json=checked_out_project, client_api=client_api)
        self.project = project

    ###########
    # methods #
    ###########
    def __get_from_cache(self) -> entities.Dataset:
        dataset = self._client_api.state_io.get('dataset')
        if dataset is not None:
            dataset = entities.Dataset.from_json(_json=dataset,
                                                 client_api=self._client_api,
                                                 datasets=self,
                                                 project=self.project)
        return dataset

    def __get_by_id(self, dataset_id) -> entities.Dataset:
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/datasets/{}'.format(dataset_id))
        if dataset_id is None or dataset_id == '':
            raise exceptions.PlatformException('400', 'Please checkout a dataset')

        if self._client_api.check_response(success, response, path='/datasets') is False:
            return None

        dataset = entities.Dataset.from_json(client_api=self._client_api,
                                             _json=response.json(),
                                             datasets=self,
                                             project=self.project)
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
    def _save_item_json_file(item_data, base_path: Path, export_version=None):
        """
        Save a single item's JSON data to a file, creating the directory structure as needed.
        
        :param dict item_data: The item data dictionary (must have 'filename' key)
        :param Path base_path: Base directory path where JSON files should be saved
        :param entities.ExportVersion export_version: Optional export version (V1 or V2) affecting filename handling
        :return: Path to the saved JSON file
        :rtype: Path
        """
        # Get filename and remove leading slash
        filename = item_data.get('filename', '')
        if not filename:
            raise ValueError("item_data must have a 'filename' key")
        filename = filename.lstrip('/')

        # Determine relative JSON path based on export version
        if export_version == entities.ExportVersion.V1:
            # V1: Replace extension with .json (e.g., "file.jpg" -> "file.json")
            rel_json_path = str(Path(filename).with_suffix('.json'))
        elif export_version == entities.ExportVersion.V2:
            # V2: Append .json (e.g., "file.jpg" -> "file.jpg.json")
            rel_json_path = filename + '.json'
        else:
            # Default/None: Replace extension with .json (backward compatible with section 1)
            rel_json_path = os.path.splitext(filename)[0] + '.json'

        # Remove leading slash if present
        if rel_json_path.startswith('/'):
            rel_json_path = rel_json_path[1:]

        # Build output path
        out_path = base_path / rel_json_path

        # Create parent directories
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON file
        try:
            with open(out_path, 'w') as outf:
                json.dump(item_data, outf, indent=2)
        except Exception:
            logger.exception(f'Failed writing export item JSON to {out_path}')
            raise

        return out_path

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
            raise exceptions.BadRequest(status_code='400', message='filters must be of type dict or Filters')

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
        if self.project is not None:
            filters.context = {"projects": [self.project.id]}
        filters.page_size = 1000
        filters.page = 0
        datasets = list()
        while True:
            success, response = self._client_api.gen_request(req_type='POST',
                                                             json_req=filters.prepare(),
                                                             path=url,
                                                             headers={'user_query': filters._user_query})
            if self._client_api.check_response(success, response, path='/datasets/query') is False:
                return None
            pool = self._client_api.thread_pools('entity.create')
            datasets_json = response.json()['items']
            jobs = [None for _ in range(len(datasets_json))]
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
                if dataset is None:
                    return None
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
                                                 project=self.project,
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
            if self._client_api.check_response(success, response, path='/datasets/{}'.format(dataset.id)) is False:
                return False
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
        if self._client_api.check_response(success, response, path=url_path) is False:
            return None
        logger.info('Dataset was updated successfully')
        return dataset

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
        if self._client_api.check_response(success, response, path=url_path) is False:
            return None
        logger.info('Dataset was unlocked successfully')
        return dataset

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
        if self._client_api.check_response(success, response, path=url_path) is False:
            return None
        return entities.DirectoryTree(_json=response.json())

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

        if self._client_api.check_response(success, response, path='/datasets/{}/clone'.format(dataset_id)) is False:
            return None

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

            if self._client_api.check_response(success, response, path=f'/datasets/{dataset_entity.id}/export') is False:
                return

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
        # V3 (LanceDB) export parameters
        export_version: DatasetExportVersion = DatasetExportVersion.V1,
        export_mode: ExportMode = None,
        from_version: int = None,
        partition_count: int = None,
        force: bool = False,
        parallel_downloads: int = 4,
    ) -> Union[Optional[str], entities.ExportManifest]:
        """
        Export dataset items and annotations.

        **Prerequisites**: You must be an *owner* or *developer* to use this method.

        You must provide at least ONE of the following params: dataset, dataset_name, dataset_id.

        **Export Versions:**

        - **DatasetExportVersion.V1** (default): Legacy export API using item-based commands
        - **DatasetExportVersion.V3**: LanceDB-based export with partitioned NDJSON output and 
          support for incremental (diff) exports

        **V1 Export Behavior (export_version=DatasetExportVersion.V1):**

        The behavior depends on the combination of `export_type` and `output_export_type`:

        **When export_type = ExportType.JSON:**

        - **output_export_type = OutputExportType.JSON (default when None):**
          - Exports data in JSON format, split into subsets of max 500 items
          - Downloads all subset JSON files and concatenates them into a single `result.json` file
          - Returns the path to the concatenated JSON file

        - **output_export_type = OutputExportType.ZIP:**
          - Same as JSON export, but zips the final `result.json` file
          - Returns the path to the zipped file (`result.json.zip`)

        - **output_export_type = OutputExportType.FOLDERS:**
          - Creates a folder structure mirroring the remote dataset structure
          - Each item gets its own JSON file named after the original filename

        **When export_type = ExportType.ZIP:**
          - Exports data as a ZIP file containing the dataset
          - Returns the downloaded ZIP item directly

        **V3 Export Behavior (export_version=DatasetExportVersion.V3):**

        - **export_mode = ExportMode.FULL**: Exports all items matching filters (default)
        - **export_mode = ExportMode.DIFF**: Exports only items changed since `from_version`
        - Returns an ExportManifest object with partition info and downloaded file paths

        :param dtlpy.entities.dataset.Dataset dataset: Dataset object
        :param str dataset_name: The name of the dataset
        :param str dataset_id: The ID of the dataset
        :param str local_path: Local directory path to save the exported dataset. Must be a directory, not a file path.
        :param Union[dict, dtlpy.entities.filters.Filters] filters: Filters entity or a query dictionary
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations (V1 only)
        :param dtlpy.entities.filters.Filters feature_vector_filters: Filters entity to filter feature vectors (V1 only)
        :param bool include_feature_vectors: Include item feature vectors in the export (V1 only)
        :param bool include_annotations: Include item annotations in the export (V1 only)
        :param bool dataset_lock: Make dataset readonly during the export (V1 only)
        :param bool export_summary: Get Summary of the dataset export (V1 only)
        :param int lock_timeout_sec: Timeout for locking the dataset during export in seconds (V1 only)
        :param entities.ExportType export_type: Type of export ('json' or 'zip') (V1 only)
        :param entities.OutputExportType output_export_type: Output format ('json', 'zip', or 'folders') (V1 only)
        :param int timeout: Maximum time in seconds to wait for the export to complete
        :param entities.DatasetExportVersion export_version: Export API version - V1 (legacy) or V3 (LanceDB)
        :param entities.ExportMode export_mode: Export mode for V3 - FULL or DIFF (V3 only)
        :param int from_version: Starting version for diff mode (V3 only). If not provided in DIFF mode, 
            falls back to last_to_version from dataset metadata. If no previous export exists, falls back to FULL mode.
        :param int partition_count: Number of partitions, auto-calculated if None (V3 only)
        :param bool force: Force re-export even if cached (V3 only)
        :param int parallel_downloads: Number of concurrent partition downloads (V3 only)
        :return: For V1: Path to exported file/directory, or None if empty. For V3: ExportManifest object
        :rtype: Union[Optional[str], entities.ExportManifest]

        **Example - V1 Export (Legacy)**:

        .. code-block:: python

            # Default V1 export
            export_path = dataset.export(
                local_path='/path/to/export',
                export_type=dl.ExportType.JSON
            )

        **Example - V3 Export (LanceDB)**:

        .. code-block:: python

            # Full V3 export
            manifest = dataset.export(
                local_path='/path/to/export',
                export_version=dl.DatasetExportVersion.V3,
                export_mode=dl.ExportMode.FULL
            )
            print(f"Exported {manifest.total_records} records")

        **Example - V3 Diff Export (Incremental)**:

        .. code-block:: python

            # Incremental export - only changes since version 5
            manifest = dataset.export(
                export_version=dl.DatasetExportVersion.V3,
                export_mode=dl.ExportMode.DIFF,
                from_version=5
            )
            # Store to_version for next diff export
            next_from_version = manifest.to_version
        """
        if local_path is not None and os.path.isfile(local_path):
            raise ValueError(f'local_path must be a directory, not a file path: {local_path}')

        # Route to appropriate export implementation based on version
        if export_version == DatasetExportVersion.V3:
            return self._export_v3(
                dataset=dataset,
                dataset_name=dataset_name,
                dataset_id=dataset_id,
                local_path=local_path,
                filters=filters,
                export_mode=export_mode,
                from_version=from_version,
                partition_count=partition_count,
                force=force,
                timeout=timeout if timeout > 0 else 300,
                parallel_downloads=parallel_downloads,
            )
        else:
            return self._export_v1(
                dataset=dataset,
                dataset_name=dataset_name,
                dataset_id=dataset_id,
                local_path=local_path,
                filters=filters,
                annotation_filters=annotation_filters,
                feature_vector_filters=feature_vector_filters,
                include_feature_vectors=include_feature_vectors,
                include_annotations=include_annotations,
                export_type=export_type,
                timeout=timeout,
                dataset_lock=dataset_lock,
                lock_timeout_sec=lock_timeout_sec,
                export_summary=export_summary,
                output_export_type=output_export_type,
            )

    def _export_v1(
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
        Export dataset using V1 (legacy) export API.
        
        Internal method called by export() when export_version=DatasetExportVersion.V1.
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
            return export_result[0]

        if output_export_type is None:
            output_export_type = OutputExportType.JSON

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
            resolved_dataset_id = self._resolve_dataset_id(dataset, dataset_name, dataset_id)
            result_file_name = f"{resolved_dataset_id}.json"
            result_file = os.path.join(base_dir, result_file_name)
            logger.debug(f"start writing all items to result file {result_file}")
            with open(result_file, 'w') as f:
                json.dump(all_items, f)
            if output_export_type == OutputExportType.ZIP:
                zip_filename = result_file + '.zip'
                logger.debug(f"start zipping result file {zip_filename}")
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(result_file, arcname=os.path.basename(result_file))
                os.remove(result_file)
                result_file = zip_filename
            return result_file

        logger.debug("start building per-item JSON files under local_path mirroring remote structure")
        for item in all_items:
            self._save_item_json_file(item_data=item, base_path=Path(base_dir), export_version=None)
        logger.debug("end building per-item JSON files under local_path mirroring remote structure")
        return base_dir

    @staticmethod
    def _extract_api_path(url: str) -> str:
        """Extract the API path portion from a full Dataloop gateway URL.
        
        Given 'https://gate.dataloop.ai/api/v1/datasets/.../manifest',
        returns '/datasets/.../manifest'.
        """
        parsed = urlparse(url)
        path = parsed.path
        # Strip the /api/v1 prefix used by the gateway
        api_prefix_idx = path.find('/api/v1/')
        if api_prefix_idx != -1:
            return path[api_prefix_idx + len('/api/v1'):]
        return path

    def _download_partition_file(self, file_info: entities.ExportFile, file_index: int, local_path: str) -> str:
        """
        Download a single partition file with checksum verification.
        
        :param file_info: ExportFile entity with download metadata
        :param file_index: Partition index (for logging)
        :param local_path: Local directory to save the file
        :return: Path to the downloaded file
        """
        api_path = self._extract_api_path(file_info.path)

        success, response = self._client_api.gen_request(
            req_type='get',
            path=api_path,
            stream=True
        )

        if self._client_api.check_response(success, response, path=api_path) is False:
            return None

        local_file_path = os.path.join(local_path, file_info.filename)

        md5_hash = hashlib.md5()
        with open(local_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    md5_hash.update(chunk)

        actual_checksum = base64.b64encode(md5_hash.digest()).decode('utf-8')
        if file_info.checksum and actual_checksum != file_info.checksum:
            os.remove(local_file_path)
            raise exceptions.PlatformException(
                error='400',
                message=f"Checksum mismatch for {file_info.filename}: "
                        f"expected {file_info.checksum}, got {actual_checksum}"
            )

        logger.debug(f"Downloaded partition {file_index}: {file_info.filename} (checksum verified)")
        return local_file_path

    def _send_v3_export_request(self, dataset_id: str, payload: dict):
        """
        Send a single V3 export POST request and return the HTTP status code and parsed Command.
        
        Both 200 and 202 are valid responses (202 means a LanceDB sync is needed first).
        
        :return: (status_code, command) tuple. Both are None if the request failed.
        """
        api_path = f'/datasets/{dataset_id}/export/v3'
        success, response = self._client_api.gen_request(
            req_type='post',
            path=api_path,
            json_req=payload
        )

        if self._client_api.check_response(success, response, path=api_path) is False:
            return None, None

        command = entities.Command.from_json(
            _json=response.json(),
            client_api=self._client_api
        )
        return response.status_code, command

    def _export_v3(
        self,
        dataset: entities.Dataset = None,
        dataset_name: str = None,
        dataset_id: str = None,
        local_path: str = None,
        filters: Union[dict, entities.Filters] = None,
        export_mode: ExportMode = None,
        from_version: int = None,
        partition_count: int = None,
        force: bool = False,
        timeout: int = 300,
        parallel_downloads: int = 4,
    ) -> entities.ExportManifest:
        """
        Export dataset using V3 (LanceDB) export API.
        
        Internal method called by export() when export_version=DatasetExportVersion.V3.
        
        This method exports dataset items and annotations using the optimized V3 export
        pipeline with partitioned NDJSON output. It supports both full exports and 
        incremental (diff) exports for efficient data synchronization.
        
        If the dataset has not been synced to LanceDB yet, the API returns 202 with a
        SyncDatasetToLanceDB command. This method waits for that sync to complete and
        retries the export once. A second 202 response is treated as an error.
        """
        resolved_dataset_id = self._resolve_dataset_id(dataset, dataset_name, dataset_id)

        # Get dataset entity if not provided (needed for metadata update)
        if dataset is None:
            dataset = self.get(dataset_id=resolved_dataset_id)

        if export_mode is None:
            export_mode = ExportMode.FULL

        if export_mode == ExportMode.DIFF and from_version is None:
            export_v3_meta = dataset.metadata.get('export_v3', {}) or {}
            last_to_version = export_v3_meta.get('last_to_version')
            if last_to_version is not None:
                from_version = last_to_version
                logger.info(
                    "from_version not provided, using last_to_version=%s from dataset metadata. "
                    "Previous export: mode=%s, time=%s, records=%s, by=%s",
                    from_version,
                    export_v3_meta.get('last_export_mode'),
                    export_v3_meta.get('last_export_time'),
                    export_v3_meta.get('last_total_records'),
                    export_v3_meta.get('last_export_by', 'unknown')
                )
            else:
                export_mode = ExportMode.FULL
                logger.warning(
                    "from_version not provided and no previous V3 export found in dataset metadata. "
                    "Falling back to full export mode."
                )

        payload = {
            'mode': export_mode.value if isinstance(export_mode, ExportMode) else export_mode,
            'format': 'ndjson',
            'force': force
        }

        if partition_count is not None:
            payload['partitionCount'] = partition_count

        if from_version is not None:
            payload['fromVersion'] = from_version

        if filters is not None:
            if isinstance(filters, entities.Filters):
                payload['filters'] = {
                    'itemsQuery': {
                        'filter': filters.prepare().get('filter', {})
                    }
                }
            elif isinstance(filters, dict):
                payload['filters'] = filters
            else:
                raise exceptions.BadRequest(
                    message='filters must be of type dict or Filters',
                    status_code=400
                )

        logger.info(f"Initiating V3 LanceDB export for dataset {resolved_dataset_id}")
        status_code, command = self._send_v3_export_request(resolved_dataset_id, payload)
        if command is None:
            return None

        # The API may return a SyncDatasetToLanceDB command (HTTP 200 or 202)
        # when the dataset hasn't been synced yet. Wait for sync, then retry.
        SYNC_COMMAND_TYPE = 'syncdatasettolancedb'
        if command.type and command.type.lower() == SYNC_COMMAND_TYPE:
            logger.info(
                "Dataset requires LanceDB sync before export (command %s, type: %s). "
                "Waiting for sync to complete...",
                command.id, command.type
            )
            command = command.wait(timeout=timeout)
            if command.status != entities.CommandsStatus.SUCCESS:
                raise exceptions.PlatformException(
                    error='424',
                    message=f"LanceDB sync command {command.id} failed with status '{command.status}'. "
                            f"Cannot proceed with export."
                )
            logger.info("LanceDB sync completed successfully. Retrying export...")
            status_code, command = self._send_v3_export_request(resolved_dataset_id, payload)
            if command is None:
                return None
            if command.type and command.type.lower() == SYNC_COMMAND_TYPE:
                raise exceptions.PlatformException(
                    error='424',
                    message=f"Dataset {resolved_dataset_id} still requires LanceDB sync after initial "
                            f"sync completed (command {command.id}). Please try again later or contact support."
                )

        logger.info(f"Export command {command.id} created, waiting for completion...")
        command = command.wait(timeout=timeout)

        if command.status != entities.CommandsStatus.SUCCESS:
            raise exceptions.PlatformException(
                error='424',
                message=f"Export command failed: {command.error}"
            )

        export_result = command.spec.get('exportResult', {})
        manifest_url = export_result.get('manifestUrl')

        if not manifest_url:
            total_records = export_result.get('totalRecords', 0) or 0
            if total_records > 0:
                raise exceptions.PlatformException(
                    error='400',
                    message=f"manifestUrl is null but totalRecords={total_records}"
                )
            logger.error("export result is empty (manifestUrl is null)")
            return None

        logger.info("Fetching export manifest...")
        manifest_path = self._extract_api_path(manifest_url)

        success, response = self._client_api.gen_request(
            req_type='get',
            path=manifest_path
        )

        if self._client_api.check_response(success, response, path=manifest_path) is False:
            return None

        manifest_json = response.json()
        manifest = entities.ExportManifest.from_json(
            _json=manifest_json,
            export_result=export_result
        )

        logger.info(
            f"Export manifest received: {manifest.total_records} records, "
            f"{manifest.partition_count} partitions, {manifest.total_bytes} bytes"
        )

        # Set up local path
        if local_path is None:
            local_path = os.path.join(
                tempfile.gettempdir(),
                'dataloop',
                'exports',
                resolved_dataset_id,
                manifest.export_id
            )

        os.makedirs(local_path, exist_ok=True)
        manifest.local_path = local_path

        if not manifest.files:
            logger.warning("No files to download in export manifest")
            # Still save metadata even for empty exports
            self._save_export_v3_metadata(
                dataset=dataset,
                manifest=manifest,
                local_path=local_path
            )
            return manifest

        logger.info(f"Downloading {len(manifest.files)} partition files to {local_path}...")

        downloaded_files = []
        with ThreadPoolExecutor(max_workers=parallel_downloads) as executor:
            future_to_file = {
                executor.submit(self._download_partition_file, f, i, local_path): f 
                for i, f in enumerate(manifest.files)
            }

            for future in tqdm.tqdm(
                as_completed(future_to_file),
                total=len(manifest.files),
                desc='Downloading partitions',
                disable=self._client_api.verbose.disable_progress_bar,
                file=sys.stdout
            ):
                try:
                    local_file = future.result()
                    downloaded_files.append(local_file)
                except Exception as e:
                    logger.error(f"Failed to download partition: {e}")
                    raise

        manifest.downloaded_files = sorted(downloaded_files)
        logger.info(f"Downloaded {len(downloaded_files)} files to {local_path}")

        # Save export metadata to dataset and local history
        self._save_export_v3_metadata(
            dataset=dataset,
            manifest=manifest,
            local_path=local_path
        )

        return manifest

    def _save_export_v3_metadata(
        self,
        dataset: entities.Dataset,
        manifest: entities.ExportManifest,
        local_path: str
    ):
        """
        Save V3 export metadata to dataset metadata and local export history file.
        
        - Updates dataset.metadata.export_v3 with latest export info (overwrites)
        - Appends to local /.dataloop/all_exports.json history file
        """
        # Build export metadata record
        export_metadata = {
            'export_id': manifest.export_id,
            'dataset_id': dataset.id,
            'exported_at': manifest.exported_at,
            'mode': manifest.mode,
            'from_version': manifest.from_version,
            'to_version': manifest.to_version,
            'total_records': manifest.total_records,
            'total_bytes': manifest.total_bytes,
            'partition_count': manifest.partition_count,
            'file_count': manifest.statistics.file_count,
            'format': manifest.format,
            'local_path': local_path,
            'downloaded_files': manifest.downloaded_files,
            'last_updated': datetime.datetime.utcnow().isoformat() + 'Z'
        }
        # 1. Update dataset metadata with latest export info
        try:
            export_by = self._client_api.info(with_token=False).get('user_email', None) or 'unknown'
            dataset.metadata['export_v3'] = {
                'last_export_id': manifest.export_id,
                'last_export_time': manifest.exported_at,
                'last_export_mode': manifest.mode,
                'last_from_version': manifest.from_version,
                'last_to_version': manifest.to_version,
                'last_total_records': manifest.total_records,
                'last_total_bytes': manifest.total_bytes,
                'last_partition_count': manifest.partition_count,
                'last_local_path': local_path,
                'last_export_by': export_by
            }

            self.update(dataset=dataset, system_metadata=True)
            logger.debug(f"Updated dataset {dataset.id} metadata with export_v3 info")
        except Exception as e:
            logger.warning(f"Failed to update dataset metadata with export_v3 info: {e}")

        # 2. Save to remote export history file in dataset
        try:
            remote_history_path = '/.dataloop/all_exports.json'
            items_repo = repositories.Items(client_api=self._client_api, dataset=dataset)

            # Try to get existing history file
            export_history = {'exports': []}
            try:
                filters = entities.Filters()
                filters.add(field='filename', values='all_exports.json')
                filters.add(field='dir', values='/.dataloop')
                pages = items_repo.list(filters=filters)
                if pages.items_count > 0:
                    history_item = pages.items[0]
                    # Download and parse existing history
                    local_temp = os.path.join(tempfile.gettempdir(), 'all_exports_temp.json')
                    history_item.download(local_path=local_temp)
                    with open(local_temp, 'r') as f:
                        export_history = json.load(f)
                    os.remove(local_temp)
            except Exception:
                pass

            # Append current export to history
            export_history['exports'].append(export_metadata)

            # Write updated history to temp file and upload
            temp_history_file = os.path.join(tempfile.gettempdir(), 'all_exports.json')
            with open(temp_history_file, 'w') as f:
                json.dump(export_history, f, indent=2)

            # Upload (overwrite if exists)
            items_repo.upload(
                local_path=temp_history_file,
                remote_path='/.dataloop',
                overwrite=True
            )
            os.remove(temp_history_file)

            logger.debug(f"Saved export history to {remote_history_path} in dataset {dataset.id}")
        except Exception as e:
            logger.warning(f"Failed to save export history to dataset: {e}")

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

        if self._client_api.check_response(success, response, path='/datasets/merge') is False:
            return False

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

        if self._client_api.check_response(success, response, path='/datasets/{}/sync'.format(dataset_id)) is False:
            return False

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
        if self._client_api.check_response(success, response, path='/datasets') is False:
            return None

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
                             alpha: float = 1,
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
            if ann_option not in entities.ViewAnnotationOptions:
                raise PlatformException(
                    error='400',
                    message=f'Unknown annotation download option: {ann_option}, please choose from: {list(entities.ViewAnnotationOptions)}',
                )
        if remote_path is not None:
            logger.warning(f'"remote_path" is ignored. Use "filters=dl.Filters(field="dir, values={remote_path!r}"')
        if filter_output_annotations is True:
            logger.warning("'filter_output_annotations' is ignored but kept for legacy support")
        if include_annotations_in_output is False:
            logger.warning("include_annotations_in_output was False, but was set to True since this function downloads annotations.")
            include_annotations_in_output = True

        if local_path is None:
            if dataset.project is None:
                # by dataset name
                local_path = str(Path(service_defaults.DATALOOP_PATH) / "datasets" / f"{dataset.name}_{dataset.id}")
            else:
                # by dataset and project name
                local_path = str(Path(service_defaults.DATALOOP_PATH) / "projects" / dataset.project.name / "datasets" / dataset.name)

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

        # Setup for incremental processing
        if len(annotation_options) == 0 :
            pool = None
            progress = None
            jobs = []
        else:             
            # Get total count for progress bar
            filter_copy = copy.deepcopy(filters)
            filter_copy.page_size = 0
            pages = dataset.items.list(filters=filter_copy)
            total_items = pages.items_count

            # Setup thread pool and progress bar
            pool = dataset._client_api.thread_pools(pool_name='dataset.download')
            progress = tqdm.tqdm(
                total=total_items,
                disable=dataset._client_api.verbose.disable_progress_bar_download_annotations,
                file=sys.stdout,
                desc='Download Annotations'
            )
            jobs = []

        # Call _export_recursive as generator
        export_generator = dataset.project.datasets._export_recursive(
            dataset=dataset,
            local_path=tempfile.mkdtemp(prefix='annotations_jsons_'),
            filters=filters,
            annotation_filters=annotation_filters,
            include_annotations=True,
            export_type=ExportType.JSON,
            dataset_lock=dataset_lock,
            lock_timeout_sec=lock_timeout_sec,
            export_summary=export_summary,
            timeout=0,
            max_items_per_subset=DOWNLOAD_ANNOTATIONS_MAX_ITEMS_PER_SUBSET
        )

        # Process each subset JSON file incrementally
        for subset_json_file in export_generator:
            if subset_json_file is None or not Path(subset_json_file).is_file():
                continue

            try:
                # Open and load the items array
                with open(subset_json_file, 'r') as f:
                    items_data = json.load(f)

                # Process each item immediately
                for item_data in items_data:
                    # Split and save individual JSON file
                    Datasets._save_item_json_file(item_data=item_data, base_path=Path(local_path) / 'json', export_version=export_version)

                    # If annotation_options are provided, submit to thread pool immediately
                    if annotation_options:
                        # Create Item entity from item_data
                        item = entities.Item.from_json(
                            _json=item_data,
                            client_api=dataset._client_api,
                            dataset=dataset
                        )

                        job = pool.submit(
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
                        jobs.append(job)

                # Clean up temporary subset JSON file
                os.remove(subset_json_file)
            except Exception as e:
                logger.exception(f'Failed processing subset JSON file {subset_json_file}: {e}')

        # Wait for all thread pool jobs to complete
        if annotation_options:
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
        if self._client_api.check_response(success, response, path=path) is False:
            return False

        command = entities.Command.from_json(_json=response.json(),
                                            client_api=self._client_api)
        command.wait()
        return True

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
        if self._client_api.check_response(success, response, path=f'/datasets/{dataset_id}/items/bulk-update-metadata') is False:
            return False

        command = entities.Command.from_json(_json=response.json(), client_api=self._client_api)
        command.wait()
        return True
