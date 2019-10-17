import logging
import traceback
from multiprocessing.pool import ThreadPool

from .. import entities, PlatformException, repositories, utilities

logger = logging.getLogger(name=__name__)


class Items:
    """
    Items repository
    """

    def __init__(self, client_api, dataset=None, items_entity=None):
        self._client_api = client_api
        self._dataset = dataset
        # set items entity to represent the item (Item, Package, Artifact etc...)
        if items_entity is None:
            self.items_entity = entities.Item

    @property
    def dataset(self):
        if self._dataset is None:
            raise PlatformException(
                error='400',
                message='Cannot perform action WITHOUT Dataset entity in Items repository. Please set a dataset')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    def set_items_entity(self, entity):
        if entity in [entities.Item, entities.Artifact, entities.Package]:
            self.items_entity = entity
        else:
            raise PlatformException(error="403",
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

        def get_page(w_page, i_start, w_items):
            try:
                for item in w_page:
                    w_items[i_start] = item
                    i_start += 1
            except Exception:
                logger.exception(traceback.format_exc())

        items = [None for _ in range(num_items)]
        pool = ThreadPool(processes=32)
        i_item = 0
        for page in pages:
            pool.apply_async(get_page, kwds={"i_start": i_item,
                                             "w_page": page,
                                             "w_items": items})
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
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(self.dataset.id),
                                                         json_req=filters.prepare())
        if not success:
            raise PlatformException(response)
        try:
            self._client_api.print_json(response.json()["items"])
            logger.debug("Page:{}/{}".format(1 + filters.page, response.json()["totalPagesCount"]))
        except ValueError:
            # no JSON returned
            pass
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
            raise PlatformException('400', 'Unknown filters type')

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

    def get(self, filepath=None, item_id=None):
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :return: Item object
        """
        if item_id is not None:
            success, response = self._client_api.gen_request(req_type="get",
                                                             path="/items/{}".format(item_id))
            if success:
                item = self.items_entity.from_json(client_api=self._client_api,
                                                   _json=response.json(),
                                                   dataset=self._dataset)
            else:
                raise PlatformException(response)
        elif filepath is not None:
            filters = entities.Filters()
            filters.show_hidden = True
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
        assert isinstance(item, entities.Item)
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
                raise PlatformException("404", "Item not found")
            elif len(items) > 1:
                raise PlatformException(error="404", message="More the 1 item exist by the name provided")
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
            raise PlatformException("400", "Must provide item id, filename or filters")

        # check response
        if success:
            logger.debug("Item/s deleted successfully")
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
            json_req = utilities.miscellaneous.DictDiffer.diff(origin=item._platform_dict,
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
                logger.exception("Error while updating item")
                raise PlatformException(response)
        # update by filters
        else:
            # prepare request
            success, response = self._client_api.gen_request(req_type="POST",
                                                             path="/datasets/{}/query".format(self.dataset.id),
                                                             json_req=filters.prepare(operation='update',
                                                                                      update=update_values))
            if not success:
                raise PlatformException(response)
            else:
                logger.debug("Items were updated successfully.")
                # return self.items_entity.from_json(
                #     client_api=self._client_api, _json=response.json(), dataset=self.dataset
                # )
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
            with_text=False
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
            with_text=with_text
        )

    def upload(
            self,
            # what to upload
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path="/",
            file_types=None,
            num_workers=32,
            overwrite=False,
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param overwrite: optional - default = False
        :param local_path: list of local file, local folder, BufferIO, or url to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers:
        :return: Output (list)
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
            file_types=file_types,
            # config
            num_workers=num_workers,
            overwrite=overwrite,
        )

    def open_in_web(self, filepath=None, item_id=None, item=None):
        import webbrowser
        if self._client_api.environment == 'https://gate.dataloop.ai/api/v1':
            head = 'https://console.dataloop.ai'
        elif self._client_api.environment == 'https://dev-gate.dataloop.ai/api/v1':
            head = 'https://dev-con.dataloop.ai'
        else:
            raise PlatformException('400', 'Please provide environment')
        if item is None:
            item = self.get(filepath=filepath, item_id=item_id)
        item_url = head + '/projects/{}/datasets/{}/annotation/{}'.format(item.dataset.project.id,
                                                                          item.dataset.id,
                                                                          item.id)
        webbrowser.open(url=item_url, new=2, autoraise=True)
