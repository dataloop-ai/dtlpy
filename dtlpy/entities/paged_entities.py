import logging
from .. import entities, repositories, utilities

logger = logging.getLogger('dataloop.package')


class PagedEntities:
    """
    Pages object
    """

    def __init__(self, items, query, page_offset, page_size):
        self.items_repository = items
        self.query = query
        self.__has_next_page = False
        self.__total_pages_count = 0
        self.__total_items_count = 0
        self.__page_offset = page_offset
        self.__page_size = page_size
        self.__items = utilities.List()

    def process_result(self, result):
        if 'page_offset' in result:
            self.__page_offset = result['page_offset']
        if 'page_size' in result:
            self.__page_size = result['page_size']
        if 'hasNextPage' in result:
            self.__has_next_page = result['hasNextPage']
        if 'totalItemsCount' in result:
            self.__total_items_count = result['totalItemsCount']
        if 'totalPagesCount' in result:
            self.__total_pages_count = result['totalPagesCount']
        if 'items' in result:
            self.__items = utilities.List(
                [entities.Item(entity_dict=entity_dict, dataset=self.items_repository.dataset) for entity_dict
                 in result['items']])

    def __iter__(self):
        self.__page_offset = 0
        self.__has_next_page = True
        while self.__has_next_page:
            self.get_page()
            self.__page_offset += 1
            yield self.items

    def get_page(self):
        result = self.items_repository.get_list(query=self.query,
                                                page_offset=self.__page_offset,
                                                page_size=self.__page_size)
        self.process_result(result)

    def print(self):
        self.items.print()

    @property
    def items(self):
        return self.__items

    @property
    def pages_count(self):
        return self.__total_pages_count

    @property
    def items_count(self):
        return self.__total_items_count

    def next_page(self):
        self.__page_offset += 1
        self.get_page()

    def prev_page(self):
        self.__page_offset -= 1
        self.get_page()

    def go_to_page(self, page=0):
        self.__page_offset = page
        self.get_page()
