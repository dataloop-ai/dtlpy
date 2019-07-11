import logging
import traceback
from multiprocessing.pool import ThreadPool
import attr

from .. import entities, PlatformException, repositories


@attr.s
class Items:
    """
    Items repository
    """

    client_api = attr.ib()
    dataset = attr.ib()
    logger = attr.ib(default=logging.getLogger("dataloop.repositories.items"))
    # set items entity to represent the item (Item, Package, Artifact etc...)
    items_entity = attr.ib(default=entities.Item)

    def set_items_entity(self, entity):
        if entity in [entities.Item, entities.Artifact, entities.Package]:
            self.items_entity = entity
        else:
            self.logger.exception(
                "Unable to se to given entity. Entity give: %s" % entity
            )
            raise PlatformException("403", "Unable to se to given entity.")

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

        def get_page(w_page, i_start, w_items):
            try:
                for item in w_page:
                    w_items[i_start] = item
                    i_start += 1
            except:
                self.logger.exception(traceback.format_exc())

        items = [None for _ in range(num_items)]
        pool = ThreadPool(processes=32)
        i_item = 0
        for page in pages:
            pool.apply_async(
                get_page, kwds={"i_start": i_item, "w_page": page, "w_items": items}
            )
            i_item += filters.page_size
        pool.close()
        pool.join()
        pool.terminate()
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
        success, response = self.client_api.gen_request(req_type="POST",
                                                        path="/datasets/%s/query" % self.dataset.id,
                                                        json_req=filters.prepare())
        if not success:
            raise PlatformException(response)
        try:
            self.client_api.print_json(response.json()["items"])
            self.logger.debug("Page:%d/%d" % (1 + filters.page, response.json()["totalPagesCount"]))
        except ValueError:
            # no JSON returned
            pass
        return response.json()

    def list(self, filters=None, page_offset=0, page_size=100):
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
            filters.page = page_offset
            filters.page_size = page_size

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise PlatformException('400', 'Unknown filters type')

        # get page
        if filters.page != page_offset:
            page_offset = filters.page
        if filters.page_size != page_size:
            page_size = filters.page_size

        if filters.resource == 'items':
            items_entity = self.items_entity
        else:
            items_entity = entities.Annotation

        paged = entities.PagedEntities(
            items_repository=self,
            filters=filters,
            page_offset=page_offset,
            page_size=page_size,
            client_api=self.client_api,
            item_entity=items_entity
        )
        paged.get_page()
        return paged

    def get(self, filepath=None, item_id=None):
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :return: Item object
        """
        if item_id is not None:
            success, response = self.client_api.gen_request(
                req_type="get",
                path="/datasets/%s/items/%s" % (self.dataset.id, item_id),
            )
            if success:
                item = self.items_entity.from_json(
                    client_api=self.client_api,
                    _json=response.json(),
                    dataset=self.dataset,
                )
            else:
                self.logger.exception(
                    "Unable to get info from item. dataset id: %s, item id: %s"
                    % (self.dataset.id, item_id)
                )
                raise PlatformException(response)
        elif filepath is not None:
            filters = entities.Filters()
            filters.add(field='filename', values=filepath)
            paged_entity = self.list(filters=filters)
            if len(paged_entity.items) == 0:
                raise PlatformException(error='404', message='Item not found. filepath= "{}"'.format(filepath))
            elif len(paged_entity.items) > 1:
                raise PlatformException(error='404',
                                        message='More than one item found. Please "get" by id. filepath: "{}"'.format(
                                            filepath))
            else:
                item = paged_entity.items[0]
        else:
            raise PlatformException(error="400",
                                    message='Must choose by at least one. "filename" or "item_id"')
        return item

    def delete(self, filename=None, item_id=None, filters=None):
        """
        Delete item from platform

        :param filters: optional - delete items by filter
        :param filename: optional - search item by remote path
        :param item_id: optional - search item by id
        :return: True
        """
        if item_id is not None:
            success, response = self.client_api.gen_request(
                req_type="delete",
                path="/datasets/%s/items/%s" % (self.dataset.id, item_id),
            )
        elif filename is not None:
            if not filename.startswith("/"):
                filename = "/" + filename
            items = self.get(filepath=filename)
            if not isinstance(items, list):
                items = [items]
            if len(items) == 0:
                raise PlatformException("404", "Item not found")
            elif len(items) > 1:
                raise PlatformException(
                    "404", "More the 1 item exist by the name provided"
                )
            else:
                item_id = items[0].id
                success, response = self.client_api.gen_request(
                    req_type="delete",
                    path="/datasets/%s/items/%s" % (self.dataset.id, item_id),
                )
        elif filters is not None:
            # prepare request
            success, response = self.client_api.gen_request(req_type="POST",
                                                            path="/datasets/%s/query" % self.dataset.id,
                                                            json_req=filters.prepare(operation='delete'))
        else:
            raise PlatformException("400", "Must provide item id, filename or filters")

        # check response
        if success:
            self.logger.debug("Item/s deleted successfully")
            return success
        else:
            raise PlatformException(response)

    def update(self, item=None, filters=None, update_values=None, system_metadata=False):
        """
        Update items metadata

        :param update_values: optional field to be updated and new values
        :param filters: optional update filtered items by given filter
        :param item: Item object
        :param system_metadata: bool
        :return: Item object
        """
        # check params
        if item is None and filters is None:
            raise PlatformException('400', 'must provide either item or filters')
        if filters is not None and update_values is None:
            raise PlatformException('400', 'Must provide fields and values to update when updating by filter')
        if item is not None and filters is not None:
            raise PlatformException('400', 'must provide either item or filters')

        # update item
        if item is not None:
            url_path = "/datasets/%s/items/%s" % (self.dataset.id, item.id)
            if system_metadata:
                url_path += "?system=true"
            success, response = self.client_api.gen_request(
                req_type="patch", path=url_path, json_req=item.to_json()
            )
            if success:
                self.logger.debug("Item was updated successfully. Item id: %s" % item.id)
                return self.items_entity.from_json(
                    client_api=self.client_api, _json=response.json(), dataset=self.dataset
                )
            else:
                self.logger.exception("Error while updating item")
                raise PlatformException(response)
        # update by filters
        else:
            # prepare request
            success, response = self.client_api.gen_request(req_type="POST",
                                                            path="/datasets/%s/query" % self.dataset.id,
                                                            json_req=filters.prepare(operation='update',
                                                                                     update=update_values))
            if not success:
                raise PlatformException(response)
            else:
                self.logger.debug("Items were updated successfully.")
                # return self.items_entity.from_json(
                #     client_api=self.client_api, _json=response.json(), dataset=self.dataset
                # )
                return response.json()

    def download(
            self,
            filters=None,
            items=None,
            # download options
            local_path=None,
            file_types=None,
            download_options=None,
            save_locally=True,
            num_workers=None,
            annotation_options=None,
            opacity=None,
            with_text=None,
            thickness=None,
    ):
        """
            Download dataset by filters or by items id (or a list of)
            Filtering the dataset for items and save them local
            Optional - also download annotation, mask, instance and image mask of the item

        :param items: download Item entity or item_id (or a list of item)
        :param filters: Filters entity or a dictionary containing filters parameters
        :param local_path: local folder or filename to save to. if folder ends with * images with be downloaded directly
                            to folder. else - an "images" folder will be create for the images
        :param file_types: a list of file type to download. e.g ['.jpg', '.png']
        :param num_workers: default - 32
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param save_locally: bool. save to disk or return a buffer
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :return: Output (list)
        """
        downloader = repositories.Downloader(self)
        return downloader.download(
            filters=filters,
            items=items,
            local_path=local_path,
            file_types=file_types,
            download_options=download_options,
            save_locally=save_locally,
            num_workers=num_workers,
            annotation_options=annotation_options,
        )

    def upload(
            self,
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path=None,
            upload_options=None,
            file_types=None,
            # config
            num_workers=None,
    ):
        """
        Upload local file/s, folder/s or binary/is to dataset.
        Local structure will remain. (upload_options['relative_path'] will upload with/out containing folder)

        :param local_path: local file, folder or binary to upload (or a list of)
        :param local_annotations_path: path to dataloop format annotations json files or a AnnotationCollection entity
                                       if directory - annotations need to be in same files structure as "local_path"
        :param remote_path: remote path (on dataloop platform) to upload to.
        :param upload_options: {'overwrite': True/False, 'relative_path': True/False} - default -> overwrite = False, relative_path = False
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers: number of processes - default = 3
        :return: Output (list)
        """
        if remote_path is not None:
            if not remote_path.startswith('/'):
                remote_path = '/' + remote_path
        uploader = repositories.Uploader(self)
        return uploader.upload(
            local_path=local_path,
            local_annotations_path=local_annotations_path,
            # upload options
            remote_path=remote_path,
            upload_options=upload_options,
            file_types=file_types,
            # config
            num_workers=num_workers,
        )
