import logging
import attr
from multiprocessing.pool import ThreadPool

from .. import entities, utilities, services

logger = logging.getLogger(name=__name__)


@attr.s
class PagedEntities:
    """
    Pages object
    """
    # api
    _client_api = attr.ib(type=services.ApiClient)

    # params
    page_offset = attr.ib()
    page_size = attr.ib()
    filters = attr.ib()
    items_repository = attr.ib()
    item_entity = attr.ib(default=entities.Item)
    has_next_page = attr.ib(default=False)
    total_pages_count = attr.ib(default=0)
    items_count = attr.ib(default=0)

    # items list
    items = attr.ib(default=utilities.List())

    def process_result(self, result):
        if 'page_offset' in result:
            self.page_offset = result['page_offset']
        if 'page_size' in result:
            self.page_size = result['page_size']
        if 'hasNextPage' in result:
            self.has_next_page = result['hasNextPage']
        if 'totalItemsCount' in result:
            self.items_count = result['totalItemsCount']
        if 'totalPagesCount' in result:
            self.total_pages_count = result['totalPagesCount']
        if 'items' in result:
            if self.filters.resource == 'items':
                self.items = utilities.List(
                    [self.item_entity.from_json(client_api=self._client_api,
                                                _json=_json,
                                                dataset=self.items_repository.dataset)
                     for _json in result['items']])
            if self.filters.resource == 'annotations':
                self.load_annotations(result=result)

    def __iter__(self):
        self.page_offset = 0
        self.has_next_page = True
        while self.has_next_page:
            self.get_page()
            self.page_offset += 1
            yield self.items

    def __reversed__(self):
        self.page_offset = self.total_pages_count - 1
        while True:
            self.get_page()
            yield self.items
            if self.page_offset == 0:
                break
            self.page_offset -= 1

    def get_page(self):
        self.filters.page = self.page_offset
        self.filters.page_size = self.page_size
        result = self.items_repository.get_list(filters=self.filters)
        self.process_result(result)

    def print(self):
        self.items.print()

    def next_page(self):
        """
        Brings the next page of items from host

        :return:
        """
        self.page_offset += 1
        self.get_page()

    def prev_page(self):
        """
        Brings the previous page of items from host

        :return:
        """
        self.page_offset -= 1
        self.get_page()

    def go_to_page(self, page=0):
        """
        Brings specified page of items from host

        :param page: page number
        :return:
        """
        self.page_offset = page
        self.get_page()

    def load_single_annotation(self, i_json, _json, items, annotations):
        if _json['itemId'] not in items:
            items[_json['itemId']] = self.items_repository.get(item_id=_json['itemId'])
        annotations[i_json] = self.item_entity.from_json(item=items[_json['itemId']], _json=_json)

    def load_annotations(self, result):
        items = dict()
        annotations = [None] * len(result['items'])
        pool = ThreadPool(processes=32)
        for i_json, _json in enumerate(result['items']):
            pool.apply_async(
                self.load_single_annotation,
                kwds={"i_json": i_json, "_json": _json, "items": items, "annotations": annotations}
            )
        pool.close()
        pool.join()
        pool.terminate()
        self.items = utilities.List(annotations)
