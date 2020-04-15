import logging

from .. import entities, exceptions, repositories, miscellaneous

logger = logging.getLogger(name=__name__)


class Items:
    """
    Items repository
    """

    def __init__(self, client_api, datasets=None, dataset=None, dataset_id=None, items_entity=None):
        self._client_api = client_api
        self._dataset = dataset
        self._dataset_id = dataset_id
        self._datasets = datasets
        # set items entity to represent the item (Item, Codebase, Artifact etc...)
        if items_entity is None:
            self.items_entity = entities.Item

    ############
    # entities #
    ############
    @property
    def dataset(self):
        if self._dataset is None:
            if self._dataset_id is None:
                raise exceptions.PlatformException(
                    error='400',
                    message='Cannot perform action WITHOUT Dataset entity in Items repository. Please set a dataset')
            self._dataset = self.datasets.get(
                dataset_id=self._dataset_id, fetch=None)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    ################
    # repositories #
    ################
    @property
    def datasets(self):
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

    def get_all_items(self, filters=None):
        """
        Get all items in dataset

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

    def get_list(self, filters):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(
                                                             self.dataset.id),
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters=None, page_offset=None, page_size=None):
        """
        List items

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset:
        :param page_size:
        :return: Pages object
        """
        # default filters
        if filters is None:
            filters = entities.Filters()

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

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

        if filters.resource == 'items':
            items_entity = self.items_entity
        else:
            items_entity = entities.Annotation

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=page_offset,
                                       page_size=page_size,
                                       client_api=self._client_api,
                                       item_entity=items_entity)
        paged.get_page()
        return paged

    def get(self, filepath=None, item_id=None, fetch=None):
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :param fetch: optional - fetch entity from platform, default taken from cookie
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
                else:
                    raise exceptions.PlatformException(response)
            elif filepath is not None:
                filters = entities.Filters()
                filters.show_hidden = True
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
              with_metadata=True, with_task_annotations_status=False):
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
                                                         path="/items/{}/clone".format(
                                                             item_id),
                                                         json_req=payload)
        # check response
        if success:
            cloned_item = self.items_entity.from_json(client_api=self._client_api,
                                                      _json=response.json(),
                                                      dataset=self._dataset)
        else:
            raise exceptions.PlatformException(response)
        return cloned_item

    def delete(self, filename=None, item_id=None, filters=None):
        """
        Delete item from platform

        :param filters: optional - delete items by filter
        :param filename: optional - search item by remote path
        :param item_id: optional - search item by id
        :return: True
        """
        if item_id is not None:
            success, response = self._client_api.gen_request(req_type="delete",
                                                             path="/items/{}".format(
                                                                 item_id),
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
                raise exceptions.PlatformException(
                    error="404", message="More the 1 item exist by the name provided")
            else:
                item_id = items[0].id
                success, response = self._client_api.gen_request(req_type="delete",
                                                                 path="/items/{}".format(item_id))
        elif filters is not None:
            # prepare request
            success, response = self._client_api.gen_request(req_type="POST",
                                                             path="/datasets/{}/query".format(
                                                                 self.dataset.id),
                                                             json_req=filters.prepare(operation='delete'))
        else:
            raise exceptions.PlatformException(
                "400", "Must provide item id, filename or filters")

        # check response
        if success:
            logger.debug("Item/s deleted successfully")
            return success
        else:
            raise exceptions.PlatformException(response)

    def update(self, item=None, filters=None, update_values=None, system_update_values=None, system_metadata=False):
        """
        Update items metadata

        :param system_update_values: values in system metadata to be updated
        :param update_values: optional field to be updated and new values
        :param filters: optional update filtered items by given filter
        :param item: Item object
        :param system_metadata: bool
        :return: Item object
        """
        ref = filters is not None and (
            filters._ref_task or filters._ref_assignment)

        if system_update_values and not system_metadata:
            logger.warning('system metadata will not be updated because param system_metadata is False')

        # check params
        if item is None and filters is None:
            raise exceptions.PlatformException(
                '400', 'must provide either item or filters')

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
                logger.debug(
                    "Item was updated successfully. Item id: {}".format(item.id))
                return self.items_entity.from_json(client_api=self._client_api,
                                                   _json=response.json(),
                                                   dataset=self._dataset)
            else:
                logger.error("Error while updating item")
                raise exceptions.PlatformException(response)
        # update by filters
        else:
            # prepare request
            url_path = "/datasets/{}/query".format(self.dataset.id)
            success, response = self._client_api.gen_request(req_type="POST",
                                                             path=url_path,
                                                             json_req=filters.prepare(operation='update',
                                                                                      system_update=system_update_values,
                                                                                      system_metadata=system_metadata,
                                                                                      update=update_values))
            if not success:
                raise exceptions.PlatformException(response)
            else:
                logger.debug("Items were updated successfully.")
                return response.json()

    def download(
            self,
            filters=None,
            items=None,
            # download options
            local_path=None,
            file_types=None,
            save_locally=True,
            num_workers=None,
            annotation_options=None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            without_relative_path=None
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param local_path: local folder or filename to save to.
        :param filters: Filters entity or a dictionary containing filters parameters
        :param to_items_folder: Create 'items' folder and download items to it
        :param overwrite: optional - default = False
        :param items: download Item entity or item_id (or a list of item)
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param num_workers: default - 32
        :param save_locally: bool. save to disk or return a buffer
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param with_text: optional - add text to annotations, default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param without_relative_path: string - remote path - download items without the relative path from platform
        :return: Output (list)
        """
        downloader = repositories.Downloader(self)
        return downloader.download(
            filters=filters,
            items=items,
            local_path=local_path,
            file_types=file_types,
            save_locally=save_locally,
            num_workers=num_workers,
            annotation_options=annotation_options,
            overwrite=overwrite,
            to_items_folder=to_items_folder,
            thickness=thickness,
            with_text=with_text,
            without_relative_path=without_relative_path
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
            num_workers=32,
            overwrite=False,
            item_metadata=None
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param item_metadata:
        :param overwrite: optional - default = False
        :param local_path: list of local file, local folder, BufferIO, or url to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param remote_name: remote base name to save.
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers:
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
            num_workers=num_workers,
            overwrite=overwrite,
            # metadata to upload with items
            item_metadata=item_metadata
        )

    def open_in_web(self, filepath=None, item_id=None, item=None):
        if item is None:
            item = self.get(filepath=filepath,
                            item_id=item_id)

        self._client_api._open_in_web(resource_type='item',
                                      project_id=item.dataset.project.id,
                                      dataset_id=item.datasetId,
                                      item_id=item.id)

    def update_status(self, status, items=None, item_ids=None, filters=None, dataset=None):

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
            items = [[dataset.items.get(item_id=item_id, fetched=False) for item_id in item_ids]]

        pool = self._client_api.thread_pools(pool_name='item.status_update')
        jobs = [None for _ in range(item_count)]
        # call multiprocess wrapper to run service on each item in list
        for page in items:
            for i_item, item in enumerate(page):
                jobs[i_item] = pool.apply_async(func=item.change_status,
                                                kwds={'status': status})
        # wait for jobs to be finish
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        out_success = [r for r in results if r is True]
        out_errors = [r for r in results if r is False]
        if len(out_errors) == 0:
            logger.debug('Item/s updated successfully. {}/{}'.format(len(out_success), len(results)))
        else:
            logger.error(out_errors)
            logger.error('Item/s updated with {} errors'.format(len(out_errors)))
