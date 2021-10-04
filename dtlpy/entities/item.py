from collections import namedtuple
from enum import Enum
import traceback
import logging
import attr
import copy
import os

from .. import repositories, entities, services, exceptions
from .annotation import ViewAnnotationOptions

logger = logging.getLogger(name=__name__)


class ItemStatus(str, Enum):
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
    spec = attr.ib()

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
        :param _json: platform json
        :param client_api: ApiClient entity
        :param dataset: dataset entity
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
        :param project: project entity
        :param _json: _json response from host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Item object
        """
        dataset_id = None
        if dataset is not None:
            dataset_id = _json.get('datasetId', None)
            if dataset.id != dataset_id and dataset_id is not None:
                logger.warning('Item has been fetched from a dataset that is not belong to it')
                dataset = None
            else:
                dataset_id = dataset.id

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
            datasetId=_json.get('datasetId', dataset_id),
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
            id=_json.get('id', None),
            spec=_json.get('spec', None)
        )
        inst.is_fetched = is_fetched
        return inst

    ############
    # entities #
    ############

    @property
    def dataset(self):
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
                          field_names=['annotations', 'datasets', 'items', 'codebases', 'artifacts', 'modalities',
                                       'features'])
        reps.__new__.__defaults__ = (None, None, None, None, None, None, None)

        if self._dataset is None:
            items = repositories.Items(client_api=self._client_api,
                                       dataset=self._dataset,
                                       dataset_id=self.datasetId,
                                       datasets=repositories.Datasets(client_api=self._client_api, project=None))
            datasets = items.datasets
            features = repositories.Features(client_api=self._client_api,
                                             project=self._project)
        else:
            items = self.dataset.items
            datasets = self.dataset.datasets
            features = self.dataset.features

        r = reps(annotations=repositories.Annotations(client_api=self._client_api,
                                                      dataset_id=self.datasetId,
                                                      item=self,
                                                      dataset=self._dataset),
                 items=items,
                 datasets=datasets,
                 codebases=None,
                 artifacts=None,
                 modalities=Modalities(item=self),
                 features=features)
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

    @property
    def features(self):
        assert isinstance(self._repositories.features, repositories.Features)
        return self._repositories.features

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
    def description(self):
        description = None
        if 'description' in self.metadata:
            description = self.metadata['description'].get('text', None)
        return description

    @property
    def platform_url(self):
        return self._client_api._get_resource_url(
            "projects/{}/datasets/{}/items/{}".format(self.project.id, self._dataset.id, self.id))

    @property
    def snapshot_partition(self):
        return self.metadata['system'].get('snapshotPartition', None)

    @snapshot_partition.setter
    def snapshot_partition(self, partition):
        """
        Adds partition to the item. this is need when working with dl.Snapshot

        Note - correct usage is to use dl.Snapshot builtin methods
        :param partition: `entities.SnapshotPartitionType
        :return:  True if successful
        """
        if partition not in list(entities.SnapshotPartitionType):
            raise exceptions.SDKError(message="{!r} is not a supported partition: {{ {} }}".format(
                partition,
                list(entities.SnapshotPartitionType)))
        try:
            self.metadata['system']['snapshotPartition'] = partition
            self.update(system_metadata=True)
        except Exception:
            logger.error('Error updating snapshot partition. Please use platform')
            logger.debug(traceback.format_exc())

    @description.setter
    def description(self, text: str):
        """
        Update Item description

        :param text: if None or "" description will be deleted
        :return
        """
        raise NotImplementedError("Set description update the item in platform, use set_description(text: str) instead")

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
                                                        attr.fields(Item).annotations_link,
                                                        attr.fields(Item).spec))

        _json.update({'annotations': self.annotations_link,
                      'annotationsCount': self.annotations_count,
                      'dataset': self.dataset_url})
        if self.spec is not None:
            _json['spec'] = self.spec
        return _json

    def download(
            self,
            # download options
            local_path=None,
            file_types=None,
            save_locally=True,
            to_array=False,
            annotation_options: ViewAnnotationOptions = None,
            overwrite=False,
            to_items_folder=True,
            thickness=1,
            with_text=False,
            annotation_filters=None
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param local_path: local folder or filename to save to disk or returns BytelsIO
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param save_locally: bool. save to disk or return a buffer
        :param to_array: returns Ndarray when True and local_path = False
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param overwrite: optional - default = False
        :param to_items_folder: Create 'items' folder and download items to it
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param annotation_filters: Filters entity to filter annotations for download
        :return: Output (list)
        """
        # if dir - concatenate local path and item name
        if local_path is not None:
            if os.path.isdir(local_path):
                local_path = os.path.join(local_path, self.name)
            else:
                _, ext = os.path.splitext(local_path)
                if not ext:
                    os.makedirs(local_path, exist_ok=True)
                    local_path = os.path.join(local_path, self.name)

        # download
        return self.items.download(items=self,
                                   local_path=local_path,
                                   file_types=file_types,
                                   save_locally=save_locally,
                                   to_array=to_array,
                                   annotation_options=annotation_options,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   annotation_filters=annotation_filters,
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
        :param system_metadata: bool - True, if you want to change metadata system
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

    def clone(self, dst_dataset_id=None, remote_filepath=None, metadata=None, with_annotations=True,
              with_metadata=True, with_task_annotations_status=False, allow_many=False, wait=True):
        """
        Clone item
        :param dst_dataset_id: destination dataset id
        :param remote_filepath: complete filepath
        :param metadata: new metadata to add
        :param with_annotations: clone annotations
        :param with_metadata: clone metadata
        :param with_task_annotations_status: clone task annotations status
        :param allow_many: `bool` if True use multiple clones in single dataset is allowed, (default=False)
        :param wait: wait the command to finish

        :return: Item
        """
        if remote_filepath is None:
            remote_filepath = self.filename
        if dst_dataset_id is None:
            dst_dataset_id = self.datasetId
        return self.items.clone(item_id=self.id,
                                dst_dataset_id=dst_dataset_id,
                                remote_filepath=remote_filepath,
                                metadata=metadata,
                                with_annotations=with_annotations,
                                with_metadata=with_metadata,
                                with_task_annotations_status=with_task_annotations_status,
                                allow_many=allow_many,
                                wait=wait)

    def open_in_web(self):
        """
        Open the items in web platform

        :return:
        """
        self._client_api._open_in_web(url=self.platform_url)

    def update_status(self, status: ItemStatus, clear=False):
        """
        update item status

        :param status: "completed" ,"approved" ,"discarded"
        :param clear: bool -

        :return :True/False
        """
        if status not in list(ItemStatus):
            raise exceptions.PlatformException(
                error='400',
                message='Unknown status: {}. Please choose from: {}'.format(status, list(ItemStatus)))
        filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
        filters.add(field='label', values=status)
        filters.add(field='metadata.system.system', values=True)
        filters.add(field='type', values='class')
        annotations = self.annotations.list(filters)
        if len(annotations) > 0:
            if clear:
                # delete all annotation (AnnotationCollection)
                annotations.delete()
            return True
        try:
            if not clear:
                annotation_definition = entities.Classification(label=status)
                entities.Annotation.new(item=self,
                                        annotation_definition=annotation_definition,
                                        metadata={'system': {'system': True}}).upload()
            return True
        except Exception:
            logger.error('Error updating status. Please use platform')
            logger.debug(traceback.format_exc())
            return False

    def set_description(self, text: str):
        """
        Update Item description

        :param text: if None or "" description will be deleted

        :return
        """
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise ValueError("Description must get string")

        filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION,
                                   field='type',
                                   values="item_description")

        if text == "":
            if self.description is not None:
                self.metadata.pop('description', None)
                self._platform_dict = self.update()._platform_dict
                for annotation in self.annotations.list(filters=filters):
                    annotation.delete()
            return self

        for annotation in self.annotations.list(filters=filters):
            annotation.delete()
        try:
            annotation_definition = entities.Description(text=text)
            editor = self._client_api.info()['user_email']
            entities.Annotation.new(item=self,
                                    annotation_definition=annotation_definition).upload(),
            self.metadata['description'] = {'editor': editor, 'text': text}
            self._platform_dict = self.update()._platform_dict
            return self
        except Exception:
            logger.error('Error adding description. Please use platform')
            logger.debug(traceback.format_exc())


class ModalityTypeEnum(str, Enum):
    """
    State enum
    """
    OVERLAY = "overlay"
    REPLACE = "replace"


class ModalityRefTypeEnum(str, Enum):
    """
    State enum
    """
    ID = "id"
    URL = "url"


class Modality:
    def __init__(self, _json=None, modality_type=None, ref=None, ref_type=ModalityRefTypeEnum.ID,
                 name=None, timestamp=None):
        """
        :param _json: json represent of all modality params
        :param modality_type: ModalityTypeEnum.OVERLAY,ModalityTypeEnum.REPLACE
        :param ref: id or url of the item reference
        :param ref_type: ModalityRefTypeEnum.ID, ModalityRefTypeEnum.URL
        :param name:
        :param timestamp: ISOString, epoch of UTC
        """
        if _json is None:
            _json = dict()
        self.type = _json.get('type', modality_type)
        self.ref_type = _json.get('refType', ref_type)
        self.ref = _json.get('ref', ref)
        self.name = _json.get('name', name)
        self.timestamp = _json.get('timestamp', timestamp)

    def to_json(self):
        _json = {"type": self.type,
                 "ref": self.ref,
                 "refType": self.ref_type}
        if self.name is not None:
            _json['name'] = self.name
        if self.timestamp is not None:
            _json['timestamp'] = self.timestamp
        return _json


class Modalities:
    def __init__(self, item):
        assert isinstance(item, Item)
        self.item = item
        if 'system' not in self.item.metadata:
            self.item.metadata['system'] = dict()

    @property
    def modalities(self):
        mod = None
        if 'system' in self.item.metadata:
            mod = self.item.metadata['system'].get('modalities', None)
        return mod

    def create(self, name, ref,
               ref_type: ModalityRefTypeEnum = ModalityRefTypeEnum.ID,
               modality_type: ModalityTypeEnum = ModalityTypeEnum.OVERLAY,
               timestamp=None):
        """
        create Modalities entity
        :param name:
        :param ref: id or url of the item reference
        :param ref_type: ModalityRefTypeEnum.ID, ModalityRefTypeEnum.URL
        :param modality_type: ModalityTypeEnum.OVERLAY,ModalityTypeEnum.REPLACE
        :param timestamp: ISOString, epoch of UTC
        """
        if self.modalities is None:
            self.item.metadata['system']['modalities'] = list()

        _json = {"type": modality_type,
                 "ref": ref,
                 "refType": ref_type}
        if name is not None:
            _json['name'] = name
        if timestamp is not None:
            _json['timestamp'] = timestamp

        self.item.metadata['system']['modalities'].append(_json)

        return Modality(_json=_json)

    def delete(self, name):
        """
        :param name:
        """
        if self.modalities is not None:
            for modality in self.item.metadata['system']['modalities']:
                if name == modality['name']:
                    self.item.metadata['system']['modalities'].remove(modality)
                    return Modality(_json=modality)
        return None

    def list(self):
        modalities = list()
        if self.modalities is not None:
            modalities = list()
            for modality in self.item.metadata['system']['modalities']:
                modalities.append(Modality(_json=modality))
        return modalities
