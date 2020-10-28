from collections import namedtuple
import traceback
import logging
import attr
import copy
import os

from .. import repositories, entities, services, exceptions

logger = logging.getLogger(name=__name__)


class ItemStatus:
    COMPLETED = "completed"
    APPROVED = "approved"
    DISCARDED = "discarded"


@attr.s
class Item(entities.BaseEntity):
    """
    Item object
    """
    # item information
    annotations_link = attr.ib(repr=False)
    dataset_url = attr.ib()
    thumbnail = attr.ib(repr=False)
    createdAt = attr.ib()
    datasetId = attr.ib()
    annotated = attr.ib(repr=False)
    metadata = attr.ib(repr=False)
    filename = attr.ib()
    stream = attr.ib(repr=False)
    name = attr.ib()
    type = attr.ib()
    url = attr.ib(repr=False)
    id = attr.ib()
    hidden = attr.ib(repr=False)
    dir = attr.ib(repr=False)

    # name change
    annotations_count = attr.ib()

    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _platform_dict = attr.ib(repr=False)

    # entities
    _dataset = attr.ib(repr=False)
    _project = attr.ib(repr=False)

    # repositories
    _repositories = attr.ib(repr=False)

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
    def from_json(cls, _json, client_api, dataset=None, project=None, is_fetched=True):
        """
        Build an item entity object from a json
        :param project:
        :param _json: _json response from host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: client_api
        :param is_fetched: is Entity fetched from Platform
        :return: Item object
        """
        if dataset is not None:
            if dataset.id != _json.get('datasetId', None):
                logger.warning('Item has been fetched from a dataset that is not belong to it')
                dataset = None

        metadata = _json.get('metadata', dict())
        inst = cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            project=project,
            # params
            annotations_link=_json.get('annotations', None),
            thumbnail=_json.get('thumbnail', None),
            datasetId=_json.get('datasetId', None),
            annotated=_json.get('annotated', None),
            dataset_url=_json.get('dataset', None),
            createdAt=_json.get('createdAt', None),
            annotations_count=_json.get('annotationsCount', None),
            hidden=_json.get('hidden', False),
            stream=_json.get('stream', None),
            dir=_json.get('dir', None),
            filename=_json.get('filename', None),
            metadata=metadata,
            name=_json.get('name', None),
            type=_json.get('type', None),
            url=_json.get('url', None),
            id=_json.get('id', None))
        inst.is_fetched = is_fetched
        return inst

    ############
    # entities #
    ############

    @property
    def dataset(self):
        if self._dataset is None:
            if self._dataset is None:
                self._dataset = self.datasets.get(dataset_id=self.datasetId, fetch=None)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def project(self):
        if self._project is None:
            if self._dataset is None:
                if self._dataset is None:
                    self._dataset = self.datasets.get(dataset_id=self.datasetId, fetch=None)
            self._project = self._dataset.project
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    ################
    # repositories #
    ################

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['annotations', 'datasets', 'items', 'codebases', 'artifacts', 'modalities'])
        reps.__new__.__defaults__ = (None, None, None, None, None, None)

        if self._dataset is None:
            items = repositories.Items(client_api=self._client_api,
                                       dataset=self._dataset,
                                       dataset_id=self.datasetId,
                                       datasets=repositories.Datasets(client_api=self._client_api, project=None))
            datasets = items.datasets
        else:
            items = self.dataset.items
            datasets = self.dataset.datasets

        r = reps(annotations=repositories.Annotations(client_api=self._client_api,
                                                      dataset_id=self.datasetId,
                                                      item=self,
                                                      dataset=self._dataset),
                 items=items,
                 datasets=datasets,
                 codebases=None,
                 artifacts=None,
                 modalities=Modalities(item=self))
        return r

    @property
    def modalities(self):
        assert isinstance(self._repositories.modalities, Modalities)
        return self._repositories.modalities

    @property
    def annotations(self):
        assert isinstance(self._repositories.annotations, repositories.Annotations)
        return self._repositories.annotations

    @property
    def datasets(self):
        assert isinstance(self._repositories.datasets, repositories.Datasets)
        return self._repositories.datasets

    @property
    def items(self):
        assert isinstance(self._repositories.items, repositories.Items)
        return self._repositories.items

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

    ###########
    # Functions #
    ###########
    def to_json(self):
        """
        Returns platform _json format of object
        :return: platform json format of object
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Item)._repositories,
                                                        attr.fields(Item)._dataset,
                                                        attr.fields(Item)._project,
                                                        attr.fields(Item)._client_api,
                                                        attr.fields(Item)._platform_dict,
                                                        attr.fields(Item).annotations_count,
                                                        attr.fields(Item).dataset_url,
                                                        attr.fields(Item).annotations_link))

        _json.update({'annotations': self.annotations_link,
                      'annotationsCount': self.annotations_count,
                      'dataset': self.dataset_url})
        return _json

    def download(
            self,
            # download options
            local_path=None,
            file_types=None,
            save_locally=True,
            to_array=False,
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

        :param local_path: local folder or filename to save to disk or returns BytelsIO
        :param to_items_folder: Create 'items' folder and download items to it
        :param overwrite: optional - default = False
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param num_workers: default - 32
        :param save_locally: bool. save to disk or return a buffer
        :param to_array: returns Ndarray when True and local_path = False
        :param annotation_options: download annotations options: dl.ViewAnnotationOptions.list()
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
                                   to_array=to_array,
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
        If the directory doesn't exist it will be created
        :param new_path: new full path to move item to.
        :return: True if update successfully
        """
        assert isinstance(new_path, str)
        if not new_path.startswith('/'):
            new_path = '/' + new_path
        if new_path.endswith('/'):
            self.filename = new_path + self.name
        else:
            try:
                self.items.get(filepath=new_path, is_dir=True)
                self.filename = new_path + '/' + self.name
            except exceptions.NotFound:
                self.filename = new_path

        return self.update(system_metadata=True)

    def clone(self, dst_dataset_id, remote_filepath=None, metadata=None, with_annotations=True,
              with_metadata=True, with_task_annotations_status=False):
        """
        Clone item
        :param dst_dataset_id: destination dataset id
        :param remote_filepath: complete filepath
        :param metadata: new metadata to add
        :param with_annotations: clone annotations
        :param with_metadata: clone metadata
        :param with_task_annotations_status: clone task annotations status
        :return: Item
        """
        if remote_filepath is None:
            remote_filepath = self.filename
        return self.items.clone(item_id=self.id,
                                dst_dataset_id=dst_dataset_id,
                                remote_filepath=remote_filepath,
                                metadata=metadata,
                                with_annotations=with_annotations,
                                with_metadata=with_metadata,
                                with_task_annotations_status=with_task_annotations_status)

    def open_in_web(self):
        self.items.open_in_web(item=self)

    def change_status(self, status):
        # TODO - deprecate
        logger.warning('[DeprecationWarning] "change_status(status)" method will be deprecated after version 1.17.0\n'
                       'Please use method "update_status(status)"')
        self.update_status(status=status)

    def update_status(self, status):
        if status not in ['completed', 'approved', 'discarded']:
            raise exceptions.PlatformException('400',
                                               'Unknown status: {}. Please chose from: completed, approved, discarded'
                                               .format(status))
        try:
            annotation_definition = entities.Classification(label=status)
            entities.Annotation.new(item=self,
                                    annotation_definition=annotation_definition,
                                    metadata={'system': {'system': True}}).upload()
            return True
        except Exception:
            logger.error('Error updating status. Please use platform')
            logger.debug(traceback.format_exc())
            return False


class ModalityTypeEnum:
    """
    State enum
    """

    OVERLAY = "overlay"


class Modality:
    def __init__(self, _json=None, modality_type=None, ref=None, ref_type='id', name=None):
        if _json is None:
            _json = dict()
        self.type = _json.get('type', modality_type)
        self.ref_type = _json.get('refType', ref_type)
        self.ref = _json.get('ref', ref)
        self.name = _json.get('name', name)

    def to_json(self):
        return {"type": self.type,
                "ref": self.ref,
                "refType": self.ref_type,
                "name": self.name}


class Modalities:
    def __init__(self, item):
        assert isinstance(item, Item)
        self.item = item

    @property
    def modalities(self):
        return self.item.metadata.get('modalities', None)

    def create(self, name, ref, ref_type='id', modality_type=ModalityTypeEnum.OVERLAY):
        if self.modalities is None:
            self.item.metadata['modalities'] = list()

        _json = {
            "type": modality_type,
            "refType": ref_type,
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
