import numpy as np
import logging
import attr
import json

from PIL import Image
from collections import namedtuple

from .. import utilities, entities, PlatformException

logger = logging.getLogger(name=__name__)


@attr.s
class Annotation:
    """
    Annotations object
    """
    # annotation definition
    annotation_definition = attr.ib()

    # platform
    id = attr.ib()
    url = attr.ib()
    item_url = attr.ib()
    item = attr.ib()
    item_id = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedBy = attr.ib()
    updatedAt = attr.ib()
    type = attr.ib()
    dataset_url = attr.ib()

    # meta
    metadata = attr.ib()
    fps = attr.ib()
    status = attr.ib(default=None)
    object_id = attr.ib(default=None)
    automated = attr.ib(default=None)

    # snapshots
    frames = attr.ib(default=None)
    current_frame = attr.ib(default=0)

    # video attributes
    end_frame = attr.ib(default=0)
    end_time = attr.ib(default=0)
    start_frame = attr.ib(default=0)

    # temp
    platform_dict = attr.ib(default=None)

    ####################################
    # annotation definition attributes #
    ####################################
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
        label = None
        for label in self.item.dataset.labels:
            if label.tag.lower() == self.label.lower():
                return label.rgb
        if label is None:
            return 255, 255, 255

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
    def start_time(self):
        if len(self.frames) > 0:
            return self.frames[min(self.frames)].timestamp
        else:
            return 0

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

    def print(self):
        utilities.List([self]).print()

    def delete(self):
        """
        Remove an annotation from item
        :return: True
        """
        return self.item.annotations.delete(annotation_id=self.id)

    def update(self, system_metadata=False):
        """
        Update an existing annotation in host.
        :param system_metadata:
        :return: Annotation object
        """
        return self.item.annotations.update(annotations=self,
                                            system_metadata=system_metadata)

    def upload(self):
        """
        Create a new annotation in host
        :return:
        """
        return self.item.annotations.upload(annotations=self)

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
                json.dump(self.to_json(), f)
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
            if self.item.height is None:
                raise PlatformException('400', 'must provide item width and height')
            height = self.item.height
        if width is None:
            if self.item.width is None:
                raise PlatformException('400', 'must provide item width and height')
            width = self.item.width

        # color
        if color is None:
            if self.color is not None:
                color = self.color
            else:
                logger.warning('No color given, random color will be selected')
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
            image = np.zeros((height, width, len(color)))
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
    def new(cls, item, annotation_definition=None, object_id=None, automated=None, metadata=None, frame_num=0):
        """
        Create a new annotation object annotations

        :param item: item to annotate
        :param annotation_definition: annotation type object
        :param object_id: object_id
        :param automated: is automated
        :param metadata: metadata
        :param frame_num: optional - first frame number if video annotation
        :return: annotation object
        """
        # init annotations
        if metadata is None:
            metadata = dict()

        # frames
        frames = dict()

        # handle fps
        if item.fps is not None:
            fps = item.fps
        else:
            fps = None

        # get type
        ann_type = None
        if annotation_definition is not None:
            ann_type = annotation_definition.type

        # dataset
        dataset_url = None
        if item is not None:
            dataset_url = item.dataset_url

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

            # temp
            platform_dict=dict(),
        )

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
            if self.item.fps is None:
                raise PlatformException('400', 'Item does not have fps')
            else:
                self.fps = self.item.fps

        # calculate time stamp
        if frame_num is None:
            timestamp = 0
        else:
            timestamp = frame_num / self.fps

        # if this is first frame
        if self.annotation_definition is None:
            if frame_num is None:
                frame_num = 0
            self.start_frame = frame_num
            self.current_frame = frame_num
            self.end_frame = frame_num
            frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                        frame_num=frame_num,
                                        timestamp=timestamp,
                                        fixed=fixed,
                                        annotation=self)

            self.frames[frame_num] = frame
            self.set_frame(frame_num)
            self.end_time = self.end_frame / self.fps
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

        # calculate time stamp
        timestamp = frame_num / self.fps

        # add frame to annotation
        if not self.is_video:
            # create first frame from annotation definition
            frame = FrameAnnotation.new(annotation_definition=self.annotation_definition,
                                        frame_num=self.last_frame,
                                        timestamp=timestamp,
                                        fixed=fixed,
                                        annotation=self)

            self.frames[self.start_frame] = frame

        # create new time annotations
        frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                    frame_num=frame_num,
                                    timestamp=timestamp,
                                    fixed=fixed,
                                    annotation=self)

        self.frames[frame_num] = frame
        self.end_frame = max(self.frames)
        self.end_time = self.end_frame / self.fps

        return True

    @classmethod
    def from_json(cls, _json, item=None):
        """
        Create an annotation object from platform json
        :param _json: platform json
        :param item: item
        :return: annotation object
        """
        # handle 'note'
        if _json['type'] == 'note':
            return None
        if item is None:
            logger.info('Using Dummy item for loading annotations')
            named = namedtuple('Item', field_names=['mimetype', 'url', 'id', 'dataset_url'])
            item = named('image/jpeg', '', '', '')

        # get item type
        is_video = False
        if 'video' in item.mimetype:
            is_video = True

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

        ############
        # if video #
        ############
        if is_video:
            # get fps
            fps = item.fps

            # get video-only attributes    
            automated = None
            end_frame = None
            start_frame = 0
            end_time = 1.5
            # get first frame attribute
            first_frame_attributes = _json.get('attributes', first_frame_attributes)
            # get first frame coordinates
            first_frame_coordinates = _json.get('coordinates', first_frame_coordinates)
            # get first frame number
            if 'system' in metadata:
                first_frame_number = _json['metadata']['system'].get('frame', first_frame_number)
            # get first frame start time
            if 'system' in metadata:
                first_frame_start_time = _json['metadata']['system'].get('startTime', first_frame_start_time)
            # get first frame number
            if 'system' in metadata:
                start_frame = _json['metadata']['system'].get('frame', start_frame)

            if 'system' in metadata:
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
            fps = None
            end_frame = 0
            end_time = 0
            start_frame = 0
            # get automated
            automated = None
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
            item_url=_json.get('item', item.url),
            item=item,
            item_id=_json.get('itemId', item.id),
            dataset_url=_json.get('dataset', item.dataset_url),
            creator=_json['creator'],
            createdAt=_json['createdAt'],
            updatedBy=_json['updatedBy'],
            updatedAt=_json['updatedAt'],
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
            start_frame=start_frame
        )

        #################
        # if has frames #
        #################
        if is_video:
            if annotation.type == 'class':
                # for class type annotation create frames
                # make copies of the head annotations for all frames in it
                for frame_num in range(start_frame, end_frame + 1):
                    snapshot = {
                        'frame': frame_num,
                        'startTime': frame_num / fps,
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
                    annotation.annotation_definition = annotation.frames[min(frames)].annotation_definition
            else:
                # set first frame
                snapshot = {
                    'attributes': first_frame_attributes,
                    'coordinates': first_frame_coordinates,
                    'fixed': True,
                    'frame': first_frame_number,
                    'label': _json['label'],
                    'type': annotation.type,
                    'startTime': first_frame_start_time,
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
                                                        attr.fields(Annotation).metadata,
                                                        attr.fields(Annotation).creator,
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
        _json['datasetId'] = self.item.dataset.id

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
            if self.type != 'class':
                _json['metadata']['system']['snapshots_'] = snapshots
        else:
            # remove metadata if empty
            if len(_json['metadata']['system']) == 0:
                _json['metadata'].pop('system')
                if len(_json['metadata']) == 0:
                    _json.pop('metadata')

        return _json


@attr.s
class FrameAnnotation:
    """
    FrameAnnotation object
    """
    # parent annotation
    annotation = attr.ib()

    # annotations
    annotation_definition = attr.ib()

    # multi
    timestamp = attr.ib()
    frame_num = attr.ib()
    fixed = attr.ib()

    ################################
    # parent annotation attributes #
    ################################

    @property
    def status(self):
        return self.annotation.status

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
        elif _json['type'] == 'ellipse':
            annotation = entities.Ellipse.from_json(_json)
        else:
            raise ValueError('Type not implemented: %s' % _json['type'])
        return annotation

    #######
    # I/O #
    #######
    @classmethod
    def new(cls, annotation, annotation_definition, frame_num, fixed, timestamp=0):
        return cls(
            # annotations
            annotation=annotation,
            annotation_definition=annotation_definition,

            # multi
            timestamp=timestamp,
            frame_num=frame_num,
            fixed=fixed
        )

    @classmethod
    def from_snapshot(cls, annotation, _json, fps):
        # get annotation class
        _json['type'] = annotation.type
        annotation_definition = cls.json_to_annotation_definition(_json=_json)

        frame_num = _json.get('frame', None)
        timestamp = _json.get('startTime', 0)
        if frame_num is None:
            logger.warning(
                'Missing frame number from annotation. using time stamp, annotation id: %s' % (_json['id']))
            if fps is not None:
                frame_num = timestamp * fps
            else:
                raise PlatformException('400', 'Cannot get annotation becaue it does not have frame num and item does '
                                               'not have fps')

        return cls(
            # annotations
            annotation=annotation,
            annotation_definition=annotation_definition,

            # multi
            timestamp=timestamp,
            frame_num=frame_num,
            fixed=_json.get('fixed', False)
        )

    def to_snapshot(self):
        snapshot_dict = {'frame': self.frame_num,
                         'startTime': self.timestamp,
                         'fixed': self.fixed,
                         'label': self.label,
                         'attributes': self.attributes,
                         'type': self.type,
                         'data': self.coordinates}
        return snapshot_dict
