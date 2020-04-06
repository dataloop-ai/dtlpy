import numpy as np
import logging
import attr
import json
from PIL import Image

from .. import entities, PlatformException, repositories
from ..services import ApiClient

logger = logging.getLogger(name=__name__)


@attr.s
class Annotation(entities.BaseEntity):
    """
    Annotations object
    """
    # annotation definition
    annotation_definition = attr.ib(repr=False)

    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    item_url = attr.ib(repr=False)
    item = attr.ib(repr=False)
    item_id = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedBy = attr.ib(repr=False)
    updatedAt = attr.ib(repr=False)
    type = attr.ib()
    dataset_url = attr.ib(repr=False)

    # meta
    metadata = attr.ib(repr=False)
    fps = attr.ib(repr=False)
    hash = attr.ib(default=None, repr=False)
    dataset_id = attr.ib(default=None, repr=False)
    status = attr.ib(default=None, repr=False)
    object_id = attr.ib(default=None, repr=False)
    automated = attr.ib(default=None, repr=False)
    hash = attr.ib(default=None, repr=False)

    # snapshots
    frames = attr.ib(default=None, repr=False)
    current_frame = attr.ib(default=0, repr=False)

    # video attributes
    end_frame = attr.ib(default=0, repr=False)
    end_time = attr.ib(default=0, repr=False)
    start_frame = attr.ib(default=0)
    start_time = attr.ib(default=0)

    # temp
    platform_dict = attr.ib(default=None, repr=False)
    _dataset = attr.ib(repr=False, default=None)
    _datasets = attr.ib(repr=False, default=None)
    _annotations = attr.ib(repr=False, default=None)
    __client_api = attr.ib(default=None, repr=False)
    _items = attr.ib(repr=False, default=None)

    ####################################
    # annotation definition attributes #
    ####################################
    @property
    def parent_id(self):
        try:
            parent_id = self.metadata['system']['parentId']
        except KeyError:
            parent_id = None
        return parent_id

    @parent_id.setter
    def parent_id(self, parent_id):
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system']['parentId'] = parent_id

    @property
    def coordinates(self):
        color = None
        if self.type in ['binary']:
            color = self.color
        coordinates = self.annotation_definition.to_coordinates(color=color)
        return coordinates

    @property
    def _client_api(self):
        if self.__client_api is None:
            if self.item is None:
                raise PlatformException('400',
                                        'This action cannot be performed without an item entity. Please set item')
            else:
                self.__client_api = self.item._client_api
        assert isinstance(self.__client_api, ApiClient)
        return self.__client_api

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.datasets.get(dataset_id=self.dataset_id)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def annotations(self):
        if self._annotations is None:
            self._annotations = repositories.Annotations(client_api=self._client_api, item=self.item)
        assert isinstance(self._annotations, repositories.Annotations)
        return self._annotations

    @property
    def datasets(self):
        if self._datasets is None:
            self._datasets = repositories.Datasets(client_api=self._client_api)
        assert isinstance(self._datasets, repositories.Datasets)
        return self._datasets

    @property
    def items(self):
        if self._items is None:
            if self._datasets is not None:
                self._items = self._dataset.items
            elif self.item is not None:
                self._items = self.item.items
            else:
                self._items = repositories.Items(client_api=self._client_api, dataset=self._dataset)
        assert isinstance(self._items, repositories.Items)
        return self._items

    @property
    def x(self):
        return self.annotation_definition.x

    @property
    def y(self):
        return self.annotation_definition.y

    @property
    def rx(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.rx
        else:
            return None

    @property
    def ry(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.ry
        else:
            return None

    @property
    def angle(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.angle
        else:
            return None

    @property
    def geo(self):
        return self.annotation_definition.geo

    @geo.setter
    def geo(self, geo):
        self.annotation_definition.geo = geo

    @property
    def top(self):
        return self.annotation_definition.top

    @top.setter
    def top(self, top):
        self.annotation_definition.top = top

    @property
    def bottom(self):
        return self.annotation_definition.bottom

    @bottom.setter
    def bottom(self, bottom):
        self.annotation_definition.bottom = bottom

    @property
    def left(self):
        return self.annotation_definition.left

    @left.setter
    def left(self, left):
        self.annotation_definition.left = left

    @property
    def right(self):
        return self.annotation_definition.right

    @right.setter
    def right(self, right):
        self.annotation_definition.right = right

    @property
    def last_frame(self):
        if len(self.frames) == 0:
            return 0
        return max(self.frames)

    @property
    def label(self):
        return self.annotation_definition.label

    @label.setter
    def label(self, label):
        self.annotation_definition.label = label

    @property
    def attributes(self):
        return self.annotation_definition.attributes

    @attributes.setter
    def attributes(self, attributes):
        if not isinstance(attributes, list):
            attributes = [attributes]
        self.annotation_definition.attributes = attributes

    @property
    def color(self):
        try:
            lower_keys = {key.lower(): label for key, label in self.dataset.labels_flat_dict.items()}
            if self.label.lower() in lower_keys:
                color = lower_keys[self.label.lower()].rgb
            else:
                color = None
            return color
        except Exception:
            return None

    ####################
    # frame attributes #
    ####################
    @property
    def frame_num(self):
        if len(self.frames) > 0:
            return self.current_frame
        else:
            return self.start_frame

    @frame_num.setter
    def frame_num(self, frame_num):
        if frame_num != self.current_frame:
            self.frames[self.current_frame].frame_num = frame_num
            self.frames[frame_num] = self.frames[self.current_frame]
            self.frames.pop(self.current_frame)

    @property
    def fixed(self):
        if len(self.frames) > 0:
            return self.frames[self.current_frame].fixed
        else:
            return False

    @fixed.setter
    def fixed(self, fixed):
        if len(self.frames) > 0:
            self.frames[self.current_frame].fixed = fixed

    @property
    def is_video(self):
        if len(self.frames) == 0:
            return False
        else:
            return True

    ################
    # polygon only #
    ################
    @property
    def is_open(self):
        is_open = None
        if self.type in ['segment', 'polyline']:
            is_open = self.annotation_definition.is_open
        return is_open

    @is_open.setter
    def is_open(self, is_open):
        if self.type in ['segment']:
            self.annotation_definition.is_open = is_open
        else:
            logger.warning('type {} annotation does not have attribute is_open'.format(self.type))

    ##################
    # entity methods #
    ##################

    def get_item(self):
        if self.item is None:
            self.item = self.items.get(item_id=self.item_id)

    def delete(self):
        """
        Remove an annotation from item
        :return: True
        """
        return self.annotations.delete(annotation_id=self.id)

    def update(self, system_metadata=False):
        """
        Update an existing annotation in host.
        :param system_metadata:
        :return: Annotation object
        """
        return self.annotations.update(annotations=self,
                                       system_metadata=system_metadata)[0]

    def upload(self):
        """
        Create a new annotation in host
        :return:
        """
        return self.annotations.upload(annotations=self)[0]

    def download(self, filepath, annotation_format='mask', height=None, width=None, thickness=1, with_text=False):
        """
        Save annotation to file
        :param filepath: local path to where annotation will be downloaded to
        :param annotation_format: ['mask'/'instance']
        :param height: image height
        :param width: image width
        :param thickness: thickness
        :param with_text: get mask with text
        :return: filepath
        """
        if annotation_format == 'json':
            with open(filepath, 'w') as f:
                json.dump(self.to_json(), f, indent=2)
        else:
            mask = self.show(thickness=thickness,
                             with_text=with_text,
                             height=height,
                             width=width,
                             annotation_format=annotation_format)
            img = Image.fromarray(mask.astype(np.uint8))
            img.save(filepath)
        return filepath

    def set_frame(self, frame):
        """
        Set annotation to frame state
        :param frame: frame number
        :return: True
        """
        if frame in self.frames:
            self.current_frame = frame
            self.annotation_definition = self.frames[frame].annotation_definition
            return True
        else:
            return False

    ############
    # Plotting #
    ############
    def show(self, image=None, thickness=None, with_text=False, height=None, width=None,
             annotation_format='mask', color=None):
        """
        Show annotations

        :param image: empty or image to draw on
        :param height: height
        :param width: width
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param annotation_format: 'mask'/'instance'
        :param color: optional
        :return: ndarray of the annotations
        """
        try:
            import cv2
        except ImportError:
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        # height/width
        if height is None:
            if self.item is None or self.item.height is None:
                raise PlatformException('400', 'must provide item width and height')
            height = self.item.height
        if width is None:
            if self.item is None or self.item.width is None:
                raise PlatformException('400', 'must provide item width and height')
            width = self.item.width

        # color
        if color is None:
            if self.color is not None:
                color = self.color
            else:
                if self.label.lower() not in ['approved', 'completed']:
                    logger.warning('No color given for label: {}, random color will be selected'.format(self.label))
                color = (127, 127, 127)
        if (isinstance(color, list) or isinstance(color, tuple)) and len(color) == 3:
            # if color is a list or tuple and size of 3 - add alpha
            color = (color[0], color[1], color[2], 255)
            if image is not None:
                # check matching dimensions
                if len(image.shape) == 2:
                    # image is gray
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
                elif image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
                elif image.shape[2] == 4:
                    pass
                else:
                    raise PlatformException(error='400',
                                            message='Image size doesnt match colors. img shape: {}, color: {}'.format(
                                                image.shape,
                                                color))
        # show annotation
        if image is None:
            image = np.zeros((height, width, len(color)), dtype=np.uint8)
            if image.shape[2] == 1:
                image = np.squeeze(image)
        return self.annotation_definition.show(image=image,
                                               thickness=thickness,
                                               with_text=with_text,
                                               height=height,
                                               width=width,
                                               annotation_format=annotation_format,
                                               color=color)

    #######
    # I/O #
    #######
    @classmethod
    def new(cls,
            item=None,
            annotation_definition=None,
            object_id=None,
            automated=None,
            metadata=None,
            frame_num=None,
            parent_id=None,
            start_time=None,
            height=None,
            width=None):
        """
        Create a new annotation object annotations

        :param start_time:
        :param width: annotation item's width
        :param height: annotation item's height
        :param item: item to annotate
        :param annotation_definition: annotation type object
        :param object_id: object_id
        :param automated: is automated
        :param metadata: metadata
        :param frame_num: optional - first frame number if video annotation
        :param parent_id: add parent annotation ID
        :return: annotation object
        """
        if frame_num is None:
            frame_num = 0

        # init annotations
        if metadata is None:
            metadata = dict()

        # add parent
        if parent_id is not None:
            if 'system' not in metadata:
                metadata['system'] = dict()
            metadata['system']['parentId'] = parent_id

        # frames
        frames = dict()

        # handle fps
        if item is not None and item.fps is not None:
            fps = item.fps
        else:
            fps = None

        # get type
        ann_type = None
        if annotation_definition is not None:
            ann_type = annotation_definition.type

        # dataset
        dataset_url = None
        dataset_id = None
        if item is not None:
            dataset_url = item.dataset_url
            dataset_id = item.datasetId

        if start_time is None:
            if fps is not None and frame_num is not None:
                start_time = frame_num / fps if fps != 0 else 0
            else:
                start_time = 0

        if frame_num is None:
            frame_num = 0

        return cls(
            # annotation_definition
            annotation_definition=annotation_definition,

            # platform
            id=None,
            url=None,
            item_url=None,
            item=item,
            item_id=None,
            creator=None,
            createdAt=None,
            updatedBy=None,
            updatedAt=None,
            object_id=object_id,
            type=ann_type,
            dataset_url=dataset_url,
            dataset_id=dataset_id,

            # meta
            metadata=metadata,
            fps=fps,
            status=None,
            automated=automated,

            # snapshots
            frames=frames,

            # video only attributes
            end_frame=frame_num,
            end_time=0,
            start_frame=frame_num,
            start_time=start_time,

            # temp
            platform_dict=dict(),
        )

    def add_frames(self, annotation_definition, frame_num=None, end_frame_num=None, start_time=None, end_time=None,
                   fixed=True):
        # handle fps
        if self.fps is None:
            if self.item is not None:
                if self.item.fps is not None:
                    self.fps = self.item.fps
        if self.fps is None:
            raise PlatformException('400', 'Annotation must have fps in order to perform this action')

        if frame_num is None:
            frame_num = int(np.round(start_time * self.fps))
        if end_frame_num is None:
            end_frame_num = int(np.round(end_time * self.fps))

        for frame in range(frame_num, end_frame_num):
            self.add_frame(annotation_definition=annotation_definition,
                           frame_num=frame,
                           fixed=fixed)

    def add_frame(self, annotation_definition, frame_num=None, fixed=True):
        """
        Add a frame state to annotation

        :param annotation_definition: annotation type object - must be same type as annotation
        :param fixed: is fixed
        :param frame_num: frame number
        :return: annotation object
        """
        # handle fps
        if self.fps is None:
            if self.item is not None:
                if self.item.fps is not None:
                    self.fps = self.item.fps
        if self.fps is None:
            raise PlatformException('400', 'Annotation must have fps in order to perform this action')

        # if this is first frame
        if self.annotation_definition is None:

            if frame_num is None:
                frame_num = 0
            self.start_frame = frame_num
            self.current_frame = frame_num
            self.end_frame = frame_num
            self.start_time = frame_num / self.fps if self.fps != 0 else 0

            frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                        frame_num=frame_num,
                                        fixed=fixed,
                                        annotation=self)

            self.frames[frame_num] = frame
            self.set_frame(frame_num)
            self.end_time = self.end_frame / self.fps if self.fps != 0 else 0
            self.type = annotation_definition.type

            return True

        # check if type matches annotation
        if not isinstance(annotation_definition, type(self.annotation_definition)):
            raise PlatformException('400', 'All frames in annotation must have same type')

        # find frame number
        if frame_num is None:
            frame_num = self.last_frame + 1
        elif frame_num < self.start_frame:
            self.start_frame = frame_num

        # add frame to annotation
        if not self.is_video:
            # create first frame from annotation definition
            frame = FrameAnnotation.new(annotation_definition=self.annotation_definition,
                                        frame_num=self.last_frame,
                                        fixed=fixed,
                                        annotation=self)

            self.frames[self.start_frame] = frame

        # create new time annotations
        frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                    frame_num=frame_num,
                                    fixed=fixed,
                                    annotation=self)

        self.frames[frame_num] = frame
        self.end_frame = max(self.frames)
        self.end_time = self.end_frame / self.fps

        return True

    @classmethod
    def from_json(cls, _json, item=None, client_api=None, annotations=None, is_video=None, fps=25):
        """
        Create an annotation object from platform json
        :param client_api:
        :param annotations:
        :param _json: platform json
        :param item: item
        :return: annotation object
        """
        # handle 'note'
        if _json['type'] == 'note':
            return None

        if is_video is None:
            if item is None:
                is_video = False
            else:
                # get item type
                if 'video' in item.mimetype:
                    is_video = True

        item_url = _json.get('item', item.url if item is not None else None)
        item_id = _json.get('itemId', item.id if item is not None else None)
        dataset_url = _json.get('dataset', item.dataset_url if item is not None else None)
        dataset_id = _json.get('datasetId', item.datasetId if item is not None else None)

        # get id
        if 'id' in _json:
            annotation_id = _json['id']
        elif '_id' in _json:
            annotation_id = _json['_id']
        else:
            raise PlatformException('400', 'missing id in annotation json')

        # get metadata, status, attributes and object id
        object_id = None
        status = None
        attributes = _json.get('attributes', list())
        metadata = _json.get('metadata', dict())
        if 'system' in metadata:
            object_id = _json['metadata']['system'].get('objectId', object_id)
            status = _json['metadata']['system'].get('status', status)

        first_frame_attributes = list()
        first_frame_coordinates = list()
        first_frame_number = 0
        first_frame_start_time = 0
        automated = None
        end_frame = None
        start_time = 0
        start_frame = 0

        ############
        # if video #
        ############
        if is_video:
            # get fps
            if item is not None and item.fps is not None:
                fps = item.fps

            # get video-only attributes
            end_time = 1.5
            # get first frame attribute
            first_frame_attributes = _json.get('attributes', first_frame_attributes)
            # get first frame coordinates
            first_frame_coordinates = _json.get('coordinates', first_frame_coordinates)
            if 'system' in metadata:
                # get first frame number
                first_frame_number = _json['metadata']['system'].get('frame', first_frame_number)
                # get first frame start time
                start_time = _json['metadata']['system'].get('startTime', first_frame_start_time)
                # get first frame number
                start_frame = _json['metadata']['system'].get('frame', start_frame)
                automated = _json['metadata']['system'].get('automated', automated)
                end_frame = _json['metadata']['system'].get('endFrame', end_frame)
                end_time = _json['metadata']['system'].get('endTime', end_time)

            annotation_definition = None
        ################
        # if not video #
        ################
        else:
            # get coordinates
            coordinates = _json.get('coordinates', list())
            # set video only attributes
            end_time = 0
            # get automated
            if 'system' in metadata:
                automated = metadata['system'].get('automated', automated)
            # set annotation definition
            def_dict = {'type': _json['type'],
                        'coordinates': coordinates,
                        'label': _json['label'],
                        'attributes': attributes}
            if _json['type'] == 'segment':
                is_open = False
                if 'system' in metadata:
                    is_open = metadata['system'].get('isOpen', is_open)
                def_dict['is_open'] = is_open
            annotation_definition = FrameAnnotation.json_to_annotation_definition(def_dict)

        frames = dict()

        # init annotation
        annotation = cls(
            # temp
            platform_dict=_json,
            # annotation definition
            annotation_definition=annotation_definition,
            # platform
            id=annotation_id,
            url=_json.get('url', None),
            item_url=item_url,
            item=item,
            item_id=item_id,
            dataset_url=dataset_url,
            dataset_id=dataset_id,
            creator=_json['creator'],
            createdAt=_json['createdAt'],
            updatedBy=_json['updatedBy'],
            updatedAt=_json['updatedAt'],
            hash=_json.get('hash', None),
            object_id=object_id,
            type=_json['type'],
            # meta
            metadata=metadata,
            fps=fps,
            status=status,
            # snapshots
            frames=frames,
            # video attributes
            automated=automated,
            end_frame=end_frame,
            end_time=end_time,
            start_frame=start_frame,
            annotations=annotations,
            start_time=start_time
        )
        annotation.__client_api = client_api

        #################
        # if has frames #
        #################
        if is_video:
            if annotation.type == 'class' or annotation.type == 'subtitle':
                if end_frame is None:
                    end_frame = start_frame
                # for class type annotation create frames
                # make copies of the head annotations for all frames in it
                for frame_num in range(start_frame, end_frame + 1):
                    snapshot = {
                        'frame': frame_num,
                        'attributes': first_frame_attributes,
                        'coordinates': first_frame_coordinates,
                        'fixed': True,
                        'label': _json['label'],
                        'type': annotation.type,
                    }
                    frame = FrameAnnotation.from_snapshot(_json=snapshot,
                                                          annotation=annotation,
                                                          fps=fps)
                    annotation.frames[frame.frame_num] = frame
            else:
                # set first frame
                snapshot = {
                    'attributes': first_frame_attributes,
                    'coordinates': first_frame_coordinates,
                    'fixed': True,
                    'frame': first_frame_number,
                    'label': _json['label'],
                    'type': annotation.type,
                }

                # add first frame
                frame = FrameAnnotation.from_snapshot(_json=snapshot,
                                                      annotation=annotation,
                                                      fps=fps)
                annotation.frames[frame.frame_num] = frame
                annotation.annotation_definition = frame.annotation_definition
                # put snapshots if there are any
                for snapshot in _json['metadata']['system']['snapshots_']:
                    frame = FrameAnnotation.from_snapshot(_json=snapshot,
                                                          annotation=annotation,
                                                          fps=fps)
                    annotation.frames[frame.frame_num] = frame

            annotation.annotation_definition = annotation.frames[min(frames)].annotation_definition

        return annotation

    def to_json(self):
        """
        Convert annotation object to a platform json representation
        :return: platform json
        """
        if len(self.frames) > 0:
            self.set_frame(min(self.frames))
        _json = attr.asdict(self,
                            filter=attr.filters.include(attr.fields(Annotation).id,
                                                        attr.fields(Annotation).url,
                                                        attr.fields(Annotation).hash,
                                                        attr.fields(Annotation).metadata,
                                                        attr.fields(Annotation).creator,
                                                        attr.fields(Annotation).hash,
                                                        attr.fields(Annotation).createdAt,
                                                        attr.fields(Annotation).updatedBy,
                                                        attr.fields(Annotation).updatedAt,
                                                        attr.fields(Annotation).metadata,
                                                        attr.fields(Annotation).createdAt,
                                                        attr.fields(Annotation).updatedBy))

        # property attributes                                                
        _json['itemId'] = self.item_id
        _json['item'] = self.item_url
        _json['label'] = self.label
        _json['attributes'] = self.attributes
        _json['dataset'] = self.dataset_url

        if self.item is not None and self.dataset_id is None:
            _json['datasetId'] = self.item.datasetId
        else:
            _json['datasetId'] = self.dataset_id

        # polyline to segment
        if self.type == 'polyline':
            _json['type'] = 'segment'
        else:
            _json['type'] = self.type
        if self.type == 'polyline':
            _json['coordinates'] = [self.coordinates]
        else:
            _json['coordinates'] = self.coordinates

        # add system metadata
        if 'system' not in _json['metadata']:
            _json['metadata']['system'] = dict()
        if self.automated is not None:
            _json['metadata']['system']['automated'] = self.automated
        if self.object_id is not None:
            _json['metadata']['system']['objectId'] = self.object_id
        if self.status is not None:
            _json['metadata']['system']['status'] = self.status
        if self.type in ['segment', 'polyline']:
            _json['metadata']['system']['isOpen'] = self.is_open

        # add frame info
        if self.is_video:
            # get all snapshots but the first one
            snapshots = list()
            first_frame_num = min(self.frames)
            for frame_num in sorted(self.frames):
                if frame_num == first_frame_num:
                    # ignore first frame in snapshots
                    continue
                snapshots.append(self.frames[frame_num].to_snapshot())
            # add metadata to json
            _json['metadata']['system']['frame'] = self.current_frame
            _json['metadata']['system']['startTime'] = self.start_time
            _json['metadata']['system']['endTime'] = self.end_time
            if self.end_frame is not None:
                _json['metadata']['system']['endFrame'] = self.end_frame

            # add snapshots only if classification
            if self.type not in ['class', 'subtitle']:
                _json['metadata']['system']['snapshots_'] = snapshots
        else:
            # remove metadata if empty
            if len(_json['metadata']['system']) == 0:
                _json['metadata'].pop('system')
                if len(_json['metadata']) == 0:
                    _json.pop('metadata')

        return _json


@attr.s
class FrameAnnotation(entities.BaseEntity):
    """
    FrameAnnotation object
    """
    # parent annotation
    annotation = attr.ib()

    # annotations
    annotation_definition = attr.ib()

    # multi
    frame_num = attr.ib()
    fixed = attr.ib()

    ################################
    # parent annotation attributes #
    ################################

    @property
    def status(self):
        return self.annotation.status

    @property
    def timestamp(self):
        if self.annotation.fps is not None and self.frame_num is not None:
            return self.frame_num / self.annotation.fps if self.annotation.fps != 0 else None

    ####################################
    # annotation definition attributes #
    ####################################
    @property
    def type(self):
        return self.annotation.type

    @property
    def label(self):
        return self.annotation_definition.label

    @property
    def attributes(self):
        return self.annotation_definition.attributes

    @property
    def geo(self):
        return self.annotation_definition.geo

    @property
    def top(self):
        return self.annotation_definition.top

    @property
    def bottom(self):
        return self.annotation_definition.bottom

    @property
    def left(self):
        return self.annotation_definition.left

    @property
    def right(self):
        return self.annotation_definition.right

    @property
    def color(self):
        if self.annotation.item is None:
            return 255, 255, 255
        else:
            label = None
            for label in self.annotation.item.dataset.labels:
                if label.tag.lower() == self.label.lower():
                    return label.rgb
            if label is None:
                return 255, 255, 255

    @property
    def coordinates(self):
        coordinates = self.annotation_definition.to_coordinates(color=self.color)
        return coordinates

    @property
    def x(self):
        return self.annotation_definition.x

    @property
    def y(self):
        return self.annotation_definition.y

    @property
    def rx(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.rx
        else:
            return None

    @property
    def ry(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.ry
        else:
            return None

    @property
    def angle(self):
        if self.annotation_definition.type == 'ellipse':
            return self.annotation_definition.angle
        else:
            return None

    ######################
    # annotation methods #
    ######################
    def show(self, **kwargs):
        """
        Show annotation as ndarray
        :param kwargs: see annotation definition
        :return: ndarray of the annotation
        """
        return self.annotation_definition.show(**kwargs)

    @staticmethod
    def json_to_annotation_definition(_json):
        if _json['type'] == 'segment':
            annotation = entities.Polygon.from_json(_json)
        elif _json['type'] == 'polyline':
            annotation = entities.Polyline.from_json(_json)
        elif _json['type'] == 'box':
            annotation = entities.Box.from_json(_json)
        elif _json['type'] == 'point':
            annotation = entities.Point.from_json(_json)
        elif _json['type'] == 'binary':
            annotation = entities.Segmentation.from_json(_json)
        elif _json['type'] == 'class':
            annotation = entities.Classification.from_json(_json)
        elif _json['type'] == 'subtitle':
            annotation = entities.Subtitle.from_json(_json)
        elif _json['type'] == 'ellipse':
            annotation = entities.Ellipse.from_json(_json)
        elif _json['type'] == 'comparison':
            annotation = entities.Comparison.from_json(_json)
        else:
            annotation = entities.UndefinedAnnotationType.from_json(_json)
        return annotation

    #######
    # I/O #
    #######
    @classmethod
    def new(cls, annotation, annotation_definition, frame_num, fixed):
        return cls(
            # annotations
            annotation=annotation,
            annotation_definition=annotation_definition,

            # multi
            frame_num=frame_num,
            fixed=fixed
        )

    @classmethod
    def from_snapshot(cls, annotation, _json, fps):
        # get annotation class
        _json['type'] = annotation.type
        annotation_definition = cls.json_to_annotation_definition(_json=_json)

        frame_num = _json.get('frame', annotation.last_frame + 1)

        return cls(
            # annotations
            annotation=annotation,
            annotation_definition=annotation_definition,

            # multi
            frame_num=frame_num,
            fixed=_json.get('fixed', False)
        )

    def to_snapshot(self):
        snapshot_dict = {'frame': self.frame_num,
                         'fixed': self.fixed,
                         'label': self.label,
                         'attributes': self.attributes,
                         'type': self.type,
                         'data': self.coordinates}
        return snapshot_dict
