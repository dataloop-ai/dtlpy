import numpy as np
import traceback
import logging
import datetime
import webvtt
import copy
import attr
import json
import os

from PIL import Image
from enum import Enum

from .. import entities, PlatformException, repositories, ApiClient, exceptions

logger = logging.getLogger(name='dtlpy')


class ExportVersion(str, Enum):
    V1 = "V1"
    V2 = "V2"


class AnnotationStatus(str, Enum):
    ISSUE = "issue"
    APPROVED = "approved"
    REVIEW = "review"
    CLEAR = "clear"


class AnnotationType(str, Enum):
    BOX = "box"
    CUBE = "cube"
    CUBE3D = "cube_3d"
    CLASSIFICATION = "class"
    COMPARISON = "comparison"
    ELLIPSE = "ellipse"
    NOTE = "note"
    POINT = "point"
    POLYGON = "segment"
    POLYLINE = "polyline"
    POSE = "pose"
    SEGMENTATION = "binary"
    SUBTITLE = "subtitle"
    TEXT = "text_mark"


class ViewAnnotationOptions(str, Enum):
    """ The Annotations file types to download (JSON, MASK, INSTANCE, ANNOTATION_ON_IMAGE, VTT, OBJECT_ID).

    .. list-table::
       :widths: 15 150
       :header-rows: 1

       * - State
         - Description
       * - JSON
         - Dataloop json format
       * - MASK
         - PNG file that contains drawing annotations on it
       * - INSTANCE
         - An image file that contains 2D annotations
       * - ANNOTATION_ON_IMAGE
         - The source image with the annotations drawing in it
       * - VTT
         - An text file contains supplementary information about a web video
       * - OBJECT_ID
         - An image file that contains 2D annotations

    """
    JSON = "json"
    MASK = "mask"
    INSTANCE = "instance"
    ANNOTATION_ON_IMAGE = "img_mask"
    VTT = "vtt"
    OBJECT_ID = "object_id"


@attr.s
class Annotation(entities.BaseEntity):
    """
    Annotations object
    """
    # platform
    id = attr.ib()
    url = attr.ib(repr=False)
    item_url = attr.ib(repr=False)
    _item = attr.ib(repr=False)
    item_id = attr.ib()
    creator = attr.ib()
    created_at = attr.ib()
    updated_by = attr.ib(repr=False)
    updated_at = attr.ib(repr=False)
    type = attr.ib()
    source = attr.ib(repr=False)
    dataset_url = attr.ib(repr=False)

    # api
    _platform_dict = attr.ib(repr=False)
    # meta
    metadata = attr.ib(repr=False)
    fps = attr.ib(repr=False)
    hash = attr.ib(default=None, repr=False)
    dataset_id = attr.ib(default=None, repr=False)
    status = attr.ib(default=None, repr=False)
    object_id = attr.ib(default=None, repr=False)
    automated = attr.ib(default=None, repr=False)
    item_height = attr.ib(default=None)
    item_width = attr.ib(default=None)
    label_suggestions = attr.ib(default=None)

    # annotation definition
    _annotation_definition = attr.ib(default=None, repr=False, type=entities.BaseAnnotationDefinition)

    # snapshots
    frames = attr.ib(default=None, repr=False)
    current_frame = attr.ib(default=0, repr=False)

    # video attributes
    _end_frame = attr.ib(default=0, repr=False)
    _end_time = attr.ib(default=0, repr=False)
    _start_frame = attr.ib(default=0)
    _start_time = attr.ib(default=0)

    # sdk
    _dataset = attr.ib(repr=False, default=None)
    _datasets = attr.ib(repr=False, default=None)
    _annotations = attr.ib(repr=False, default=None)
    __client_api = attr.ib(default=None, repr=False)
    _items = attr.ib(repr=False, default=None)

    # temp
    _recipe_2_attributes = attr.ib(repr=False, default=None)

    ############
    # Platform #
    ############

    @property
    def annotation_definition(self):
        return self._annotation_definition

    @annotation_definition.setter
    def annotation_definition(self, ann_def):
        if ann_def is not None:
            ann_def._annotation = self
        self._annotation_definition = ann_def

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def updatedBy(self):
        return self.updated_by

    @property
    def _client_api(self) -> ApiClient:
        if self.__client_api is None:
            if self._item is None:
                raise PlatformException('400',
                                        'This action cannot be performed without an item entity. Please set item')
            else:
                self.__client_api = self._item._client_api
        assert isinstance(self.__client_api, ApiClient)
        return self.__client_api

    @property
    def dataset(self):
        if self._dataset is None:
            if self._item is not None:
                # get from item
                self._dataset = self._item.dataset
            else:
                # get directly
                self._dataset = self.datasets.get(dataset_id=self.dataset_id)
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def item(self):
        if self._item is None:
            self._item = self.items.get(item_id=self.item_id)
        assert isinstance(self._item, entities.Item)
        return self._item

    @property
    def annotations(self):
        if self._annotations is None:
            self._annotations = repositories.Annotations(client_api=self._client_api, item=self._item)
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
            elif self._item is not None:
                self._items = self._item.items
            else:
                self._items = repositories.Items(client_api=self._client_api, dataset=self._dataset)
        assert isinstance(self._items, repositories.Items)
        return self._items

    #########################
    # Annotation Properties #
    #########################
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
            color = self.annotation_definition._color
            if color is None:
                color = self.color
        coordinates = self.annotation_definition.to_coordinates(color=color)
        return coordinates

    @property
    def start_frame(self):
        return self._start_frame

    @start_frame.setter
    def start_frame(self, val):
        if not isinstance(val, float) and not isinstance(val, int):
            raise ValueError('Must input a valid number')
        self._start_frame = round(val)
        self._start_time = val / self.fps if self.fps else 0
        self.frames.start = self._start_frame

    @property
    def end_frame(self):
        return self._end_frame

    @end_frame.setter
    def end_frame(self, val):
        if not isinstance(val, float) and not isinstance(val, int):
            raise ValueError('Must input a valid number')
        self._end_frame = round(val)
        self._end_time = val / self.fps if self.fps else 0
        self.frames.end = self._end_frame

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, val):
        if not isinstance(val, float) and not isinstance(val, int):
            raise ValueError('Must input a valid number')
        self._start_frame = round(val * self.fps if self.fps else 0)
        self._start_time = val
        self.frames.start = self._start_frame

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, val):
        if not isinstance(val, float) and not isinstance(val, int):
            raise ValueError('Must input a valid number')
        self._end_frame = round(val * self.fps if self.fps else 0)
        self._end_time = val
        self.frames.end = self._end_frame

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
        if self.annotation_definition.type in ['ellipse', 'cube', 'box']:
            return self.annotation_definition.angle
        else:
            return None

    @property
    def messages(self):
        if hasattr(self.annotation_definition, 'messages'):
            return self.annotation_definition.messages
        else:
            return None

    @messages.setter
    def messages(self, messages):
        if self.type == 'note':
            self.annotation_definition.messages = messages
        else:
            raise PlatformException('400', 'Annotation of type {} does not have attribute messages'.format(self.type))

    def add_message(self, body: str = None):
        if self.type == 'note':
            return self.annotation_definition.add_message(body=body)
        else:
            raise PlatformException('400', 'Annotation of type {} does not have method add_message'.format(self.type))

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
    def height(self):
        return self.annotation_definition.height

    @height.setter
    def height(self, height):
        self.annotation_definition.height = height

    @property
    def width(self):
        return self.annotation_definition.width

    @width.setter
    def width(self, width):
        self.annotation_definition.width = width

    @property
    def description(self):
        return self.annotation_definition.description

    @description.setter
    def description(self, description):
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise ValueError("Description must get string")
        self.annotation_definition.description = description

    @property
    def last_frame(self):
        if len(self.frames.actual_keys()) == 0:
            return 0
        return max(self.frames.actual_keys())

    @property
    def label(self):
        return self.annotation_definition.label

    @label.setter
    def label(self, label):
        self.annotation_definition.label = label

    @property
    def _use_attributes_2(self):
        if self.__client_api is None and self._item is None:
            return os.environ.get("USE_ATTRIBUTE_2", 'false') == 'true'
        return self._client_api.attributes_mode.use_attributes_2

    @property
    def attributes(self):
        return self._recipe_2_attributes if self._use_attributes_2 else self.annotation_definition.attributes

    @attributes.setter
    def attributes(self, attributes):
        if self._use_attributes_2:
            if not isinstance(attributes, dict):
                raise ValueError(
                    'Attributes must be a dict. If you are using v1 attributes please use dl.use_attributes_2(False)')
            self._recipe_2_attributes = attributes
        else:
            if not isinstance(attributes, list):
                raise ValueError(
                    'Attributes must be a list. If you are using v2 attributes please use dl.use_attributes_2(True)')
            self.annotation_definition.attributes = attributes

    @property
    def color(self):
        # if "dataset" is not in self - this will always get the dataset
        if self.type == 'binary' and self.annotation_definition._color is not None:
            color = self.annotation_definition._color
        else:
            try:
                colors = self.dataset._get_ontology().color_map
            except (exceptions.BadRequest, exceptions.NotFound):
                colors = None
                logger.warning('Cant get dataset for annotation color. using default.')
            if colors is not None and self.label in colors:
                color = colors[self.label]
            else:
                color = (255, 255, 255)
        return color

    @color.setter
    def color(self, color):
        if self.type == 'binary':
            if not isinstance(color, tuple) or len(color) != 3:
                raise ValueError("Color must get tuple of length 3")
            self.annotation_definition._color = color
        else:
            raise exceptions.BadRequest(
                status_code='400',
                message='Invalid annotation type - Updating color is only available to binary annotation'
            )

    ####################
    # frame attributes #
    ####################
    @property
    def frame_num(self):
        if len(self.frames.actual_keys()) > 0:
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
        if len(self.frames.actual_keys()) > 0:
            return self.frames[self.current_frame].fixed
        else:
            return False

    @fixed.setter
    def fixed(self, fixed):
        if len(self.frames.actual_keys()) > 0:
            self.frames[self.current_frame].fixed = fixed

    @property
    def object_visible(self):
        if len(self.frames.actual_keys()) > 0:
            return self.frames[self.current_frame].object_visible
        else:
            return False

    @object_visible.setter
    def object_visible(self, object_visible):
        if len(self.frames.actual_keys()) > 0:
            self.frames[self.current_frame].object_visible = object_visible

    @property
    def is_video(self):
        if len(self.frames.actual_keys()) == 0:
            return False
        else:
            return True

    ##################
    # entity methods #
    ##################
    def update_status(self, status: AnnotationStatus = AnnotationStatus.ISSUE):
        """
        Set status on annotation

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or *developer* or be assigned a task that includes that item as an *annotation manager*.

        :param str status: can be AnnotationStatus.ISSUE, AnnotationStatus.APPROVED, AnnotationStatus.REVIEW, AnnotationStatus.CLEAR
        :return: Annotation object
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = annotation.update_status(status=dl.AnnotationStatus.ISSUE)
        """
        return self.annotations.update_status(annotation=self, status=status)

    def delete(self):
        """
        Remove an annotation from item

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = annotation.delete()
        """
        if self.id is None:
            raise PlatformException(
                '400',
                'Cannot delete annotation because it was not fetched from platform and therefore does not have an id'
            )
        return self.annotations.delete(annotation_id=self.id)

    def update(self, system_metadata=False):
        """
        Update an existing annotation in host.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param system_metadata: True, if you want to change metadata system
        :return: Annotation object
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = annotation.update()
        """
        return self.annotations.update(annotations=self,
                                       system_metadata=system_metadata)[0]

    def upload(self):
        """
        Create a new annotation in host

        **Prerequisites**: Any user can upload annotations.

        :return: Annotation entity
        :rtype: dtlpy.entities.annotation.Annotation
        """
        return self.annotations.upload(annotations=self)[0]

    def download(self,
                 filepath: str,
                 annotation_format: ViewAnnotationOptions = ViewAnnotationOptions.JSON,
                 height: float = None,
                 width: float = None,
                 thickness: int = 1,
                 with_text: bool = False,
                 alpha: float = 1):
        """
        Save annotation to file

        **Prerequisites**: Any user can upload annotations.

        :param str filepath: local path to where annotation will be downloaded to
        :param list annotation_format: options: list(dl.ViewAnnotationOptions)
        :param float height: image height
        :param float width: image width
        :param int thickness: line thickness
        :param bool with_text: get mask with text
        :param float alpha: opacity value [0 1], default 1
        :return: filepath
        :rtype: str

        **Example**:

        .. code-block:: python

            filepath = annotation.download(filepath='filepath', annotation_format=dl.ViewAnnotationOptions.MASK)
        """
        _, ext = os.path.splitext(filepath)
        if ext == '':
            if annotation_format == ViewAnnotationOptions.JSON:
                ext = '.json'
            else:
                if self.is_video:
                    ext = '.mp4'
                else:
                    ext = '.png'
            filepath = os.path.join(filepath, self.id + ext)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if annotation_format == ViewAnnotationOptions.JSON:
            with open(filepath, 'w') as f:
                json.dump(self.to_json(), f, indent=2)
        elif annotation_format == entities.ViewAnnotationOptions.VTT:
            _, ext = os.path.splitext(filepath)
            if ext != '.vtt':
                raise PlatformException(error='400', message='file extension must be vtt')
            vtt = webvtt.WebVTT()
            if self.type in ['subtitle']:
                s = str(datetime.timedelta(seconds=self.start_time))
                if len(s.split('.')) == 1:
                    s += '.000'
                e = str(datetime.timedelta(seconds=self.end_time))
                if len(e.split('.')) == 1:
                    e += '.000'
                caption = webvtt.Caption(
                    '{}'.format(s),
                    '{}'.format(e),
                    '{}'.format(self.coordinates['text'])
                )
                vtt.captions.append(caption)
            vtt.save(filepath)
        else:
            if self.is_video:
                entities.AnnotationCollection(item=self.item, annotations=[self])._video_maker(
                    input_filepath=None,
                    output_filepath=filepath,
                    annotation_format=annotation_format,
                    thickness=thickness,
                    alpha=alpha,
                    with_text=with_text
                )
            else:
                mask = self.show(thickness=thickness,
                                 alpha=alpha,
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

        **Prerequisites**: Any user can upload annotations.

        :param int frame: frame number
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = annotation.set_frame(frame=10)
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
    def show(self,
             image=None,
             thickness=None,
             with_text=False,
             height=None,
             width=None,
             annotation_format: ViewAnnotationOptions = ViewAnnotationOptions.MASK,
             color=None,
             label_instance_dict=None,
             alpha=1,
             frame_num=None
             ):
        """
        Show annotations
        mark the annotation of the image array and return it

        **Prerequisites**: Any user can upload annotations.

        :param image: empty or image to draw on
        :param int thickness: line thickness
        :param bool with_text: add label to annotation
        :param float height: height
        :param float width: width
        :param dl.ViewAnnotationOptions annotation_format: list(dl.ViewAnnotationOptions)
        :param tuple color: optional - color tuple
        :param label_instance_dict: the instance labels
        :param float alpha: opacity value [0 1], default 1
        :param int frame_num: for video annotation, show specific fame
        :return: list or single ndarray of the annotations

        **Exampls**:

        .. code-block:: python

            image = annotation.show(image='ndarray',
                            thickness=1,
                            annotation_format=dl.VIEW_ANNOTATION_OPTIONS_MASK,
                            )
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise
        # sanity check for alpha
        if alpha > 1 or alpha < 0:
            raise ValueError(
                'input variable alpha in annotation.show() should be between 0 and 1. got: {!r}'.format(alpha))
        if height is None:
            if self._item is None or self._item.height is None:
                if image is None:
                    raise PlatformException(error='400', message='must provide item width and height')
                else:
                    height = image.shape[0]
            else:
                height = self._item.height
        if width is None:
            if self._item is None or self._item.width is None:
                if image is None:
                    raise PlatformException(error='400', message='must provide item width and height')
                else:
                    width = image.shape[1]
            else:
                width = self._item.width

        # try getting instance map from dataset, otherwise set to default
        if annotation_format in [entities.ViewAnnotationOptions.INSTANCE, entities.ViewAnnotationOptions.OBJECT_ID] and \
                label_instance_dict is None:
            if self._dataset is not None:
                label_instance_dict = self._dataset.instance_map
            else:
                if self._item is not None and self._item._dataset is not None:
                    label_instance_dict = self._item._dataset.instance_map
            if label_instance_dict is None:
                logger.warning("Couldn't set label_instance_dict in annotation.show(). All labels will be mapped to 1")
                label_instance_dict = dict()

        in_video_range = True
        if frame_num is not None:
            in_video_range = self.set_frame(frame_num)

        if self.is_video and not in_video_range:
            if image is None:
                image = self._get_default_mask(annotation_format=annotation_format,
                                               width=width,
                                               height=height,
                                               label_instance_dict=label_instance_dict)
            return image
        else:
            image = self._show_single_frame(image=image,
                                            thickness=thickness,
                                            alpha=alpha,
                                            with_text=with_text,
                                            height=height,
                                            width=width,
                                            annotation_format=annotation_format,
                                            color=color,
                                            label_instance_dict=label_instance_dict)
        return image

    def _show_single_frame(self,
                           image=None,
                           thickness=None,
                           with_text=False,
                           height=None,
                           width=None,
                           annotation_format: ViewAnnotationOptions = ViewAnnotationOptions.MASK,
                           color=None,
                           label_instance_dict=None,
                           alpha=None):
        """
        Show annotations
        mark the annotation of the single frame array and return it
        :param image: empty or image to draw on
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param height: height
        :param width: width
        :param annotation_format: list(dl.ViewAnnotationOptions)
        :param color: optional - color tuple
        :param label_instance_dict: the instance labels
        :param alpha: opacity value [0 1], default 1
        :return: ndarray of the annotations
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise
        # height/width
        if self.annotation_definition.type == 'cube_3d':
            logger.warning('the show for 3d_cube is not supported.')
            return image
        if annotation_format == entities.ViewAnnotationOptions.MASK:
            # create an empty mask
            if image is None:
                image = self._get_default_mask(annotation_format=annotation_format,
                                               width=width,
                                               height=height,
                                               label_instance_dict=label_instance_dict)
            else:
                if len(image.shape) == 2:
                    # image is gray
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
                elif image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
                elif image.shape[2] == 4:
                    pass
                else:
                    raise PlatformException(
                        error='1001',
                        message='Unknown image shape. expected depth: gray or RGB or RGBA. got: {}'.format(image.shape))
        elif annotation_format == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE:
            if image is None:
                raise PlatformException(error='1001',
                                        message='Must input image with ANNOTATION_ON_IMAGE view option.')
        elif annotation_format in [entities.ViewAnnotationOptions.INSTANCE, entities.ViewAnnotationOptions.OBJECT_ID]:
            if image is None:
                # create an empty mask
                image = self._get_default_mask(annotation_format=annotation_format,
                                               width=width,
                                               height=height,
                                               label_instance_dict=label_instance_dict)
            else:
                if len(image.shape) != 2:
                    raise PlatformException(
                        error='1001',
                        message='Image shape must be 2d array when trying to draw instance on image')
            # create a dictionary of labels and ids
        else:
            raise PlatformException(error='1001',
                                    message='unknown annotations format: "{}". known formats: "{}"'.format(
                                        annotation_format, '", "'.join(list(entities.ViewAnnotationOptions))))
        # color
        if color is None:
            if annotation_format in [entities.ViewAnnotationOptions.MASK,
                                     entities.ViewAnnotationOptions.INSTANCE,
                                     entities.ViewAnnotationOptions.OBJECT_ID]:
                color = self._get_color_for_show(annotation_format=annotation_format,
                                                 alpha=alpha,
                                                 label_instance_dict=label_instance_dict)
            else:
                raise PlatformException(error='1001',
                                        message='unknown annotations format: {}. known formats: "{}"'.format(
                                            annotation_format, '", "'.join(list(entities.ViewAnnotationOptions))))

        return self.annotation_definition.show(image=image,
                                               thickness=thickness,
                                               with_text=with_text,
                                               height=height,
                                               width=width,
                                               annotation_format=annotation_format,
                                               color=color,
                                               alpha=alpha)

    def _get_color_for_show(self, annotation_format, alpha=1, label_instance_dict=None):
        if annotation_format == entities.ViewAnnotationOptions.MASK:
            color = self.color
            if len(color) == 3:
                color = color + (int(alpha * 255),)
        elif annotation_format == entities.ViewAnnotationOptions.INSTANCE:
            color = label_instance_dict.get(self.label, 1)
        elif annotation_format == entities.ViewAnnotationOptions.OBJECT_ID:
            if self.object_id is None:
                raise ValueError('Try to show object_id but annotation has no value. annotation id: {}'.format(self.id))
            color = int(self.object_id)
        else:
            raise ValueError('cant find color for the annotation format: {}'.format(annotation_format))
        return color

    def _get_default_mask(self, annotation_format, height, width, label_instance_dict):
        """
        Create a default mask take from the colors or instance map. tag should '$default'.
        Default value is zeros

        :param annotation_format: dl.AnnotationOptions to show
        :param height: item height
        :param width: item width
        :return:
        """
        if annotation_format == entities.ViewAnnotationOptions.MASK:
            try:
                colors = self.dataset._get_ontology().color_map
            except exceptions.BadRequest:
                colors = None
                logger.warning('Cant get dataset for annotation color. using default.')
            if colors is not None and '$default' in colors:
                default_color = colors['$default']
            else:
                default_color = None
            if default_color is None:
                default_color = (0, 0, 0, 0)
            if len(default_color) == 3:
                default_color += (255,)
            if len(default_color) != 4:
                raise ValueError('default color for show() mask should be with len 3 or 4 (RGB/RGBA)')
            image = np.full(shape=(height, width, 4), fill_value=default_color, dtype=np.uint8)
        elif annotation_format in [entities.ViewAnnotationOptions.INSTANCE,
                                   entities.ViewAnnotationOptions.OBJECT_ID]:
            default_color = 0
            if '$default' in label_instance_dict:
                default_color = label_instance_dict['$default']
            image = np.full(shape=(height, width), fill_value=default_color, dtype=np.uint8)
        else:
            raise ValueError('cant create default mask for annotation_format: {}'.format(annotation_format))
        return image

    #######
    # I/O #
    #######
    @classmethod
    def new(cls,
            item=None,
            annotation_definition=None,
            object_id=None,
            automated=True,
            metadata=None,
            frame_num=None,
            parent_id=None,
            start_time=None,
            item_height=None,
            item_width=None,
            end_time=None):
        """
        Create a new annotation object annotations

        **Prerequisites**: Any user can upload annotations.

        :param dtlpy.entities.item.Items item: item to annotate
        :param annotation_definition: annotation type object
        :param str object_id: object_id
        :param bool automated: is automated
        :param dict metadata: metadata
        :param int frame_num: optional - first frame number if video annotation
        :param str parent_id: add parent annotation ID
        :param start_time: optional - start time if video annotation
        :param float item_height: annotation item's height
        :param float item_width: annotation item's width
        :param end_time: optional - end time if video annotation
        :return: annotation object
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = annotation.new(item='item_entity,
                            annotation_definition=dl.Box(top=10,left=10,bottom=100, right=100,label='labelName'))
                            )
        """
        if frame_num is None:
            frame_num = 0

        if object_id is not None:
            if isinstance(object_id, int):
                object_id = '{}'.format(object_id)
            elif not isinstance(object_id, str) or not object_id.isnumeric():
                raise ValueError('Object id must be an int or a string containing only numbers.')

        # init annotations
        if metadata is None:
            metadata = dict()

        # add parent
        if parent_id is not None:
            if 'system' not in metadata:
                metadata['system'] = dict()
            metadata['system']['parentId'] = parent_id

        # add note status to metadata
        if annotation_definition is not None and annotation_definition.type == 'note':
            if 'system' not in metadata:
                metadata['system'] = dict()
            metadata['system']['status'] = annotation_definition.status

        # handle fps
        fps = None
        if item is not None:
            if item.fps is not None:
                fps = item.fps
            elif item.mimetype is not None and 'audio' in item.mimetype:
                fps = 1000

        # get type
        ann_type = None
        if annotation_definition is not None:
            ann_type = annotation_definition.type

        # dataset
        dataset_url = None
        dataset_id = None
        if item is not None:
            dataset_url = item.dataset_url
            dataset_id = item.dataset_id

        if start_time is None:
            if fps is not None and frame_num is not None:
                start_time = frame_num / fps if fps != 0 else 0
            else:
                start_time = 0
        if end_time is None:
            end_time = start_time

        if frame_num is None:
            frame_num = 0

        # frames
        frames = entities.ReflectDict(
            value_type=FrameAnnotation,
            on_access=Annotation.on_access,
            start=frame_num,
            end=frame_num
        )

        res = cls(
            # platform
            id=None,
            url=None,
            item_url=None,
            item=item,
            item_id=None,
            creator=None,
            created_at=None,
            updated_by=None,
            updated_at=None,
            object_id=object_id,
            type=ann_type,
            dataset_url=dataset_url,
            dataset_id=dataset_id,
            item_height=item_height,
            item_width=item_width,

            # meta
            metadata=metadata,
            fps=fps,
            status=None,
            automated=automated,

            # snapshots
            frames=frames,

            # video only attributes
            end_frame=frame_num,
            end_time=end_time,
            start_frame=frame_num,
            start_time=start_time,

            # temp
            platform_dict=dict(),
            source='sdk'
        )

        if annotation_definition:
            res.annotation_definition = annotation_definition

        if annotation_definition and annotation_definition.attributes:
            res.attributes = annotation_definition.attributes

        return res

    def add_frames(self,
                   annotation_definition,
                   frame_num=None,
                   end_frame_num=None,
                   start_time=None,
                   end_time=None,
                   fixed=True,
                   object_visible=True):
        """
        Add a frames state to annotation

        **Prerequisites**: Any user can upload annotations.

        :param annotation_definition: annotation type object - must be same type as annotation
        :param int frame_num: first frame number
        :param int end_frame_num: last frame number
        :param start_time: starting time for video
        :param end_time: ending time for video
        :param bool fixed: is fixed
        :param bool object_visible: does the annotated object is visible
        :return:

        **Example**:

        .. code-block:: python

            annotation.add_frames(frame_num=10,
                            annotation_definition=dl.Box(top=10,left=10,bottom=100, right=100,label='labelName'))
                            )
        """
        # handle fps
        if self.fps is None:
            if self._item is not None:
                if self._item.fps is not None:
                    self.fps = self._item.fps
        if self.fps is None:
            raise PlatformException('400', 'Annotation must have fps in order to perform this action')

        if frame_num is None:
            frame_num = int(np.round(start_time * self.fps))

        if end_frame_num is None:
            if end_time is not None:
                end_frame_num = int(np.round(end_time * self.fps))
            else:
                end_frame_num = frame_num

        for frame in range(frame_num, end_frame_num + 1):
            self.add_frame(annotation_definition=annotation_definition,
                           frame_num=frame,
                           fixed=fixed,
                           object_visible=object_visible)

    def add_frame(self,
                  annotation_definition,
                  frame_num=None,
                  fixed=True,
                  object_visible=True):
        """
        Add a frame state to annotation

        :param annotation_definition: annotation type object - must be same type as annotation
        :param int frame_num: frame number
        :param bool fixed: is fixed
        :param bool object_visible: does the annotated object is visible
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = annotation.add_frame(frame_num=10,
                            annotation_definition=dl.Box(top=10,left=10,bottom=100, right=100,label='labelName'))
                            )
        """
        # handle fps
        if self.fps is None:
            if self._item is not None:
                if self._item.fps is not None:
                    self.fps = self._item.fps
        if self.fps is None:
            raise PlatformException('400', 'Annotation must have fps in order to perform this action')

        # if this is first frame
        if self.annotation_definition is None:

            if frame_num is None:
                frame_num = 0

            frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                        frame_num=frame_num,
                                        fixed=fixed,
                                        object_visible=object_visible,
                                        annotation=self)

            self.frames[frame_num] = frame
            self.set_frame(frame_num)
            self.current_frame = frame_num
            self.end_frame = frame_num
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
                                        object_visible=object_visible,
                                        annotation=self)

            self.frames[self.start_frame] = frame

        # create new time annotations
        frame = FrameAnnotation.new(annotation_definition=annotation_definition,
                                    frame_num=frame_num,
                                    fixed=fixed,
                                    object_visible=object_visible,
                                    annotation=self)

        self.frames[frame_num] = frame
        if not self.frames[frame_num].fixed and self.start_frame < frame_num:
            frame_last = self.frames[frame_num - 1].to_snapshot()
            frame_current = self.frames[frame_num].to_snapshot()
            frame_last.pop('frame')
            frame_current.pop('frame')
            if frame_last == frame_current:
                self.frames[frame_num]._interpolation = True
        self.end_frame = max(self.last_frame, frame_num)

        return True

    @staticmethod
    def _protected_from_json(_json,
                             item=None,
                             client_api=None,
                             annotations=None,
                             is_video=None,
                             fps=None,
                             item_metadata=None,
                             dataset=None):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param item: item
        :param client_api: ApiClient entity
        :param annotations:
        :param is_video:
        :param fps:
        :param item_metadata:
        :param dataset
        :return: annotation object
        """
        try:
            annotation = Annotation.from_json(_json=_json,
                                              item=item,
                                              client_api=client_api,
                                              annotations=annotations,
                                              is_video=is_video,
                                              fps=fps,
                                              item_metadata=item_metadata,
                                              dataset=dataset)
            status = True
        except Exception:
            annotation = traceback.format_exc()
            status = False
        return status, annotation

    @classmethod
    def from_json(cls,
                  _json,
                  item=None,
                  client_api=None,
                  annotations=None,
                  is_video=None,
                  fps=None,
                  item_metadata=None,
                  dataset=None,
                  is_audio=None):
        """
        Create an annotation object from platform json

        :param dict _json: platform json
        :param dtlpy.entities.item.Item item: item
        :param client_api: ApiClient entity
        :param annotations:
        :param bool is_video: is video
        :param fps: video fps
        :param item_metadata: item metadata
        :param dataset: dataset entity
        :param bool is_audio: is audio
        :return: annotation object
        :rtype: dtlpy.entities.annotation.Annotation
        """
        if item_metadata is None:
            item_metadata = dict()

        if is_video is None:
            if item is None:
                if _json['metadata'].get('system', {}).get('endFrame', 0) > 0:
                    is_video = True
                else:
                    is_video = False
            else:
                # get item type
                if item.mimetype is not None and 'video' in item.mimetype:
                    is_video = True

        if is_audio is None:
            if item is None:
                is_audio = False
            else:
                # get item type
                if item.mimetype is not None and 'audio' in item.mimetype:
                    is_audio = True

        item_url = _json.get('item', item.url if item is not None else None)
        item_id = _json.get('itemId', item.id if item is not None else None)
        dataset_url = _json.get('dataset', item.dataset_url if item is not None else None)
        dataset_id = _json.get('datasetId', item.dataset_id if item is not None else None)

        if item is not None:
            if item.id != item_id:
                logger.warning('Annotation has been fetched from a item that is not belong to it')
                item = None

        if dataset is not None:
            if dataset.id != dataset_id:
                logger.warning('Annotation has been fetched from a dataset that is not belong to it')
                dataset = None

        # get id
        annotation_id = None
        if 'id' in _json:
            annotation_id = _json['id']
        elif '_id' in _json:
            annotation_id = _json['_id']

        metadata = _json.get('metadata', dict())

        # get metadata, status, attributes and object id
        object_id = None
        status = None
        if 'system' in metadata and metadata['system'] is not None:
            object_id = _json['metadata']['system'].get('objectId', object_id)
            status = _json['metadata']['system'].get('status', status)

        if client_api is not None:
            recipe_2_attributes = client_api.attributes_mode.use_attributes_2
        else:
            recipe_2_attributes = False
        named_attributes = metadata.get('system', dict()).get('attributes', None)
        attributes = named_attributes if recipe_2_attributes else _json.get('attributes', None)

        first_frame_attributes = attributes
        first_frame_coordinates = list()
        first_frame_number = 0
        first_frame_start_time = 0
        automated = None
        end_frame = None
        start_time = 0
        start_frame = 0
        end_time = None
        annotation_definition = None

        ############
        # if video #
        ############
        if is_video or is_audio:
            # get fps
            if item is not None and item.fps is not None:
                fps = item.fps
            if fps is None:
                if is_video:
                    fps = item_metadata.get('fps', 25)
                else:
                    item_metadata.get('fps', 1000)

            # get video-only attributes
            end_time = 1.5
            # get first frame attribute
            first_frame_attributes = first_frame_attributes
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
        ################
        # if not video #
        ################
        if not is_video or is_audio:
            # get coordinates
            coordinates = _json.get('coordinates', list())
            # set video only attributes
            if not is_audio:
                end_time = 0
            # get automated
            if 'system' in metadata and metadata['system'] is not None:
                automated = metadata['system'].get('automated', automated)
            # set annotation definition
            def_dict = {'type': _json['type'],
                        'coordinates': coordinates,
                        'label': _json['label'],
                        'attributes': attributes}
            annotation_definition = FrameAnnotation.json_to_annotation_definition(def_dict)

        frames = entities.ReflectDict(
            value_type=FrameAnnotation,
            on_access=Annotation.on_access,
            start=start_frame,
            end=end_frame
        )

        # init annotation
        annotation = cls(
            # temp
            platform_dict=copy.deepcopy(_json),
            # platform
            id=annotation_id,
            url=_json.get('url', None),
            item_url=item_url,
            item=item,
            item_id=item_id,
            dataset=dataset,
            dataset_url=dataset_url,
            dataset_id=dataset_id,
            creator=_json['creator'],
            created_at=_json['createdAt'],
            updated_by=_json['updatedBy'],
            updated_at=_json['updatedAt'],
            hash=_json.get('hash', None),
            object_id=object_id,
            type=_json['type'],
            item_width=item_metadata.get('width', None),
            item_height=item_metadata.get('height', None),
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
            start_time=start_time,
            recipe_2_attributes=named_attributes,
            label_suggestions=_json.get('labelSuggestions', None),
            source=_json.get('source', None)
        )
        annotation.annotation_definition = annotation_definition
        annotation.__client_api = client_api
        if annotation_definition:
            description = _json.get('description', None)
            if description is not None:
                annotation.description = description

        #################
        # if has frames #
        #################
        if is_video:
            # set first frame
            snapshot = {
                'attributes': first_frame_attributes,
                'coordinates': first_frame_coordinates,
                'fixed': True,
                'objectVisible': True,
                'frame': first_frame_number,
                'label': _json['label'],
                'type': annotation.type,
                'namedAttributes': named_attributes
            }

            # add first frame
            frame = FrameAnnotation.from_snapshot(
                _json=snapshot,
                annotation=annotation,
                fps=fps
            )
            annotation.frames[frame.frame_num] = frame
            annotation.annotation_definition = frame.annotation_definition

            # put snapshots if there are any
            for snapshot in _json['metadata']['system'].get('snapshots_', []):
                frame = FrameAnnotation.from_snapshot(
                    _json=snapshot,
                    annotation=annotation,
                    fps=fps
                )

                annotation.frames[frame.frame_num] = frame

            annotation.annotation_definition = annotation.frames[min(frames.actual_keys())].annotation_definition
            if annotation.annotation_definition:
                description = _json.get('description', None)
                if description is not None:
                    annotation.description = description

        return annotation

    @staticmethod
    def on_access(reflect_dict, actual_key: int, requested_key: int, val):
        val = copy.copy(val)
        val._interpolation = True
        val.fixed = False
        val.frame_num = requested_key
        reflect_dict[requested_key] = val
        return val

    def to_json(self):
        """
        Convert annotation object to a platform json representatio

        :return: platform json
        :rtype: dict
        """
        if len(self.frames.actual_keys()) > 0:
            self.set_frame(min(self.frames.actual_keys()))
        _json = attr.asdict(self,
                            filter=attr.filters.include(attr.fields(Annotation).id,
                                                        attr.fields(Annotation).url,
                                                        attr.fields(Annotation).metadata,
                                                        attr.fields(Annotation).creator,
                                                        attr.fields(Annotation).hash,
                                                        attr.fields(Annotation).metadata))

        # property attributes
        item_id = self.item_id
        if item_id is None and self._item is not None:
            item_id = self._item.id

        _json['itemId'] = item_id
        _json['item'] = self.item_url
        _json['label'] = self.label

        # Need to put back after transition to attributes 2.0
        # _json['attributes'] = self.attributes

        _json['dataset'] = self.dataset_url

        _json['createdAt'] = self.created_at
        _json['updatedBy'] = self.updated_by
        _json['updatedAt'] = self.updated_at
        _json['source'] = self.source

        if self.description is not None:
            _json['description'] = self.description

        if self.label_suggestions:
            _json['labelSuggestions'] = self.label_suggestions

        if self._item is not None and self.dataset_id is None:
            _json['datasetId'] = self._item.dataset_id
        else:
            _json['datasetId'] = self.dataset_id

        _json['type'] = self.type
        if self.type != 'class':
            _json['coordinates'] = self.coordinates

        # add system metadata
        if _json['metadata'].get('system', None) is None:
            _json['metadata']['system'] = dict()
        if self.automated is not None:
            _json['metadata']['system']['automated'] = self.automated
        if self.object_id is not None:
            _json['metadata']['system']['objectId'] = self.object_id
        if self.status is not None:
            # if status is CLEAR need to set status to None so it will be deleted in backend
            _json['metadata']['system']['status'] = self.status if self.status != AnnotationStatus.CLEAR else None

        if isinstance(self.annotation_definition, entities.Description):
            _json['metadata']['system']['system'] = True

        if self._use_attributes_2:
            _json['metadata']['system']['attributes'] = self._recipe_2_attributes
            if 'attributes' in self._platform_dict:
                _json['attributes'] = self._platform_dict['attributes']
        else:
            _json['attributes'] = self.attributes
            orig_metadata_system = self._platform_dict.get('metadata', {}).get('system', {})
            if 'attributes' in orig_metadata_system:
                _json['metadata']['system']['attributes'] = orig_metadata_system['attributes']

        # add frame info
        if self.is_video or (self.end_time and self.end_time > 0) or (self.end_frame and self.end_frame > 0):
            # get all snapshots but the first one
            snapshots = list()
            frame_numbers = self.frames.actual_keys() if len(self.frames.actual_keys()) else []
            for frame_num in sorted(frame_numbers):
                if frame_num <= self.frames.start:
                    continue
                if frame_num > self.frames.end:
                    break
                if not self.frames[frame_num]._interpolation or self.frames[frame_num].fixed:
                    snapshots.append(self.frames[frame_num].to_snapshot())
                    self.frames[frame_num]._interpolation = False
            # add metadata to json
            _json['metadata']['system']['frame'] = self.start_frame
            _json['metadata']['system']['startTime'] = self.start_time
            _json['metadata']['system']['endTime'] = self.end_time
            if self.end_frame is not None:
                _json['metadata']['system']['endFrame'] = self.end_frame

            # add snapshots only if classification
            if self.type not in ['subtitle']:
                _json['metadata']['system']['snapshots_'] = snapshots

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
    object_visible = attr.ib()

    # temp
    _recipe_2_attributes = attr.ib(repr=False, default=None)
    _interpolation = attr.ib(repr=False, default=False)

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

    @label.setter
    def label(self, label):
        self.annotation_definition.label = label

    @property
    def attributes(self):
        return self._recipe_2_attributes if self.annotation._use_attributes_2 else self.annotation_definition.attributes

    @attributes.setter
    def attributes(self, attributes):
        if self.annotation._use_attributes_2:
            if not isinstance(attributes, dict):
                raise ValueError(
                    'Attributes must be a dict. If you are using v1 attributes please use dl.use_attributes_2(False)')
            self._recipe_2_attributes = attributes
        else:
            if not isinstance(attributes, list):
                raise ValueError(
                    'Attributes must be a list. If you are using v2 attributes please use dl.use_attributes_2(True)')
            self.annotation_definition.attributes = attributes

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
        if self.annotation_definition.type in ['ellipse', 'box']:
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
        elif _json['type'] == 'cube':
            annotation = entities.Cube.from_json(_json)
        elif _json['type'] == 'cube_3d':
            annotation = entities.Cube3d.from_json(_json)
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
        elif _json['type'] == 'note':
            annotation = entities.Note.from_json(_json)
        elif _json['type'] == 'pose':
            annotation = entities.Pose.from_json(_json)
        else:
            annotation = entities.UndefinedAnnotationType.from_json(_json)
        return annotation

    #######
    # I/O #
    #######
    @classmethod
    def new(cls, annotation, annotation_definition, frame_num, fixed, object_visible=True):
        """
        new frame state to annotation

        :param annotation: annotation
        :param annotation_definition: annotation type object - must be same type as annotation
        :param frame_num: frame number
        :param fixed: is fixed
        :param object_visible: does the annotated object is visible
        :return: FrameAnnotation object
        """
        frame = cls(
            # annotations
            annotation=annotation,
            annotation_definition=annotation_definition,

            # multi
            frame_num=frame_num,
            fixed=fixed,
            object_visible=object_visible,
        )
        if annotation_definition.attributes:
            frame.attributes = annotation_definition.attributes
        return frame

    @classmethod
    def from_snapshot(cls, annotation, _json, fps):
        """
        new frame state to annotation

        :param annotation: annotation
        :param _json: annotation type object - must be same type as annotation
        :param fps: frame number
        :return: FrameAnnotation object
        """
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
            fixed=_json.get('fixed', False),
            object_visible=_json.get('objectVisible', True),

            # temp
            recipe_2_attributes=_json.get('namedAttributes', None)
        )

    def to_snapshot(self):

        snapshot_dict = {
            'frame': self.frame_num,
            'fixed': self.fixed,
            'label': self.label,
            'type': self.type,
            'objectVisible': self.object_visible,
            'data': self.coordinates
        }

        if self.annotation._use_attributes_2:
            snapshot_dict['namedAttributes'] = self._recipe_2_attributes
        else:
            snapshot_dict['attributes'] = self.attributes

        return snapshot_dict
