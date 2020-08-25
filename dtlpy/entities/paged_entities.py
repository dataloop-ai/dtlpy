import logging
import math
import copy
import attr
from .. import services, miscellaneous

logger = logging.getLogger(name=__name__)


@attr.s
class PagedEntities:
    """
    Pages object
    """
    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)

    # params
    page_offset = attr.ib()
    page_size = attr.ib()
    filters = attr.ib()
    items_repository = attr.ib(repr=False)
    has_next_page = attr.ib(default=False)
    total_pages_count = attr.ib(default=0)
    items_count = attr.ib(default=0)

    # execution attribute
    _service_id = attr.ib(default=None, repr=False)
    _project_id = attr.ib(default=None, repr=False)
    _order_by_type = attr.ib(default=None, repr=False)
    _order_by_direction = attr.ib(default=None, repr=False)
    _execution_status = attr.ib(default=None, repr=False)
    _execution_resource_type = attr.ib(default=None, repr=False)
    _execution_resource_id = attr.ib(default=None, repr=False)
    _execution_function_name = attr.ib(default=None, repr=False)

    # items list
    items = attr.ib(default=miscellaneous.List(), repr=False)

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
            items = self.items_repository._build_entities_from_response(response_items=result['items'])
        else:
            items = miscellaneous.List(list())
        return items

    def __getitem__(self, y):
        self.go_to_page(y)
        return self.items

    def __len__(self):
        return self.items_count

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

    def return_page(self, page_offset=None, page_size=None):
        if page_size is None:
            page_size = self.page_size
        if page_offset is None:
            page_offset = self.page_offset

        if self.filters is not None:
            filters = copy.copy(self.filters)
            filters.page = page_offset
            filters.page_size = page_size
            result = self.items_repository._list(filters=filters)
            items = self.process_result(result)
            return items
        else:
            raise ValueError('Cant return page. Filters is empty')

    def get_page(self, page_offset=None, page_size=None):
        items = self.return_page(page_offset=page_offset,
                                 page_size=page_size)
        self.items = items

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

    def all(self):
        page_offset = 0
        page_size = 100
        total_pages = math.ceil(self.items_count / page_size)
        jobs = list()
        pool = self._client_api.thread_pools('item.page')
        while True:
            if page_offset <= total_pages:
                jobs.append(pool.apply_async(self.return_page, kwds={'page_offset': page_offset,
                                                                     'page_size': page_size}))
                page_offset += 1
            for i_job, job in enumerate(jobs):
                if job.ready():
                    for item in job.get():
                        yield item
                    jobs.remove(job)
            if len(jobs) == 0:
                break

    ########
    # misc #
    ########
    def print(self, columns=None):
        self.items.print(columns=columns)

    def to_df(self, columns=None):
        self.items.to_df(columns=columns)
