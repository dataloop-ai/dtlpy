import logging

from .. import entities, exceptions, repositories, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Items:
    """
    Items Repository

    The Items class allows you to manage items in your datasets.
    For information on actions related to items see https://developers.dataloop.ai/tutorials/data_management/upload_and_manage_items/chapter/
    """

    def __init__(self,
                 client_api: ApiClient,
                 datasets: repositories.Datasets = None,
                 dataset: entities.Dataset = None,
                 dataset_id=None,
                 items_entity=None,
                 project=None):
        self._client_api = client_api
        self._dataset = dataset
        self._dataset_id = dataset_id
        self._datasets = datasets
        self._project = project
        # set items entity to represent the item (Item, Codebase, Artifact etc...)
        if items_entity is None:
            self.items_entity = entities.Item
        if self._dataset_id is None and self._dataset is not None:
            self._dataset_id = self._dataset.id

    ############
    # entities #
    ############
    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            if self._dataset_id is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Cannot perform action WITHOUT Dataset entity in Items repository. Please set a dataset')
            self._dataset = self.datasets.get(dataset_id=self._dataset_id, fetch=None)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='400',
                message='Cannot perform action WITHOUT Project entity in Items repository. Please set a project')
        assert isinstance(self._dataset, entities.Dataset)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Dataset entity')
        self._project = project

    ################
    # repositories #
    ################
    @property
    def datasets(self) -> repositories.Datasets:
        if self._datasets is None:
            self._datasets = repositories.Datasets(client_api=self._client_api)
        assert isinstance(self._datasets, repositories.Datasets)
        return self._datasets

    ###########
    # methods #
    ###########

    def set_items_entity(self, entity):
        """
        Set the item entity type to `Artifact <https://dataloop.ai/docs/auto-annotation-service?#uploading-model-weights-as-artifacts>`_, Item, or Codebase.

        :param entities.Item, entities.Artifact, entities.Codebase entity: entity type [entities.Item, entities.Artifact, entities.Codebase]
        """
        if entity in [entities.Item, entities.Artifact, entities.Codebase]:
            self.items_entity = entity
        else:
            raise exceptions.PlatformException(error="403",
                                               message="Unable to set given entity. Entity give: {}".format(entity))

    def get_all_items(self, filters: entities.Filters = None) -> [entities.Item]:
        """
        Get all items in dataset.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :return: list of all items
        :rtype: list

        **Example**:

        .. code-block:: python

            dataset.items.get_all_items()

        """
        if filters is None:
            filters = entities.Filters()
            filters._user_query = 'false'
            filters.add(field='type', values='file')
        pages = self.list(filters=filters)
        num_items = pages.items_count
        items = [None for _ in range(num_items)]
        for i_item, item in enumerate(pages.all()):
            items[i_item] = item
        items = [item for item in items if item is not None]
        return items

    def _build_entities_from_response(self, response_items) -> miscellaneous.List[entities.Item]:
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_item, item in enumerate(response_items):
            jobs[i_item] = pool.submit(self.items_entity._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': item,
                                          'dataset': self.dataset})
        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        items = miscellaneous.List([r[1] for r in results if r[0] is True])
        return items

    def _list(self, filters: entities.Filters):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(self.dataset.id),
                                                         json_req=filters.prepare(),
                                                         headers={'user_query': filters._user_query})
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/datasets/{id}/query', method='post')
    def list(self,
             filters: entities.Filters = None,
             page_offset: int = None,
             page_size: int = None
             ) -> entities.PagedEntities:
        """
        List items in a dataset.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param int page_offset: start page
        :param int page_size: page size
        :return: Pages object
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            dataset.items.list(page_offset=0, page_size=100)
        """
        # default filters
        if filters is None:
            filters = entities.Filters()
            filters._user_query = 'false'
        # assert type filters
        elif not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException(error='400',
                                               message='Unknown filters type: {!r}'.format(type(filters)))
        if filters.resource != entities.FiltersResource.ITEM and filters.resource != entities.FiltersResource.ANNOTATION:
            raise exceptions.PlatformException(
                error='400',
                message='Filters resource must to be FiltersResource.ITEM. Got: {!r}'.format(filters.resource))

        # page size
        if page_size is None:
            # take from default
            page_size = filters.page_size
        else:
            filters.page_size = page_size

        # page offset
        if page_offset is None:
            # take from default
            page_offset = filters.page
        else:
            filters.page = page_offset

        if filters.resource == entities.FiltersResource.ITEM:
            items_repository = self
        else:
            items_repository = repositories.Annotations(client_api=self._client_api,
                                                        dataset=self._dataset)

        paged = entities.PagedEntities(items_repository=items_repository,
                                       filters=filters,
                                       page_offset=page_offset,
                                       page_size=page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

    @_api_reference.add(path='/items/{id}', method='get')
    def get(self,
            filepath: str = None,
            item_id: str = None,
            fetch: bool = None,
            is_dir: bool = False
            ) -> entities.Item:
        """
        Get Item object

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str filepath: optional - search by remote path
        :param str item_id: optional - search by id
        :param bool fetch: optional - fetch entity from platform, default taken from cookie
        :param bool is_dir: True if you want to get an item from dir type
        :return: Item object
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            dataset.items.get(item_id='item_id')
        """
        if fetch is None:
            fetch = self._client_api.fetch_entities

        if fetch:
            if item_id is not None:
                success, response = self._client_api.gen_request(req_type="get",
                                                                 path="/items/{}".format(item_id))
                if success:
                    item = self.items_entity.from_json(client_api=self._client_api,
                                                       _json=response.json(),
                                                       dataset=self._dataset,
                                                       project=self._project)
                    # verify input filepath is same as the given id
                    if filepath is not None and item.filename != filepath:
                        logger.warning(
                            "Mismatch found in items.get: filepath is different then item.filename: "
                            "{!r} != {!r}".format(
                                filepath,
                                item.filename))
                else:
                    raise exceptions.PlatformException(response)
            elif filepath is not None:
                filters = entities.Filters()
                filters.pop(field='hidden')
                if is_dir:
                    filters.add(field='type', values='dir')
                    filters.recursive = False
                filters.add(field='filename', values=filepath)
                paged_entity = self.list(filters=filters)
                if len(paged_entity.items) == 0:
                    raise exceptions.PlatformException(error='404',
                                                       message='Item not found. filepath= "{}"'.format(filepath))
                elif len(paged_entity.items) > 1:
                    raise exceptions.PlatformException(
                        error='404',
                        message='More than one item found. Please "get" by id. filepath: "{}"'.format(filepath))
                else:
                    item = paged_entity.items[0]
            else:
                raise exceptions.PlatformException(error="400",
                                                   message='Must choose by at least one. "filename" or "item_id"')
        else:
            item = entities.Item.from_json(_json={'id': item_id,
                                                  'filename': filepath},
                                           client_api=self._client_api,
                                           dataset=self._dataset,
                                           is_fetched=False,
                                           project=self._project)
        assert isinstance(item, entities.Item)
        return item

    @_api_reference.add(path='/items/{id}/clone', method='post')
    def clone(self,
              item_id: str,
              dst_dataset_id: str,
              remote_filepath: str = None,
              metadata: dict = None,
              with_annotations: bool = True,
              with_metadata: bool = True,
              with_task_annotations_status: bool = False,
              allow_many: bool = False,
              wait: bool = True):
        """
        Clone item. Read more about cloning datatsets and items in our `documentation <https://dataloop.ai/docs/clone-merge-dataset#cloned-dataset>`_ and `SDK documentation <https://developers.dataloop.ai/tutorials/data_management/data_versioning/chapter/>`_.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str item_id: item to clone
        :param str dst_dataset_id: destination dataset id
        :param str remote_filepath: complete filepath
        :param dict metadata: new metadata to add
        :param bool with_annotations: clone annotations
        :param bool with_metadata: clone metadata
        :param bool with_task_annotations_status: clone task annotations status
        :param bool allow_many: `bool` if True, using multiple clones in single dataset is allowed, (default=False)
        :param bool wait: wait for the command to finish
        :return: Item object
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            dataset.items.clone(item_id='item_id',
                    dst_dataset_id='dist_dataset_id',
                    with_metadata=True,
                    with_task_annotations_status=False,
                    with_annotations=False)
        """
        if metadata is None:
            metadata = dict()
        payload = {"targetDatasetId": dst_dataset_id,
                   "remoteFileName": remote_filepath,
                   "metadata": metadata,
                   "cloneDatasetParams": {
                       "withItemsAnnotations": with_annotations,
                       "withMetadata": with_metadata,
                       "withTaskAnnotationsStatus": with_task_annotations_status},
                   "allowMany": allow_many
                   }
        success, response = self._client_api.gen_request(req_type="post",
                                                         path="/items/{}/clone".format(item_id),
                                                         json_req=payload)
        # check response
        if not success:
            raise exceptions.PlatformException(response)

        command = entities.Command.from_json(_json=response.json(),
                                             client_api=self._client_api)
        if not wait:
            return command
        command = command.wait()

        if 'returnedModelId' not in command.spec:
            raise exceptions.PlatformException(error='400',
                                               message="returnedModelId key is missing in command response: {}"
                                               .format(response))
        cloned_item = self.get(item_id=command.spec['returnedModelId'][0])
        return cloned_item

    @_api_reference.add(path='/items/{id}', method='delete')
    def delete(self,
               filename: str = None,
               item_id: str = None,
               filters: entities.Filters = None):
        """
        Delete item from platform.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        You must provide at least ONE of the following params: item id, filename, filters.

        :param str filename: optional - search item by remote path
        :param str item_id: optional - search item by id
        :param dtlpy.entities.filters.Filters filters: optional - delete items by filter
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.items.delete(item_id='item_id')
        """
        if item_id is not None:
            success, response = self._client_api.gen_request(req_type="delete",
                                                             path="/items/{}".format(item_id),
                                                             )
        elif filename is not None:
            if not filename.startswith("/"):
                filename = "/" + filename
            items = self.get(filepath=filename)
            if not isinstance(items, list):
                items = [items]
            if len(items) == 0:
                raise exceptions.PlatformException("404", "Item not found")
            elif len(items) > 1:
                raise exceptions.PlatformException(error="404", message="More the 1 item exist by the name provided")
            else:
                item_id = items[0].id
                success, response = self._client_api.gen_request(req_type="delete",
                                                                 path="/items/{}".format(item_id))
        elif filters is not None:
            # prepare request
            success, response = self._client_api.gen_request(req_type="POST",
                                                             path="/datasets/{}/query".format(self.dataset.id),
                                                             json_req=filters.prepare(operation='delete'))
        else:
            raise exceptions.PlatformException("400", "Must provide item id, filename or filters")

        # check response
        if success:
            logger.debug("Item/s deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    @_api_reference.add(path='/items/{id}', method='patch')
    def update(self,
               item: entities.Item = None,
               filters: entities.Filters = None,
               update_values=None,
               system_update_values=None,
               system_metadata: bool = False):
        """
        Update item metadata.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        You must provide at least ONE of the following params: update_values, system_update_values.

        :param dtlpy.entities.item.Item item: Item object
        :param dtlpy.entities.filters.Filters filters: optional update filtered items by given filter
        :param update_values: optional field to be updated and new values
        :param system_update_values: values in system metadata to be updated
        :param bool system_metadata: True, if you want to update the metadata system
        :return: Item object
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            dataset.items.update(item='item_entity')
        """
        ref = filters is not None and (filters._ref_task or filters._ref_assignment)

        if system_update_values and not system_metadata:
            logger.warning('system metadata will not be updated because param system_metadata is False')

        # check params
        if item is None and filters is None:
            raise exceptions.PlatformException('400', 'must provide either item or filters')

        value_to_update = update_values or system_update_values

        if item is None and not ref and not value_to_update:
            raise exceptions.PlatformException('400',
                                               'Must provide update_values or system_update_values')

        # update item
        if item is not None:
            json_req = miscellaneous.DictDiffer.diff(origin=item._platform_dict,
                                                     modified=item.to_json())
            if not json_req:
                return item
            url_path = "/items/{}".format(item.id)
            if system_metadata:
                url_path += "?system=true"
            success, response = self._client_api.gen_request(req_type="patch",
                                                             path=url_path,
                                                             json_req=json_req)
            if success:
                logger.debug("Item was updated successfully. Item id: {}".format(item.id))
                return self.items_entity.from_json(client_api=self._client_api,
                                                   _json=response.json(),
                                                   dataset=self._dataset)
            else:
                logger.error("Error while updating item")
                raise exceptions.PlatformException(response)
        # update by filters
        else:
            # prepare request
            prepared_filter = filters.prepare(operation='update',
                                              system_update=system_update_values,
                                              system_metadata=system_metadata,
                                              update=update_values)
            success, response = self._client_api.gen_request(req_type="POST",
                                                             path="/datasets/{}/query".format(self.dataset.id),
                                                             json_req=prepared_filter)
            if not success:
                raise exceptions.PlatformException(response)
            else:
                logger.debug("Items were updated successfully.")
                return response.json()

    def download(
            self,
            filters: entities.Filters = None,
            items=None,
            # download options
            local_path: str = None,
            file_types: list = None,
            save_locally: bool = True,
            to_array: bool = False,
            annotation_options: entities.ViewAnnotationOptions = None,
            annotation_filters: entities.Filters = None,
            overwrite: bool = False,
            to_items_folder: bool = True,
            thickness: int = 1,
            with_text: bool = False,
            without_relative_path=None,
            avoid_unnecessary_annotation_download: bool = False,
            include_annotations_in_output: bool = True,
            export_png_files: bool = False,
            filter_output_annotations: bool = False,
            alpha: float = 1,
            export_version=entities.ExportVersion.V1
    ):
        """
        Download dataset items by filters.

        Filters the dataset for items and saves them locally.

        Optional -- download annotation, mask, instance, and image mask of the item.

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param List[dtlpy.entities.item.Item] or dtlpy.entities.item.Item items: download Item entity or item_id (or a list of item)
        :param str local_path: local folder or filename to save to.
        :param list file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param bool save_locally: bool. save to disk or return a buffer
        :param bool to_array: returns Ndarray when True and local_path = False
        :param list annotation_options: download annotations options:  list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False
        :param bool to_items_folder: Create 'items' folder and download items to it
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param bool without_relative_path: bool - download items without the relative path from platform
        :param bool avoid_unnecessary_annotation_download: default - False
        :param bool include_annotations_in_output: default - False , if export should contain annotations
        :param bool export_png_files: default - if True, semantic annotations should be exported as png files
        :param bool filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return: generator of local_path per each downloaded item
        :rtype: generator or single item

        **Example**:

        .. code-block:: python

            dataset.items.download(local_path='local_path',
                                 annotation_options=dl.ViewAnnotationOptions,
                                 overwrite=False,
                                 thickness=1,
                                 with_text=False,
                                 alpha=1,
                                 save_locally=True
                                 )
        """
        downloader = repositories.Downloader(self)
        return downloader.download(
            filters=filters,
            items=items,
            local_path=local_path,
            file_types=file_types,
            save_locally=save_locally,
            to_array=to_array,
            annotation_options=annotation_options,
            annotation_filters=annotation_filters,
            overwrite=overwrite,
            to_items_folder=to_items_folder,
            thickness=thickness,
            alpha=alpha,
            with_text=with_text,
            without_relative_path=without_relative_path,
            avoid_unnecessary_annotation_download=avoid_unnecessary_annotation_download,
            include_annotations_in_output=include_annotations_in_output,
            export_png_files=export_png_files,
            filter_output_annotations=filter_output_annotations,
            export_version=export_version
        )

    def upload(
            self,
            # what to upload
            local_path: str,
            local_annotations_path: str = None,
            # upload options
            remote_path: str = "/",
            remote_name: str = None,
            file_types: list = None,
            overwrite: bool = False,
            item_metadata: dict = None,
            output_entity=entities.Item,
            no_output: bool = False,
            export_version: str = entities.ExportVersion.V1,
            item_description: str = None
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain unchanged.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without the head directory.

        **Prerequisites**: Any user can upload items.

        :param str local_path: list of local file, local folder, BufferIO, numpy.ndarray or url to upload
        :param str local_annotations_path: path to dataloop format annotations json files.
        :param str remote_path: remote path to save.
        :param str remote_name: remote base name to save. when upload numpy.ndarray as local path, remote_name with .jpg or .png ext is mandatory
        :param list file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param dict item_metadata: metadata dict to upload to item or ExportMetadata option to export metadata from annotation file
        :param bool overwrite: optional - default = False
        :param output_entity: output type
        :param bool no_output: do not return the items after upload
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :param str item_description: add a string description to the uploaded item
        :return: Output (generator/single item)
        :rtype: generator or single item

        **Example**:

        .. code-block:: python

            dataset.items.upload(local_path='local_path',
                                 local_annotations_path='local_annotations_path',
                                 overwrite=True,
                                 item_metadata={'Hellow': 'Word'}
                                 )
        """
        # initiate and use uploader
        uploader = repositories.Uploader(items_repository=self, output_entity=output_entity, no_output=no_output)
        return uploader.upload(
            local_path=local_path,
            local_annotations_path=local_annotations_path,
            # upload options
            remote_path=remote_path,
            remote_name=remote_name,
            file_types=file_types,
            # config
            overwrite=overwrite,
            # metadata to upload with items
            item_metadata=item_metadata,
            export_version=export_version,
            item_description=item_description
        )

    @property
    def platform_url(self):
        return self._client_api._get_resource_url(
            "projects/{}/datasets/{}/items".format(self.dataset.project.id, self.dataset.id))

    def open_in_web(self, filepath=None, item_id=None, item=None):
        """
        Open the item in web platform

        **Prerequisites**: You must be in the role of an *owner* or *developer* or be an *annotation manager*/*annotator* with access to that item through task.

        :param str filepath: item file path
        :param str item_id: item id
        :param dtlpy.entities.item.Item item: item entity

        **Example**:

        .. code-block:: python

            dataset.items.open_in_web(item_id='item_id')

        """
        if filepath is not None:
            item = self.get(filepath=filepath)
        if item is not None:
            item.open_in_web()
        elif item_id is not None:
            self._client_api._open_in_web(url=self.platform_url + '/' + str(item_id))
        else:
            self._client_api._open_in_web(url=self.platform_url)

    def update_status(self,
                      status: entities.ItemStatus,
                      items=None,
                      item_ids=None,
                      filters=None,
                      dataset=None,
                      clear=False):
        """
        Update item status in task

        **Prerequisites**: You must be in the role of an *owner* or *developer* or *annotation manager* who has been assigned a task with the item.

        You must provide at least ONE of the following params: items, item_ids, filters.

        :param str status: ItemStatus.COMPLETED, ItemStatus.APPROVED, ItemStatus.DISCARDED
        :param list items: list of items
        :param list item_ids: list of items id
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :param bool clear: to delete status

        **Example**:

        .. code-block:: python

            dataset.items.update_status(item_ids='item_id', status=dl.ItemStatus.COMPLETED)

        """
        if items is None and item_ids is None and filters is None:
            raise exceptions.PlatformException('400', 'Must provide either items, item_ids or filters')

        if self._dataset is None and dataset is None:
            raise exceptions.PlatformException('400', 'Please provide dataset')
        elif dataset is None:
            dataset = self._dataset

        if filters is not None:
            items = dataset.items.list(filters=filters)
            item_count = items.items_count
        elif items is not None:
            if isinstance(items, entities.PagedEntities):
                item_count = items.items_count
            else:
                if not isinstance(items, list):
                    items = [items]
                item_count = len(items)
                items = [items]
        else:
            if not isinstance(item_ids, list):
                item_ids = [item_ids]
            item_count = len(item_ids)
            items = [[dataset.items.get(item_id=item_id, fetch=False) for item_id in item_ids]]

        pool = self._client_api.thread_pools(pool_name='item.status_update')
        jobs = [None for _ in range(item_count)]
        # call multiprocess wrapper to run service on each item in list
        for page in items:
            for i_item, item in enumerate(page):
                jobs[i_item] = pool.submit(item.update_status,
                                           **{'status': status,
                                              'clear': clear})

        # get all results
        results = [j.result() for j in jobs]
        out_success = [r for r in results if r is True]
        out_errors = [r for r in results if r is False]
        if len(out_errors) == 0:
            logger.debug('Item/s updated successfully. {}/{}'.format(len(out_success), len(results)))
        else:
            logger.error(out_errors)
            logger.error('Item/s updated with {} errors'.format(len(out_errors)))

    def make_dir(self, directory, dataset: entities.Dataset = None) -> entities.Item:
        """
        Create a directory in a dataset.

        **Prerequisites**: All users.

        :param str directory: name of directory
        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :return: Item object
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            dataset.items.make_dir(directory='directory_name')
        """
        if self._dataset_id is None and dataset is None:
            raise exceptions.PlatformException('400', 'Please provide parameter dataset')

        payload = {
            'type': 'dir',
            'path': directory
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        success, response = self._client_api.gen_request(req_type="post",
                                                         headers=headers,
                                                         path="/datasets/{}/items".format(self._dataset_id),
                                                         data=payload)
        if success:
            item = self.items_entity.from_json(client_api=self._client_api,
                                               _json=response.json(),
                                               dataset=self._dataset)
        else:
            raise exceptions.PlatformException(response)

        return item

    def move_items(self,
                   destination: str,
                   filters: entities.Filters = None,
                   items=None,
                   dataset: entities.Dataset = None
                   ) -> bool:
        """
        Move items to another directory.
        If directory does not exist we will create it

        **Prerequisites**: You must be in the role of an *owner* or *developer*.

        :param str destination: destination directory
        :param dtlpy.entities.filters.Filters filters: optional - either this or items. Query of items to move
        :param items: optional - either this or filters. A list of items to move
        :param dtlpy.entities.dataset.Dataset dataset: dataset object
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            dataset.items.move_items(destination='directory_name')
        """
        if filters is None and items is None:
            raise exceptions.PlatformException('400', 'Must provide either filters or items')

        dest_dir_filter = entities.Filters(resource=entities.FiltersResource.ITEM, field='type', values='dir')
        dest_dir_filter.recursive = False
        dest_dir_filter.add(field='filename', values=destination)
        dirs_page = self.list(filters=dest_dir_filter)

        if dirs_page.items_count == 0:
            directory = self.make_dir(directory=destination, dataset=dataset)
        elif dirs_page.items_count == 1:
            directory = dirs_page.items[0]
        else:
            raise exceptions.PlatformException('404', 'More than one directory by the name of: {}'.format(destination))

        if filters is not None:
            items = self.list(filters=filters)
        elif isinstance(items, list):
            items = [items]
        elif not isinstance(items, entities.PagedEntities):
            raise exceptions.PlatformException('400', 'items must be a list of items or a pages entity not {}'.format(
                type(items)))

        item_ids = list()
        for page in items:
            for item in page:
                item_ids.append(item.id)

        success, response = self._client_api.gen_request(req_type="put",
                                                         path="/datasets/{}/items/{}".format(self._dataset_id,
                                                                                             directory.id),
                                                         json_req=item_ids)
        if not success:
            raise exceptions.PlatformException(response)

        return success
