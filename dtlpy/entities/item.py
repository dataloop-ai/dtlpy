from collections import namedtuple
import traceback
import logging
import attr
import copy
import os

from .. import repositories, miscellaneous, entities, services, PlatformException

logger = logging.getLogger(name=__name__)


@attr.s
class Item:
    """
    Item object
    """
    # item information
    annotations_link = attr.ib()
    dataset_url = attr.ib()
    thumbnail = attr.ib()
    createdAt = attr.ib()
    datasetId = attr.ib()
    annotated = attr.ib()
    metadata = attr.ib()
    filename = attr.ib()
    stream = attr.ib()
    name = attr.ib()
    type = attr.ib()
    url = attr.ib()
    id = attr.ib()
    hidden = attr.ib()
    dir = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient)
    _platform_dict = attr.ib()

    # entities
    _dataset = attr.ib()

    # repositories
    _repositories = attr.ib()
    modalities = attr.ib()

    @staticmethod
    def _protected_from_json(_json, client_api, dataset=None):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param dataset:
        :return:
        """
        try:
            item = Item.from_json(_json=_json,
                                  client_api=client_api,
                                  dataset=dataset)
            status = True
        except Exception:
            item = traceback.format_exc()
            status = False
        return status, item

    @classmethod
    def from_json(cls, _json, client_api, dataset=None):
        """
        Build an item entity object from a json
        :param _json: _json response form host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: client_api
        :return: Item object
        """
        metadata = _json.get('metadata', dict())
        return cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            # params
            annotations_link=_json.get('annotations', None),
            thumbnail=_json.get('thumbnail', None),
            datasetId=_json.get('datasetId', None),
            annotated=_json.get('annotated', None),
            dataset_url=_json.get('dataset', None),
            createdAt=_json.get('createdAt', None),
            hidden=_json.get('hidden', False),
            stream=_json.get('stream', None),
            dir=_json.get('dir', None),
            filename=_json['filename'],
            metadata=metadata,
            name=_json['name'],
            type=_json['type'],
            url=_json['url'],
            id=_json['id'])

    def to_json(self):
        """
        Returns platform _json format of object
        :return: platform json format of object
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Item)._repositories,
                                                        attr.fields(Item)._dataset,
                                                        attr.fields(Item).modalities,
                                                        attr.fields(Item)._client_api,
                                                        attr.fields(Item)._platform_dict,
                                                        attr.fields(Item).dataset_url,
                                                        attr.fields(Item).annotations_link))

        _json.update({'annotations': self.annotations_link,
                      'dataset': self.dataset_url})
        return _json

    @modalities.default
    def set_modalities(self):
        modalities = Modalities(item=self)
        assert isinstance(modalities, Modalities)
        return modalities

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['annotations', 'items', 'packages', 'artifacts'])
        reps.__new__.__defaults__ = (None, None, None, None)

        if self._dataset is None:
            items = repositories.Items(client_api=self._client_api,
                                       dataset=None,
                                       dataset_id=self.datasetId,
                                       datasets=repositories.Datasets(client_api=self._client_api, project=None))
        else:
            items = self.dataset.items

        r = reps(annotations=repositories.Annotations(client_api=self._client_api, item=self),
                 items=items)
        return r

    ##############
    # Properties #
    ##############
    @property
    def height(self):
        return self.metadata.get('system', dict()).get('height', None)

    @height.setter
    def height(self, val):
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system']['height'] = val

    @property
    def width(self):
        return self.metadata.get('system', dict()).get('width', None)

    @width.setter
    def width(self, val):
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system']['width'] = val

    @property
    def fps(self):
        return self.metadata.get('fps', None)

    @fps.setter
    def fps(self, val):
        self.metadata['fps'] = val

    @property
    def mimetype(self):
        return self.metadata.get('system', dict()).get('mimetype', None)

    @property
    def size(self):
        return self.metadata.get('system', dict()).get('size', None)

    @property
    def system(self):
        return self.metadata.get('system', dict())

    @property
    def annotations(self):
        assert isinstance(self._repositories.annotations, repositories.Annotations)
        return self._repositories.annotations

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = repositories.Datasets(client_api=self._client_api).get(dataset_id=self.datasetId)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    ###########
    # Methods #
    ###########
    def print(self):
        miscellaneous.List([self]).print()

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
        # if dir - concatenate local path and item name
        if local_path is not None:
            _, ext = os.path.splitext(local_path)
            if not ext:
                local_path = os.path.join(local_path, self.name)

        # download
        return self.items.download(items=self,
                                   local_path=local_path,
                                   file_types=file_types,
                                   save_locally=save_locally,
                                   num_workers=num_workers,
                                   annotation_options=annotation_options,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   thickness=thickness,
                                   with_text=with_text)

    def delete(self):
        """
        Delete item from platform
        :return: True
        """
        return self.items.delete(item_id=self.id)

    def update(self, system_metadata=False):
        """
        Update items metadata
        :param system_metadata: bool
        :return: Item object
        """
        return self.items.update(item=self, system_metadata=system_metadata)

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
        self.items.open_in_web(item=self)


class Modality:
    def __init__(self, _json=None, modality_type=None, ref=None, name=None):
        self.type = _json.get('type', modality_type)
        self.ref = _json.get('ref', ref)
        self.name = _json.get('name', name)


class Modalities:
    def __init__(self, item):
        assert isinstance(item, Item)
        self.item = item

    @property
    def modalities(self):
        return self.item.metadata.get('modalities', None)

    def create(self, name, ref, modality_type='overlay'):
        if self.modalities is None:
            self.item.metadata['modalities'] = list()

        _json = {
            "type": modality_type,
            "ref": ref,
            "name": name
        }

        self.item.metadata['modalities'].append(_json)

        return Modality(_json=_json)

    def delete(self, name):
        if self.modalities is not None:
            for modality in self.item.metadata['modalities']:
                if name == modality['name']:
                    self.item.metadata['modalities'].remove(modality)
                    return Modality(_json=modality)
        return None

    def list(self):
        modalities = list()
        if self.modalities is not None:
            modalities = list()
            for modality in self.item.metadata['modalities']:
                modalities.append(Modality(_json=modality))
        return modalities
