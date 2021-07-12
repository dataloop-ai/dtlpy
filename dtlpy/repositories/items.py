import logging

from .. import entities, exceptions, repositories, miscellaneous, services

logger = logging.getLogger(name=__name__)


class Items:
    """
    Items repository
    """

    def __init__(self,
                 client_api: services.ApiClient,
                 datasets: repositories.Datasets = None,
                 dataset: entities.Dataset = None,
                 dataset_id=None, items_entity=None):
        self._client_api = client_api
        self._dataset = dataset
        self._dataset_id = dataset_id
        self._datasets = datasets
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
        if entity in [entities.Item, entities.Artifact, entities.Codebase]:
            self.items_entity = entity
        else:
            raise exceptions.PlatformException(error="403",
                                               message="Unable to set given entity. Entity give: {}".format(entity))

    def get_all_items(self, filters: entities.Filters = None) -> [entities.Item]:
        """
        Get all items in dataset
        :param filters: dl.Filters entity to filters items
        :return: list of all items
        """
        if filters is None:
            filters = entities.Filters()
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

        :param filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(self.dataset.id),
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None, page_offset=None, page_size=None) -> entities.PagedEntities:
        """
        List items

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset: start page
        :param page_size: page size
        :return: Pages object
        """
        # default filters
        if filters is None:
            filters = entities.Filters()
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

    def get(self, filepath=None, item_id=None, fetch=None, is_dir=False) -> entities.Item:
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :param fetch: optional - fetch entity from platform, default taken from cookie
        :param is_dir: True if you want to get an item from dir type
        :return: Item object
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
                                                       dataset=self._dataset)
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
                                           is_fetched=False)
        assert isinstance(item, entities.Item)
        return item

    def clone(self, item_id, dst_dataset_id, remote_filepath=None, metadata=None, with_annotations=True,
              with_metadata=True, with_task_annotations_status=False, wait=True):
        """
        Clone item
        :param item_id: item to clone
        :param dst_dataset_id: destination dataset id
        :param remote_filepath: complete filepath
        :param metadata: new metadata to add
        :param with_annotations: clone annotations
        :param with_metadata: clone metadata
        :param with_task_annotations_status: clone task annotations status
        :param wait: wait the command to finish
        :return: Item
        """
        if metadata is None:
            metadata = dict()
        payload = {"targetDatasetId": dst_dataset_id,
                   "remoteFileName": remote_filepath,
                   "metadata": metadata,
                   "cloneDatasetParams": {
                       "withItemsAnnotations": with_annotations,
                       "withMetadata": with_metadata,
                       "withTaskAnnotationsStatus": with_task_annotations_status}
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

    def delete(self, filename=None, item_id=None, filters: entities.Filters = None):
        """
        Delete item from platform

        :param filename: optional - search item by remote path
        :param item_id: optional - search item by id
        :param filters: optional - delete items by filter
        :return: True
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

    def update(self,
               item: entities.Item = None,
               filters: entities.Filters = None,
               update_values=None,
               system_update_values=None,
               system_metadata=False):
        """
        Update items metadata
        :param item: Item object
        :param filters: optional update filtered items by given filter
        :param update_values: optional field to be updated and new values
        :param system_update_values: values in system metadata to be updated
        :param system_metadata: bool - True, if you want to change metadata system
        :return: Item object
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
            local_path=None,
            file_types=None,
            save_locally=True,
            to_array=False,
            annotation_options: entities.ViewAnnotationOptions = None,
            annotation_filters: entities.Filters = None,
            annotation_filter_type: entities.AnnotationType = None,
            annotation_filter_label=None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            without_relative_path=None,
            avoid_unnecessary_annotation_download=False
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param filters: Filters entity or a dictionary containing filters parameters
        :param items: download Item entity or item_id (or a list of item)
        :param local_path: local folder or filename to save to.
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param save_locally: bool. save to disk or return a buffer
        :param to_array: returns Ndarray when True and local_path = False
        :param annotation_options: download annotations options:  list(dl.ViewAnnotationOptions)
        :param annotation_filters: Filters entity to filter annotations for download
        :param annotation_filter_type: DEPRECATED - list (dl.AnnotationType) of annotation types when downloading annotation, not relevant for JSON option
        :param annotation_filter_label: DEPRECATED - list of labels types when downloading annotation, not relevant for JSON option
        :param overwrite: optional - default = False
        :param to_items_folder: Create 'items' folder and download items to it
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param without_relative_path: string - remote path - download items without the relative path from platform
        :param avoid_unnecessary_annotation_download: default - False
        :return: `List` of local_path per each downloaded item
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
            annotation_filter_type=annotation_filter_type,  # to deprecate - use "annotation_filters"
            annotation_filter_label=annotation_filter_label,  # to deprecate - use "annotation_filters"
            overwrite=overwrite,
            to_items_folder=to_items_folder,
            thickness=thickness,
            with_text=with_text,
            without_relative_path=without_relative_path,
            avoid_unnecessary_annotation_download=avoid_unnecessary_annotation_download
        )

    def upload(
            self,
            # what to upload
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path="/",
            remote_name=None,
            file_types=None,
            overwrite=False,
            item_metadata=None
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param local_path: list of local file, local folder, BufferIO, numpy.ndarray or url to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param remote_name: remote base name to save.
                            when upload numpy.ndarray as local path, remote_name with .jpg or .png ext is mandatory
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param item_metadata:
        :param overwrite: optional - default = False
        :return: Output (list/single item)
        """
        # fix remote path
        if remote_path is not None:
            if not remote_path.startswith('/'):
                remote_path = '/' + remote_path

        # initiate and use uploader
        uploader = repositories.Uploader(self)
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
            item_metadata=item_metadata
        )

    def open_in_web(self, filepath=None, item_id=None, item=None):
        """
        :param filepath: item file path
        :param item_id: item id
        :param item: item entity
        """
        if item is None:
            item = self.get(filepath=filepath,
                            item_id=item_id)

        self._client_api._open_in_web(resource_type='item',
                                      project_id=item.dataset.project.id,
                                      dataset_id=item.datasetId,
                                      item_id=item.id)

    def update_status(self, status: entities.ItemStatus, items=None, item_ids=None,
                      filters=None, dataset=None, clear=False):
        """
        :param status: ItemStatus.COMPLETED, ItemStatus.APPROVED, ItemStatus.DISCARDED
        :param items:
        :param item_ids:
        :param filters:
        :param dataset:
        :param clear:
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
            if not isinstance(items, list):
                items = [items]
            item_count = len(items)
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
        Create a directory in a dataset

        :param directory: name of directory
        :param dataset: optional
        :return:
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

    def move_items(self, destination, filters: entities.Filters = None, items=None,
                   dataset: entities.Dataset = None) -> bool:
        """
        Move items to another directory.

        If directory does not exist we will create it

        :param destination: destination directory
        :param filters: optional - either this or items. Query of items to move
        :param items: optional - either this or filters. A list of items to move
        :param dataset: optional
        :return: True if success
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
