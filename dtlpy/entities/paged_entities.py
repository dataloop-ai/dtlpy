import logging
import math
import time
import tqdm
import copy
import sys
from typing import Optional, List, Any

import attr

from .filters import FiltersOperations, FiltersOrderByDirection, FiltersResource
from .. import miscellaneous, exceptions
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


@attr.s
class PagedEntities:
    """
    Pages object for efficient API pagination.
    Defaults to offset-based pagination for compatibility with all operations.
    Switches to keyset/cursor-based pagination (using 'id' as the cursor) during iteration for performance.
    Falls back to offset-based pagination if keyset is not possible (e.g., custom sort).
    """
    # api
    _client_api: ApiClient = attr.ib(repr=False)

    # params
    page_offset: int = attr.ib()
    page_size: int = attr.ib()
    filters: Any = attr.ib()
    items_repository: Any = attr.ib(repr=False)
    has_next_page: bool = attr.ib(default=False)
    total_pages_count: int = attr.ib(default=0)
    items_count: int = attr.ib(default=0)

    # hybrid pagination
    use_id_based_paging: bool = attr.ib(default=False)  # Default to False for offset-based pagination
    last_seen_id: Optional[Any] = attr.ib(default=None)

    # execution attribute
    _service_id = attr.ib(default=None, repr=False)
    _project_id = attr.ib(default=None, repr=False)
    _list_function = attr.ib(default=None, repr=False)

    # items list
    items: List[Any] = attr.ib(default=miscellaneous.List(), repr=False)

    @staticmethod
    def _has_explicit_sort(flt) -> bool:
        """
        Check if the filter has custom sort fields defined (not id/createdAt).
        """
        prepared = flt.prepare() if flt else {}
        sort_fields = list(prepared.get("sort", {}).keys())
        if isinstance(sort_fields, list) and len(sort_fields) > 0:
            return sort_fields[0] not in {"id", "createdAt"}
        return False

    def _should_use_keyset_pagination(self) -> bool:
        """
        Determine whether to use keyset pagination based on page offset and resource type.
        Keyset pagination can only be used when page_offset is 0 (first page).
        :param page_offset: The page offset to check
        :return: True if keyset pagination should be used, False otherwise
        """
        # Keyset pagination only works for page 0 (first page)
        if self.page_offset != 0:
            return False
                
        # can't use add to custom filter
        if self.filters.custom_filter is not None:
            return False
        
        # Check if the resource supports keyset pagination
        enable_id_based_paging = getattr(self.filters, "resource", None) in [
            FiltersResource.ITEM,
            FiltersResource.ANNOTATION,
            FiltersResource.FEATURE,
        ]
        
        if not enable_id_based_paging:
            return False
            
        # Check if there's no explicit sort that would prevent keyset pagination
        if self._has_explicit_sort(self.filters):
            return False
            
        return True

    def process_result(self, result: dict) -> List[Any]:
        """
        Process the API result and update pagination state.
        :param result: json object
        :return: list of items
        """
        # Only update page_offset if using offset-based pagination
        if not self.use_id_based_paging and 'page_offset' in result:
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

    def __getitem__(self, y: int) -> List[Any]:
        # If we're already on the requested page, return current items
        if y == self.page_offset:
            return self.items
        # Otherwise, go to the requested page
        self.go_to_page(y)
        return self.items

    def __len__(self) -> int:
        return self.items_count

    def __iter__(self):
        # Use keyset/cursor-based pagination for iteration when possible
        self.last_seen_id = None
        self.page_offset = 0  # Start from the first page for iteration
        self.use_id_based_paging = self._should_use_keyset_pagination()
        self.has_next_page = True  # Start with assumption that there are more pages
        self.page_size = self.page_size or 100
        pbar = tqdm.tqdm(total=self.items_count,
                         disable=self._client_api.verbose.disable_progress_bar_iterate_pages,
                         file=sys.stdout, desc="Iterate Pages")
        
        # Get the first page
        self.get_page()
        if self.items:
            yield self.items
            pbar.update()
        
        # Continue with next pages
        while self.has_next_page:
            if self.use_id_based_paging:
                # For keyset pagination, just get the next page
                self.page_offset = 0
                self.get_page()
            else:
                # For offset pagination, increment the offset
                self._move_page_offset(1)
                self.get_page()
            
            if not self.items:
                break
            yield self.items
            pbar.update()
        pbar.close()

    def __reversed__(self):
        # Force offset-based pagination for reverse iteration
        self.use_id_based_paging = False
        self.page_offset = self.total_pages_count - 1
        while True:
            self.get_page()
            yield self.items
            if self.page_offset == 0:
                break
            self._move_page_offset(-1)

    def _move_page_offset(self, offset: int) -> None:
        """
        Move the page offset by a given step.
        :param offset: offset to move
        """
        self.page_offset += offset
        if self.filters.custom_filter is not None:
            if 'page' in self.filters.custom_filter and self.filters.custom_filter['page'] != self.page_offset:
                self.filters.custom_filter['page'] = self.page_offset

    def return_page(self, page_offset: Optional[int] = None, page_size: Optional[int] = None) -> List[Any]:
        """
        Return a page of results using offset-based pagination by default.
        Switches to keyset/cursor-based pagination when supported and beneficial.
        :param page_offset: page offset (for offset-based)
        :param page_size: page size
        :return: list of items
        """
        if page_size is not None:
            self.page_size = page_size
        if page_offset is not None:
            self.page_offset = page_offset

        if self.filters is None:
            raise ValueError("Can't return page. Filters is empty")
        self.filters.page_size = self.page_size
        self.filters.page = self.page_offset
        req = copy.deepcopy(self.filters)

        # Determine pagination method based on page offset and resource type
        self.use_id_based_paging = self._should_use_keyset_pagination()

        if self.use_id_based_paging:
            # Use keyset/cursor-based pagination
            prepared = req.prepare()
            sort_spec = prepared.get("sort", {})
            order = next(iter(sort_spec.values()), None)
            if order is None:
                order = FiltersOrderByDirection.ASCENDING
            if order == FiltersOrderByDirection.DESCENDING:
                operator_value = FiltersOperations.LESS_THAN
            else:
                operator_value = FiltersOperations.GREATER_THAN
                
            req.sort_by(field="id", value=order)
            req.page = 0  # always fetch from the start for keyset
            # Only add last_seen_id filter if we're not explicitly requesting page 0
            if self.last_seen_id:
                req.add(
                    field="id",
                    values=self.last_seen_id,
                    operator=operator_value,
                    method=FiltersOperations.AND,
                )
        # Fetch data
        if self._list_function is None:
            result = self.items_repository._list(filters=req)
        else:
            result = self._list_function(filters=req)

        items = self.process_result(result)

        # Update last_seen_id for keyset
        if self.use_id_based_paging and items and hasattr(items[-1], "id"):
            self.last_seen_id = items[-1].id
        elif self.use_id_based_paging and not items:
            self.last_seen_id = None
        return items

    def get_page(self, page_offset: Optional[int] = None, page_size: Optional[int] = None) -> None:
        """
        Get a page of results and update self.items.
        :param page_offset: page offset (for offset-based)
        :param page_size: page size
        """
        try:
            items = self.return_page(page_offset=page_offset, page_size=page_size)
            self.items = items
        except exceptions.BadRequest as e:
            logger.warning(f"BadRequest error received: {str(e)}")
            self.items = miscellaneous.List(list())

    def next_page(self) -> None:
        """
        Brings the next page of items from host.
        """
        if self.use_id_based_paging:
            # For keyset pagination, just get the next page
            self.get_page()
        else:
            # For offset pagination, increment the offset
            self._move_page_offset(1)
            self.get_page()

    def prev_page(self) -> None:
        """
        Brings the previous page of items from host.
        Only works with offset-based pagination.
        """
        if self.use_id_based_paging:
            raise NotImplementedError("prev_page is not supported for keyset pagination.")
        self._move_page_offset(-1)
        self.get_page()

    def go_to_page(self, page: int = 0) -> None:
        """
        Brings specified page of items from host.
        For page 0, uses keyset pagination if supported.
        For other pages, uses offset-based pagination.
        :param page: page number
        """
        # Reset last_seen_id when going to page 0 to ensure we get all items
        if page == 0:
            self.last_seen_id = None
        self.page_offset = page
        self.get_page()

    def all(self):
        """
        Iterate over all items in all pages efficiently.
        Uses the iterator implementation (__iter__).
        """
        for items in self:
            for item in items:
                yield item

    ########
    # misc #
    ########
    def print(self, columns=None):
        self.items.print(columns=columns)

    def to_df(self, columns=None):
        return self.items.to_df(columns=columns)