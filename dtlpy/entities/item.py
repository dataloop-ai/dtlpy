import logging
import copy
from .. import repositories, utilities, PlatformException
import attr

logger = logging.getLogger('dataloop.item')


@attr.s
class Item:
    """
    Item object
    """
    # platform
    client_api = attr.ib()
    id = attr.ib()
    annotations_link = attr.ib()
    stream = attr.ib()
    thumbnail = attr.ib()
    metadata = attr.ib()
    url = attr.ib()
    system = attr.ib()
    platform_dict = attr.ib()
    created_at = attr.ib()

    # params
    annotated = attr.ib()
    filename = attr.ib()
    mimetype = attr.ib()
    name = attr.ib()
    size = attr.ib()
    type = attr.ib()
    fps = attr.ib()

    # entities
    dataset = attr.ib()

    # repositories
    _annotations = attr.ib()

    # defaults
    width = attr.ib()
    height = attr.ib()

    @classmethod
    def from_json(cls, _json, dataset, client_api):
        """
        Build an item entity object from a json
        :param _json: _json response form host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: client_api
        :return: Item object
        """
        if _json['type'] == 'dir':
            return cls(
                client_api=client_api,
                dataset=dataset,
                annotated=None,
                annotations_link=None,
                stream=None,
                thumbnail=None,
                url=_json['url'],
                filename=_json['filename'],
                id=_json['id'],
                metadata=_json['metadata'],
                mimetype=None,
                name=_json['name'],
                size=None,
                system=None,
                type=_json['type'],
                fps=None,
                platform_dict=copy.deepcopy(_json),
                created_at=_json.get('createdAt', None))
        elif _json['type'] == 'file':
            fps = _json.get('fps', None)
            if fps is None and 'metadata' in _json:
                fps = _json['metadata'].get('fps', None)
            return cls(
                client_api=client_api,
                dataset=dataset,
                annotated=_json['annotated'],
                annotations_link=_json['annotations'],
                stream=_json['stream'],
                thumbnail=_json['thumbnail'],
                url=_json['url'],
                filename=_json['filename'],
                id=_json['id'],
                metadata=_json['metadata'],
                mimetype=_json['metadata']['system']['mimetype'],
                name=_json['name'],
                size=_json['metadata']['system']['size'],
                system=_json['metadata']['system'],
                type=_json['type'],
                fps=fps,
                platform_dict=copy.deepcopy(_json),
                created_at=_json.get('createdAt', None))
        else:
            message = 'Unknown item type: %s' % _json['type']
            raise PlatformException('404', message)

    @_annotations.default
    def set_annotations(self):
        return repositories.Annotations(dataset=self.dataset, item=self, client_api=self.client_api)

    @property
    def annotations(self):
        assert isinstance(self._annotations, repositories.Annotations)
        return self._annotations

    @height.default
    def set_height(self):
        height = None
        if self.system is not None and 'height' in self.system:
            height = self.system['height']
        return height

    @width.default
    def set_width(self):
        width = None
        if self.system is not None and 'width' in self.system:
            width = self.system['width']
        return width

    def set_metadata(self, metadata):
        self.metadata = metadata

    def to_json(self):
        """
        Returns platform _json format of object
        :return: platform json format of object
        """
        if self.type == 'dir':
            _json = attr.asdict(self,
                                filter=attr.filters.include(attr.fields(Item).id,
                                                            attr.fields(Item).filename,
                                                            attr.fields(Item).type,
                                                            attr.fields(Item).metadata,
                                                            attr.fields(Item).name,
                                                            attr.fields(Item).url))
        elif self.type == 'file':
            _json = attr.asdict(self,
                                filter=attr.filters.include(attr.fields(Item).id,
                                                            attr.fields(Item).filename,
                                                            attr.fields(Item).type,
                                                            attr.fields(Item).metadata,
                                                            attr.fields(Item).name,
                                                            attr.fields(Item).url,
                                                            attr.fields(Item).annotated,
                                                            attr.fields(Item).thumbnail,
                                                            attr.fields(Item).stream))
            _json.update({'annotations': self.annotations_link})
        else:
            message = 'Unknown item type: %s' % self.type
            raise PlatformException('404', message)
        _json['createdAt'] = self.created_at
        return _json

    def from_dict(self, metadata):
        # does nothing
        return

    def print(self):
        utilities.List([self]).print()

    def download(
            self,
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
        :param to_items_folder: Create 'items' folder and download items to it
        :param overwrite: optional - default = False
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param num_workers: default - 32
        :param save_locally: bool. save to disk or return a buffer
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param with_text: optional - add text to annotations, default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :return: Output (list)
        """
        return self.dataset.items.download(items=self,
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

    def delete(self):
        """
        Delete item from platform
        :return: True
        """
        return self.dataset.items.delete(item_id=self.id)

    def update(self, system_metadata=False):
        """
        Update items metadata
        :param system_metadata: bool
        :return: Item object
        """
        return self.dataset.items.update(item=self, system_metadata=system_metadata)

    def move(self, new_path):
        """
        Move item from one folder to another in Platform
        :param new_path: new path to move item to. Format: /main_folder/sub_folder/.../item_name.type
        :return: True
        """
        assert isinstance(new_path, str)
        if not new_path.startswith('/'):
            new_path = '/' + new_path
        if '.' in new_path:
            if len(new_path.split('.')) > 2:
                raise PlatformException('400', 'Remote path cannot include dots')
            else:
                self.filename = new_path
        else:
            self.filename = new_path + '/' + self.name

        return self.update(system_metadata=True)

    def open_in_web(self):
        self.dataset.items.open_in_web(item=self)
