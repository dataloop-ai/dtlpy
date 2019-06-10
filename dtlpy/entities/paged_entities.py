import logging
from .. import entities, utilities
import attr

logger = logging.getLogger('dataloop.package')
@attr.s
class PagedEntities:
    """
    Pages object
    """
    page_offset = attr.ib()
    page_size = attr.ib()
    query = attr.ib()
    items_repository = attr.ib()
    client_api = attr.ib()
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
            self.items = utilities.List(
                [self.item_entity.from_json(client_api=self.client_api,
                                            _json=_json,
                                            dataset=self.items_repository.dataset)
                 for _json in result['items']])

    def __iter__(self):
        self.page_offset = 0
        self.has_next_page = True
        while self.has_next_page:
            self.get_page()
            self.page_offset += 1
            yield self.items

    def get_page(self):
        result = self.items_repository.get_list(query=self.query,
                                                page_offset=self.page_offset,
                                                page_size=self.page_size)
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
