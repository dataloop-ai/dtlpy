import warnings
from collections import namedtuple
from enum import Enum
import traceback
import logging
import attr
import copy
import os

from .. import repositories, entities, exceptions
from .annotation import ViewAnnotationOptions, ExportVersion
from ..services.api_client import ApiClient
from ..services.api_client import client as client_api

logger = logging.getLogger(name='dtlpy')


class ExportMetadata(Enum):
    FROM_JSON = 'from_json'


class ItemStatus(str, Enum):
    COMPLETED = "completed"
    APPROVED = "approved"
    DISCARDED = "discard"


@attr.s
class Item(entities.BaseEntity):
    """
    Item object
    """
    # item information
    annotations_link = attr.ib(repr=False)
    dataset_url = attr.ib()
    thumbnail = attr.ib(repr=False)
    created_at = attr.ib()
    dataset_id = attr.ib()
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
    creator = attr.ib()
    _description = attr.ib()
    _src_item = attr.ib(repr=False)

    # name change
    annotations_count = attr.ib()

    # api
    _client_api = attr.ib(type=ApiClient, repr=False)
    _platform_dict = attr.ib(repr=False)

    # entities
    _dataset = attr.ib(repr=False)
    _model = attr.ib(repr=False)
    _project = attr.ib(repr=False)
    _project_id = attr.ib(repr=False)

    # repositories
    _repositories = attr.ib(repr=False)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def datasetId(self):
        return self.dataset_id

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
    def from_json(cls, _json, client_api, dataset=None, project=None, model=None, is_fetched=True):
        """
        Build an item entity object from a json

        :param dtlpy.entities.project.Project project: project entity
        :param dict _json: _json response from host
        :param dtlpy.entities.dataset.Dataset dataset: dataset in which the annotation's item is located
        :param dtlpy.entities.dataset.Model model: the model entity if item is an artifact of a model
        :param dlApiClient client_api: ApiClient entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: Item object
        :rtype: dtlpy.entities.item.Item
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
        project_id = _json.get('projectId', None)
        if project_id is None:
            project_id = project.id if project else None
        inst = cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            project=project,
            model=model,
            # params
            annotations_link=_json.get('annotations', None),
            thumbnail=_json.get('thumbnail', None),
            dataset_id=_json.get('datasetId', dataset_id),
            annotated=_json.get('annotated', None),
            dataset_url=_json.get('dataset', None),
            created_at=_json.get('createdAt', None),
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
            spec=_json.get('spec', None),
            creator=_json.get('creator', None),
            project_id=project_id,
            description=_json.get('description', None),
            src_item=_json.get('srcItem', None),
        )
        inst.is_fetched = is_fetched
        return inst

    def __getstate__(self):
        # dump state to json
        return self.to_json()

    def __setstate__(self, state):
        # create a new item, and update the current one with the same state
        # this way we can have _client_api, and all the repositories and entities which are not picklable
        self.__dict__.update(entities.Item.from_json(_json=state,
                                                     client_api=client_api).__dict__)

    ############
    # entities #
    ############
    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def model(self):
        return self._model

    @property
    def project(self):
        if self._project is None:
            if self._dataset is None:
                self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
            self._project = self._dataset.project
            if self._project is None:
                raise exceptions.PlatformException(error='2001',
                                                   message='Missing entity "project".')
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def project_id(self):
        if self._project_id is None:
            if self._dataset is None:
                self._dataset = self.datasets.get(dataset_id=self.dataset_id, fetch=None)
            self._project_id = self._dataset.project.id
        return self._project_id

    ################
    # repositories #
    ################

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['annotations', 'datasets', 'items', 'codebases', 'artifacts', 'modalities',
                                       'features', 'assignments', 'tasks', 'resource_executions'])
        reps.__new__.__defaults__ = (None, None, None, None, None, None, None, None, None)

        if self._dataset is None:
            items = repositories.Items(
                client_api=self._client_api,
                dataset=self._dataset,
                dataset_id=self.dataset_id,
                datasets=repositories.Datasets(client_api=self._client_api, project=None)
            )
            datasets = items.datasets

        else:
            items = self.dataset.items
            datasets = self.dataset.datasets

        r = reps(
            annotations=repositories.Annotations(
                client_api=self._client_api,
                dataset_id=self.dataset_id,
                item=self,
                dataset=self._dataset
            ),
            items=items,
            datasets=datasets,
            codebases=None,
            artifacts=None,
            modalities=Modalities(item=self),
            features=repositories.Features(
                client_api=self._client_api,
                project=self._project,
                item=self
            ),
            tasks=repositories.Tasks(
                client_api=self._client_api,
                project=self._project,
                dataset=self._dataset
            ),
            assignments=repositories.Assignments(
                client_api=self._client_api,
                project=self._project,
                dataset=self._dataset
            ),
            resource_executions=repositories.ResourceExecutions(
                client_api=self._client_api,
                project=self._project,
                resource=self
            )
        )
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
    def assignments(self):
        assert isinstance(self._repositories.assignments, repositories.Assignments)
        return self._repositories.assignments

    @property
    def tasks(self):
        assert isinstance(self._repositories.tasks, repositories.Tasks)
        return self._repositories.tasks

    @property
    def resource_executions(self):
        assert isinstance(self._repositories.resource_executions, repositories.ResourceExecutions)
        return self._repositories.resource_executions

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
        if self._description is not None:
            description = self._description
        elif 'description' in self.metadata:
            description = self.metadata['description'].get('text', None)
        return description

    @property
    def platform_url(self):
        return self._client_api._get_resource_url(
            "projects/{}/datasets/{}/items/{}".format(self.dataset.projects[-1], self.dataset.id, self.id))

    @description.setter
    def description(self, text: str):
        """
        Update Item description

        :param text: if None or "" description will be deleted
        :return
        """
        self.set_description(text=text)

    ###########
    # Functions #
    ###########
    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(Item)._repositories,
                                                        attr.fields(Item)._dataset,
                                                        attr.fields(Item)._model,
                                                        attr.fields(Item)._project,
                                                        attr.fields(Item)._client_api,
                                                        attr.fields(Item)._platform_dict,
                                                        attr.fields(Item).annotations_count,
                                                        attr.fields(Item).dataset_url,
                                                        attr.fields(Item).annotations_link,
                                                        attr.fields(Item).spec,
                                                        attr.fields(Item).creator,
                                                        attr.fields(Item).created_at,
                                                        attr.fields(Item).dataset_id,
                                                        attr.fields(Item)._project_id,
                                                        attr.fields(Item)._description,
                                                        attr.fields(Item)._src_item,
                                                        ))

        _json.update({'annotations': self.annotations_link,
                      'annotationsCount': self.annotations_count,
                      'dataset': self.dataset_url,
                      'createdAt': self.created_at,
                      'datasetId': self.dataset_id,
                      })
        if self.spec is not None:
            _json['spec'] = self.spec
        if self.creator is not None:
            _json['creator'] = self.creator
        if self._description is not None:
            _json['description'] = self.description
        if self._src_item is not None:
            _json['srcItem'] = self._src_item
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
            annotation_filters=None,
            alpha=1,
            export_version=ExportVersion.V1
    ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param str local_path: local folder or filename to save to.
        :param list file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param bool save_locally: bool. save to disk or return a buffer
        :param bool to_array: returns Ndarray when True and local_path = False
        :param list annotation_options: download annotations options:  list(dl.ViewAnnotationOptions)
        :param dtlpy.entities.filters.Filters annotation_filters: Filters entity to filter annotations for download
        :param bool overwrite: optional - default = False
        :param bool to_items_folder: Create 'items' folder and download items to it
        :param int thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param bool with_text: optional - add text to annotations, default = False
        :param float alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return: generator of local_path per each downloaded item
        :rtype: generator or single item

        **Example**:

        .. code-block:: python

            item.download(local_path='local_path',
                         annotation_options=dl.ViewAnnotationOptions.MASK,
                         overwrite=False,
                         thickness=1,
                         with_text=False,
                         alpha=1,
                         save_locally=True
                         )
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
        filters = None
        items = self
        if self.type == 'dir':
            filters = self.datasets._bulid_folder_filter(folder_path=self.filename)
            items = None

        return self.items.download(items=items,
                                   local_path=local_path,
                                   file_types=file_types,
                                   save_locally=save_locally,
                                   to_array=to_array,
                                   annotation_options=annotation_options,
                                   overwrite=overwrite,
                                   to_items_folder=to_items_folder,
                                   annotation_filters=annotation_filters,
                                   thickness=thickness,
                                   alpha=alpha,
                                   with_text=with_text,
                                   export_version=export_version,
                                   filters=filters)

    def delete(self):
        """
        Delete item from platform

        :return: True
        :rtype: bool
        """
        return self.items.delete(item_id=self.id)

    def update(self, system_metadata=False):
        """
        Update items metadata

        :param bool system_metadata: bool - True, if you want to change metadata system
        :return: Item object
        :rtype: dtlpy.entities.item.Item
        """
        return self.items.update(item=self, system_metadata=system_metadata)

    def move(self, new_path):
        """
        Move item from one folder to another in Platform
        If the directory doesn't exist it will be created

        :param str new_path: new full path to move item to.
        :return: True if update successfully
        :rtype: bool
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

        :param str dst_dataset_id: destination dataset id
        :param str remote_filepath: complete filepath
        :param dict metadata: new metadata to add
        :param bool with_annotations: clone annotations
        :param bool with_metadata: clone metadata
        :param bool with_task_annotations_status: clone task annotations status
        :param bool allow_many: `bool` if True, using multiple clones in single dataset is allowed, (default=False)
        :param bool wait: wait for the command to finish
        :return: Item object
        :rtype: dtlpy.entities.item.Item

        **Example**:

        .. code-block:: python

            item.clone(item_id='item_id',
                    dst_dataset_id='dist_dataset_id',
                    with_metadata=True,
                    with_task_annotations_status=False,
                    with_annotations=False)
        """
        if remote_filepath is None:
            remote_filepath = self.filename
        if dst_dataset_id is None:
            dst_dataset_id = self.dataset_id
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

    def _set_action(self, status: str, operation: str, assignment_id: str = None, task_id: str = None):
        """
        update item status

        :param status: str - string the describes the status
        :param operation: str -  'create' or 'delete'
        :param assignment_id: str - assignment id
        :param task_id: str - task id

        :return :True/False
        """
        if assignment_id:
            success = self.assignments.set_status(
                status=status,
                operation=operation,
                item_id=self.id,
                assignment_id=assignment_id
            )
        elif task_id:
            success = self.tasks.set_status(
                status=status,
                operation=operation,
                item_ids=[self.id],
                task_id=task_id
            )

        else:
            raise exceptions.PlatformException('400', 'Must provide task_id or assignment_id')

        return success

    def update_status(self, status: str, clear: bool = False, assignment_id: str = None, task_id: str = None):
        """
        update item status

        :param str status: "completed" ,"approved" ,"discard"
        :param bool clear: if true delete status
        :param str assignment_id: assignment id
        :param str task_id: task id

        :return :True/False
        :rtype: bool

        **Example**:

        .. code-block:: python

            item.update_status(status='complete',
                               operation='created',
                               task_id='task_id')

        """
        if not assignment_id and not task_id:
            system_metadata = self.metadata.get('system', dict())
            if 'refs' in system_metadata:
                refs = system_metadata['refs']
                if len(refs) <= 2:
                    for ref in refs:
                        if ref.get('type', '') == 'assignment':
                            assignment_id = ref['id']
                        if ref.get('type', '') == 'task':
                            task_id = ref['id']

        if assignment_id or task_id:
            if clear:
                self._set_action(status=status, operation='delete', assignment_id=assignment_id, task_id=task_id)
            else:
                self._set_action(status=status, operation='create', assignment_id=assignment_id, task_id=task_id)
        else:
            raise exceptions.PlatformException('400', 'must provide assignment_id or task_id')

    def set_description(self, text: str):
        """
        Update Item description

        :param str text: if None or "" description will be deleted

        :return
        """
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise ValueError("Description must get string")
        self._description = text
        self._platform_dict = self.update()._platform_dict
        return self


class ModalityTypeEnum(str, Enum):
    """
    State enum
    """
    OVERLAY = "overlay"
    REPLACE = "replace"
    PREVIEW = "preview"


class ModalityRefTypeEnum(str, Enum):
    """
    State enum
    """
    ID = "id"
    URL = "url"


class Modality:
    def __init__(self, _json=None, modality_type=None, ref=None, ref_type=ModalityRefTypeEnum.ID,
                 name=None, timestamp=None, mimetype=None):
        """
        :param _json: json represent of all modality params
        :param modality_type: ModalityTypeEnum.OVERLAY,ModalityTypeEnum.REPLACE
        :param ref: id or url of the item reference
        :param ref_type: ModalityRefTypeEnum.ID, ModalityRefTypeEnum.URL
        :param name:
        :param timestamp: ISOString, epoch of UTC
        :param mimetype: str - type of the file
        """
        if _json is None:
            _json = dict()
        self.type = _json.get('type', modality_type)
        self.ref_type = _json.get('refType', ref_type)
        self.ref = _json.get('ref', ref)
        self.name = _json.get('name', name)
        self.timestamp = _json.get('timestamp', timestamp)
        self.mimetype = _json.get('mimetype', mimetype)

    def to_json(self):
        _json = {"type": self.type,
                 "ref": self.ref,
                 "refType": self.ref_type}
        if self.name is not None:
            _json['name'] = self.name
        if self.timestamp is not None:
            _json['timestamp'] = self.timestamp
        if self.mimetype is not None:
            _json['mimetype'] = self.mimetype
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
               timestamp=None,
               mimetype=None,
               ):
        """
        create Modalities entity

        :param name: name
        :param ref: id or url of the item reference
        :param ref_type: ModalityRefTypeEnum.ID, ModalityRefTypeEnum.URL
        :param modality_type: ModalityTypeEnum.OVERLAY,ModalityTypeEnum.REPLACE
        :param timestamp: ISOString, epoch of UTC
        :param mimetype: str - type of the file
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
        if mimetype is not None:
            _json['mimetype'] = mimetype

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
