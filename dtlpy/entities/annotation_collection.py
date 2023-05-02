import mimetypes
import traceback
import datetime
import webvtt
import logging
import attr
import json
import os

import numpy as np
from PIL import Image

from .. import entities, PlatformException, miscellaneous

logger = logging.getLogger(name='dtlpy')


@attr.s
class AnnotationCollection(entities.BaseEntity):
    """
        Collection of Annotation entity
    """
    item = attr.ib(default=None)
    annotations = attr.ib()  # type: miscellaneous.List[entities.Annotation]
    _dataset = attr.ib(repr=False, default=None)
    _colors = attr.ib(repr=False, default=None)

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.item.dataset
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @annotations.default
    def set_annotations(self):
        return list()

    def __iter__(self):
        for annotation in self.annotations:
            yield annotation

    def __getitem__(self, index: int):
        return self.annotations[index]

    def __len__(self):
        return len(self.annotations)

    def add(self,
            annotation_definition,
            object_id=None,
            frame_num=None,
            end_frame_num=None,
            start_time=None,
            end_time=None,
            automated=True,
            fixed=True,
            object_visible=True,
            metadata=None,
            parent_id=None,
            model_info=None):
        """
        Add annotations to collection

        :param annotation_definition: dl.Polygon, dl.Segmentation, dl.Point, dl.Box etc
        :param object_id: Object id (any id given by user). If video - must input to match annotations between frames
        :param frame_num: video only, number of frame
        :param end_frame_num: video only, the end frame of the annotation
        :param start_time: video only, start time of the annotation
        :param end_time: video only, end time of the annotation
        :param automated:
        :param fixed: video only, mark frame as fixed
        :param object_visible: video only, does the annotated object is visible
        :param metadata: optional- metadata dictionary for annotation
        :param parent_id: set a parent for this annotation (parent annotation ID)
        :param model_info: optional - set model on annotation {'name',:'', 'confidence':0}
        :return:
        """
        if model_info is not None:
            if not isinstance(model_info, dict) or 'name' not in model_info or 'confidence' not in model_info:
                raise ValueError('"model_info" must be a dict with keys: "name" and "confidence"')
            if metadata is None:
                metadata = dict()
            if 'user' not in metadata:
                metadata['user'] = dict()
            metadata['user']['model'] = {'name': model_info['name'],
                                         'confidence': float(model_info['confidence']),
                                         'model_id': model_info.get('model_id'),
                                         'snapshot_id': model_info.get('snapshot_id'),
                                         }
            metadata['user']['annotation_type'] = 'prediction'

        # to support list of definitions with same parameters
        if not isinstance(annotation_definition, list):
            annotation_definition = [annotation_definition]

        for single_definition in annotation_definition:
            annotation = entities.Annotation.new(item=self.item,
                                                 annotation_definition=single_definition,
                                                 frame_num=frame_num,
                                                 automated=automated,
                                                 metadata=metadata,
                                                 object_id=object_id,
                                                 parent_id=parent_id,
                                                 start_time=start_time,
                                                 end_time=end_time)
            #  add frame if exists
            if (frame_num is not None or start_time is not None) and (
                    self.item is None or 'audio' not in self.item.metadata.get('system').get(
                    'mimetype', '')):
                if object_id is None:
                    raise ValueError('Video Annotation must have object_id.')
                else:
                    if isinstance(object_id, int):
                        object_id = '{}'.format(object_id)
                    elif not isinstance(object_id, str) or not object_id.isnumeric():
                        raise ValueError('Object id must be an int or a string containing only numbers.')
                # find matching element_id
                matched_ind = [i_annotation
                               for i_annotation, annotation in enumerate(self.annotations)
                               if annotation.object_id == object_id]
                if len(matched_ind) == 0:
                    # no matching object id found - create new one
                    self.annotations.append(annotation)
                    matched_ind = len(self.annotations) - 1
                elif len(matched_ind) == 1:
                    matched_ind = matched_ind[0]
                else:
                    raise PlatformException(error='400',
                                            message='more than one annotation with same object id: {}'.format(
                                                object_id))

                self.annotations[matched_ind].add_frames(annotation_definition=single_definition,
                                                         frame_num=frame_num,
                                                         end_frame_num=end_frame_num,
                                                         start_time=start_time,
                                                         end_time=end_time,
                                                         fixed=fixed,
                                                         object_visible=object_visible)
            else:
                # add new annotation to list
                self.annotations.append(annotation)

    ############
    # Plotting #
    ############
    def show(self,
             image=None,
             thickness=None,
             with_text=False,
             height=None,
             width=None,
             annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
             label_instance_dict=None,
             color=None,
             alpha=1,
             frame_num=None):
        """
        Show annotations according to annotation_format

        **Prerequisites**: Any user can upload annotations.

        :param ndarray image: empty or image to draw on
        :param int height: height
        :param int width: width
        :param int thickness: line thickness
        :param bool with_text: add label to annotation
        :param dl.ViewAnnotationOptions annotation_format: how to show thw annotations. options: list(dl.ViewAnnotationOptions)
        :param dict label_instance_dict: instance label map {'Label': 1, 'More': 2}
        :param tuple color: optional - color tuple
        :param float alpha: opacity value [0 1], default 1
        :param int frame_num: for video annotation, show specific frame
        :return: ndarray of the annotations

        **Example**:

        .. code-block:: python

            image = builder.show(image='ndarray',
                        thickness=1,
                        annotation_format=dl.VIEW_ANNOTATION_OPTIONS_MASK,
                        )
        """
        # if 'video' in self.item.mimetype and (annotation_format != 'json' or annotation_format != ['json']):
        #     raise PlatformException('400', 'Cannot show mask or instance of video item')
        # height/weight
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        # split the annotations to binary and not binary to put the binaries first
        segment_annotations = list()
        rest_annotations = list()
        for annotation in self.annotations:
            if annotation.type == 'binary':
                segment_annotations.append(annotation)
            else:
                rest_annotations.append(annotation)
        all_annotations = segment_annotations + rest_annotations
        # gor over all annotations and put the id where the annotations is
        for annotation in all_annotations:
            # get the mask of the annotation
            image = annotation.show(thickness=thickness,
                                    with_text=with_text,
                                    height=height,
                                    width=width,
                                    label_instance_dict=label_instance_dict,
                                    annotation_format=annotation_format,
                                    image=image,
                                    alpha=alpha,
                                    color=color,
                                    frame_num=frame_num)
        return image

    def _video_maker(self,
                     input_filepath,
                     output_filepath,
                     thickness=1,
                     annotation_format=entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE,
                     with_text=False,
                     alpha=1):
        """
        create a video from frames

        :param input_filepath: str - input file path
        :param output_filepath: str - out put file path
        :param thickness: int - thickness of the annotations
        :param annotation_format: str - ViewAnnotationOptions - annotations format
        :param with_text: bool - if True show the label in the output
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        is_color = True
        if annotation_format in [entities.ViewAnnotationOptions.INSTANCE,
                                 entities.ViewAnnotationOptions.OBJECT_ID]:
            is_color = False
        # read input video
        fps = self.item.system.get('fps', 0)
        height = self.item.system.get('height', 0)
        width = self.item.system.get('width', 0)
        nb_frames = int(self.item.system.get('ffmpeg', {}).get('nb_read_frames'))
        writer = cv2.VideoWriter(filename=output_filepath,
                                 fourcc=cv2.VideoWriter_fourcc(*"mp4v"),
                                 fps=fps,
                                 frameSize=(width, height),
                                 isColor=is_color)
        if input_filepath is not None and is_color:
            reader = cv2.VideoCapture(input_filepath)
        else:
            reader = None

        for frame_num in range(nb_frames):
            if reader is not None:
                ret, frame = reader.read()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            else:
                frame = None
            frame = self.show(image=frame,
                              annotation_format=annotation_format,
                              thickness=thickness,
                              alpha=alpha,
                              height=height,
                              width=width,
                              with_text=with_text,
                              frame_num=frame_num)
            if is_color:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            writer.write(frame)
        writer.release()
        if reader is not None:
            reader.release()

    def _set_flip_args(self, orientation):
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. that make the exif orientation not supported')
            raise
        if orientation == 3:
            return cv2.ROTATE_180, cv2.ROTATE_180, 0
        elif orientation == 4:
            return cv2.ROTATE_180, cv2.ROTATE_180, 1
        elif orientation == 5:
            return cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, 1
        elif orientation == 6:
            return cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, 0
        elif orientation == 7:
            return cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_90_CLOCKWISE, 1
        else:
            return cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_90_CLOCKWISE, 0

    def download(self,
                 filepath,
                 img_filepath=None,
                 annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.JSON,
                 height=None,
                 width=None,
                 thickness=1,
                 with_text=False,
                 orientation=0,
                 alpha=1):
        """
        Save annotations to file

        **Prerequisites**: Any user can upload annotations.

        :param str filepath: path to save annotation
        :param str img_filepath: img file path - needed for img_mask
        :param dl.ViewAnnotationOptions annotation_format: how to show thw annotations. options: list(dl.ViewAnnotationOptions)
        :param int height: height
        :param int width: width
        :param int thickness: thickness
        :param bool with_text: add a text to the image
        :param int orientation: the image orientation
        :param float alpha: opacity value [0 1], default 1
        :return: file path of the downlaod annotation
        :rtype: str

        **Example**:

        .. code-block:: python

            filepath = builder.download(filepath='filepath', annotation_format=dl.ViewAnnotationOptions.MASK)
        """
        dir_name, ex = os.path.splitext(filepath)
        if annotation_format == entities.ViewAnnotationOptions.JSON:
            if not ex:
                filepath = os.path.join(dir_name, '{}.json'.format(os.path.splitext(self.item.name)[0]))
            _json = dict()
            if self.item is not None:
                _json = {'_id': self.item.id,
                         'filename': self.item.filename}
            annotations = list()
            for ann in self.annotations:
                annotations.append(ann.to_json())
            _json['annotations'] = annotations
            if self.item is not None:
                _json['metadata'] = self.item.metadata
            with open(filepath, 'w+') as f:
                json.dump(_json, f, indent=2)
        elif annotation_format in [entities.ViewAnnotationOptions.MASK,
                                   entities.ViewAnnotationOptions.INSTANCE,
                                   entities.ViewAnnotationOptions.OBJECT_ID,
                                   entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE]:
            if not ex:
                if 'video' in self.item.mimetype:
                    filepath = os.path.join(dir_name, '{}.mp4'.format(os.path.splitext(self.item.name)[0]))
                else:
                    filepath = os.path.join(dir_name, '{}.png'.format(os.path.splitext(self.item.name)[0]))
            image = None
            if 'video' in self.item.mimetype:
                if annotation_format == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE:
                    if img_filepath is None:
                        img_filepath = self.item.download()
                    annotation_format = entities.ViewAnnotationOptions.MASK
                self._video_maker(input_filepath=img_filepath,
                                  output_filepath=filepath,
                                  thickness=thickness,
                                  annotation_format=annotation_format,
                                  with_text=with_text,
                                  alpha=alpha
                                  )
                return filepath
            if annotation_format == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE:
                if img_filepath is None:
                    img_filepath = self.item.download()
                annotation_format = entities.ViewAnnotationOptions.MASK
                image = np.asarray(Image.open(img_filepath))
            if orientation in [3, 4, 5, 6, 7, 8]:
                try:
                    import cv2
                except (ImportError, ModuleNotFoundError):
                    logger.error(
                        'Import Error! Cant import cv2. that make the exif orientation not supported')
                    raise
                first_rotate, second_rotate, flip = self._set_flip_args(orientation=orientation)
                image = cv2.rotate(image, first_rotate)
                if flip:
                    image = np.flip(image, 1)
            mask = self.show(image=image,
                             thickness=thickness,
                             with_text=with_text,
                             height=height,
                             width=width,
                             alpha=alpha,
                             annotation_format=annotation_format)
            if orientation not in [3, 4, 5, 6, 7, 8]:
                img = Image.fromarray(mask.astype(np.uint8))
            else:
                img = Image.fromarray(cv2.rotate(mask.astype(np.uint8), second_rotate))
            img.save(filepath)
        elif annotation_format == entities.ViewAnnotationOptions.VTT:
            if not ex:
                filepath = '{}/{}.vtt'.format(dir_name, os.path.splitext(self.item.name)[0])
            annotations_dict = [{'start_time': annotation.start_time,
                                 'end_time': annotation.end_time,
                                 'text': annotation.coordinates['text']} for annotation in self.annotations if
                                annotation.type in ['subtitle']]
            sorted_by_start_time = sorted(annotations_dict, key=lambda i: i['start_time'])
            vtt = webvtt.WebVTT()
            for ann in sorted_by_start_time:
                s = str(datetime.timedelta(seconds=ann['start_time']))
                if len(s.split('.')) == 1:
                    s += '.000'
                e = str(datetime.timedelta(seconds=ann['end_time']))
                if len(e.split('.')) == 1:
                    e += '.000'
                caption = webvtt.Caption(
                    '{}'.format(s),
                    '{}'.format(e),
                    '{}'.format(ann['text'])
                )
                vtt.captions.append(caption)
            vtt.save(filepath)
        else:
            raise PlatformException(error="400", message="Unknown annotation option: {}".format(annotation_format))
        return filepath

    ############
    # Platform #
    ############
    def update(self, system_metadata=True):
        """
        Update an existing annotation in host.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param system_metadata: True, if you want to change metadata system
        :return: Annotation object
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = builder.update()
        """
        if self.item is None:
            raise PlatformException('400', 'missing item to perform platform update')
        return self.item.annotations.update(annotations=self.annotations, system_metadata=system_metadata)

    def delete(self):
        """
        Remove an annotation from item

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = builder.delete()
        """
        if self.item is None:
            raise PlatformException('400', 'missing item to perform platform delete')
        return [self.item.annotations.delete(annotation_id=annotation.id) for annotation in self.annotations]

    def upload(self):
        """
        Create a new annotation in host

        **Prerequisites**: Any user can upload annotations.

        :return: Annotation entity
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = builder.upload()
        """
        if self.item is None:
            raise PlatformException('400', 'missing item to perform platform upload')
        return self.item.annotations.upload(self.annotations)

    @staticmethod
    def _json_to_annotation(item: entities.Item, w_json: dict, is_video=None, fps=25, item_metadata=None,
                            client_api=None):
        try:
            annotation = entities.Annotation.from_json(_json=w_json,
                                                       fps=fps,
                                                       item_metadata=item_metadata,
                                                       is_video=is_video,
                                                       item=item,
                                                       client_api=client_api)
            status = True
        except Exception:
            annotation = traceback.format_exc()
            status = False
        return status, annotation

    @classmethod
    def from_json(cls, _json: list, item=None, is_video=None, fps=25, height=None, width=None,
                  client_api=None, is_audio=None):
        """
        Create an annotation collection object from platform json

        :param dict _json: platform json
        :param dtlpy.entities.item.Item item: item
        :param client_api: ApiClient entity
        :param bool is_video: is video
        :param fps: video fps
        :param float height: height
        :param float width: width
        :param bool is_audio: is audio
        :return: annotation object
        :rtype: dtlpy.entities.annotation.Annotation
        """
        if item is None:
            if isinstance(_json, dict):
                metadata = _json.get('metadata', dict())
                system_metadata = metadata.get('system', dict())
                if is_video is None:
                    if 'mimetype' in system_metadata:
                        is_video = 'video' in system_metadata['mimetype']
                        is_audio = 'audio' in system_metadata['mimetype']
                    elif 'filename' in _json:
                        ext = os.path.splitext(_json['filename'])[-1]
                        try:
                            is_video = 'video' in mimetypes.types_map[ext.lower()]
                            is_audio = 'is_audio' in mimetypes.types_map[ext.lower()]
                        except Exception:
                            logger.info("Unknown annotation's item type. Default item type is set to: image")
                    else:
                        logger.info("Unknown annotation's item type. Default item type is set to: image")
                if is_video:
                    fps = system_metadata.get('fps', fps)
                    ffmpeg_info = system_metadata.get('ffmpeg', dict())
                    height = ffmpeg_info.get('height', None)
                    width = ffmpeg_info.get('width', None)
                elif is_audio:
                    fps = system_metadata.get('fps', 1000)
                    height = system_metadata.get('height', None)
                    width = system_metadata.get('width', None)
                else:
                    fps = 0
                    height = system_metadata.get('height', None)
                    width = system_metadata.get('width', None)
        else:
            if client_api is None:
                client_api = item._client_api
            fps = item.fps
            height = item.height
            width = item.width

        item_metadata = {
            'fps': fps,
            'height': height,
            'width': width
        }

        if 'annotations' in _json:
            _json = _json['annotations']

        results = list([None for _ in range(len(_json))])
        for i_json, single_json in enumerate(_json):
            results[i_json] = cls._json_to_annotation(item=item,
                                                      fps=fps,
                                                      item_metadata=item_metadata,
                                                      is_video=is_video,
                                                      w_json=single_json,
                                                      client_api=client_api)
        # log errors
        _ = [logger.warning(j[1]) for j in results if j[0] is False]

        # return good jobs
        annotations = [j[1] for j in results if j[0] is True]

        # sort
        if is_video:
            annotations.sort(key=lambda x: x.start_frame)
        else:
            annotations.sort(key=lambda x: x.label)

        return cls(annotations=miscellaneous.List(annotations), item=item)

    @classmethod
    def from_json_file(cls, filepath, item=None):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_json(_json=data, item=item)

    def from_vtt_file(self, filepath):
        """
        convert annotation from vtt format

        :param str filepath: path to the file
        """
        for caption in webvtt.read(filepath):
            h, m, s = caption.start.split(':')
            start_time = datetime.timedelta(hours=float(h), minutes=float(m), seconds=float(s)).total_seconds()
            h, m, s = caption.end.split(':')
            end_time = datetime.timedelta(hours=float(h), minutes=float(m), seconds=float(s)).total_seconds()
            if self.item.fps is not None:
                start_frame = round(start_time * self.item.fps)
            else:
                raise ValueError('Item do not have fps, please wait for video-preprocess to complete')
            annotation_definition = entities.Subtitle(text=caption.text, label='Text')
            annotation = entities.Annotation.new(
                annotation_definition=annotation_definition,
                frame_num=start_frame,
                item=self.item,
                start_time=start_time)

            annotation.add_frames(annotation_definition=annotation_definition,
                                  frame_num=start_frame, end_time=end_time)

            self.annotations.append(annotation)

    def from_instance_mask(self, mask, instance_map=None):
        """
        convert annotation from instance mask format

        :param mask: the mask annotation
        :param instance_map: labels
        """
        if instance_map is None:
            instance_map = self.item.dataset.instance_map
        # go over all instance ids
        for label, instance_id in instance_map.items():
            # find a binary mask per instance
            class_mask = instance_id == mask
            if not np.any(class_mask):
                continue
            # add the binary mask to the annotation builder
            self.add(annotation_definition=entities.Segmentation(geo=class_mask, label=label))

    def to_json(self):
        """
        Convert annotation object to a platform json representation

        :return: platform json
        :rtype: dict
        """
        if self.item is None:
            item_id = None
            item_name = None
        else:
            item_id = self.item.id
            item_name = self.item.filename

        _json = {
            "_id": item_id,
            "filename": item_name,
            'annotations': [annotation.to_json() for annotation in self.annotations]
        }

        return _json

    def print(self, to_return=False, columns=None):
        """

        :param to_return:
        :param columns:
        """
        return miscellaneous.List(self.annotations).print(to_return=to_return, columns=columns)

    #########################
    # For video annotations #
    #########################
    def get_frame(self, frame_num):
        """
        Get frame

        :param int frame_num: frame num
        :return: AnnotationCollection
        """
        frame_collection = AnnotationCollection(item=self.item)
        for annotation in self.annotations:
            if frame_num in annotation.frames:
                annotation.set_frame(frame=frame_num)
                frame_collection.annotations.append(annotation)
        return frame_collection

    def video_player(self):
        from ..utilities.videos.video_player import VideoPlayer
        _ = VideoPlayer(dataset_id=self.item.dataset.id,
                        item_id=self.item.id)
