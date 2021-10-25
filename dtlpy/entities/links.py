from .. import entities
from .. import PlatformException
from enum import Enum
import os
import mimetypes


class LinkTypeEnum(str, Enum):
    """
    State enum
    """
    ID = "id"
    URL = "url"


class Link:

    # noinspection PyShadowingBuiltins
    def __init__(self, name, type: LinkTypeEnum, ref, mimetype=None, dataset_id=None):
        self.type = type
        self.ref = ref
        self.name = name
        self.dataset_id = dataset_id
        self.mimetype = mimetype


class UrlLink(Link):

    def __init__(self, ref, mimetype=None, name=None):
        if name is None:
            name = os.path.split(ref)[-1].replace('/', "").replace("\\", '').replace('.', '')
            name = name.split('?')[0]
        # noinspection PyShadowingBuiltins
        type = LinkTypeEnum.URL
        if not mimetype:
            mimetype = mimetypes.guess_type(ref.split('?')[0])[0] or 'image'
        super().__init__(name=name, type=type, mimetype=mimetype, ref=ref)

    @staticmethod
    def from_list(url_list):
        url_links = list()
        for url in url_list:
            url_links.append(UrlLink(ref=url))
        return url_links


class ItemLink(Link):

    def __init__(self, ref=None, name=None, dataset_id=None, item=None):
        if ref is None and item is None:
            raise PlatformException('400', 'Must provide either ref or item_id')

        if item is not None and not isinstance(item, entities.Item):
            raise PlatformException('400', 'Param item must be of type Item')

        if ref is None:
            ref = item.id

        if name is None:
            if item is not None:
                name = item.name
            else:
                name = ref

        if dataset_id is None and item is not None and isinstance(item, entities.Item):
            dataset_id = item.dataset_id

        # noinspection PyShadowingBuiltins
        type = LinkTypeEnum.ID
        super().__init__(name=name, type=type, ref=ref, dataset_id=dataset_id)

    @staticmethod
    def from_list(items):
        if not isinstance(items, list):
            items = [items]

        item_links = list()
        for item in items:
            if isinstance(item, str):
                item_links.append(ItemLink(ref=item))
            elif isinstance(item, entities.Item):
                item_links.append(ItemLink(item=item))
            else:
                raise PlatformException('400', 'Unknown item type. items should be a list of item entities/item ids')
        return item_links
