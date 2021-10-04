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

logger = logging.getLogger(name=__name__)


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
            if isinstance(single_definition.description, str):
                if metadata is None:
                    metadata = dict()
                if 'system' not in metadata:
                    metadata['system'] = dict()
                metadata['system']['description'] = single_definition.description

            annotation = entities.Annotation.new(item=self.item,
                                                 annotation_definition=single_definition,
                                                 frame_num=frame_num,
                                                 automated=automated,
                                                 metadata=metadata,
                                                 object_id=object_id,
                                                 parent_id=parent_id)
            #  add frame if exists
            if frame_num is not None or start_time is not None:
                if object_id is None:
                    raise ValueError('Video Annotation must have object_id. '
                                     'for more information visit: https://dataloop.ai/docs/sdk-create-video-annotation#create-video-annotation')
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
    def show(self, image=None, thickness=None, with_text=False, height=None, width=None,
             annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
             label_instance_dict=None, color=None):
        """
            Show annotations according to annotation_format

        :param image: empty or image to draw on
        :param height: height
        :param width: width
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param annotation_format: how to show thw annotations. options: list(dl.ViewAnnotationOptions)
        :param label_instance_dict: instance label map {'Label': 1, 'More': 2}
        :param color: optional - color tuple
        :return: ndarray of the annotations
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
        # gor over all annotations and put the id where the annotations is
        for annotation in self.annotations:
            # get the mask of the annotation
            image = annotation.show(thickness=thickness,
                                    with_text=with_text,
                                    height=height,
                                    width=width,
                                    label_instance_dict=label_instance_dict,
                                    annotation_format=annotation_format,
                                    image=image,
                                    color=color)

        return image

    def _video_maker(self, input_filepath, output_filepath, thickness=1):
        """
        create a video from frames
        :param input_filepath:
        :param output_filepath:
        :param thickness:
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise
        # read input video
        try:
            reader = cv2.VideoCapture(input_filepath)
            width = int(reader.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = reader.get(cv2.CAP_PROP_FPS)
            writer = cv2.VideoWriter(output_filepath, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            frames = list()
            while reader.isOpened():
                ret, frame = reader.read()
                if not ret:
                    break
                frames.append(frame)
            for annotation in self.annotations:
                frames = annotation.show(image=frames, color=annotation.color,
                                         annotation_format=entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE,
                                         thickness=thickness,
                                         height=height,
                                         width=width)
            for ann_frame in frames:
                writer.write(ann_frame.astype(np.uint8))
            reader.release()
            writer.release()
        except Exception as e:
            raise ValueError(e)

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

    def download(self, filepath, img_filepath=None,
                 annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
                 height=None,
                 width=None, thickness=1,
                 with_text=False,
                 orientation=0):
        """
            Save annotations to file

        :param filepath: path to save annotation
        :param img_filepath: img file path - needed for img_mask
        :param annotation_format: how to show thw annotations. options: list(dl.ViewAnnotationOptions)
        :param height: height
        :param width: width
        :param thickness: thickness
        :param with_text: add a text to the image
        :param orientation: the image orientation
        :return:
        """
        dir_name, ex = os.path.splitext(filepath)
        if annotation_format == entities.ViewAnnotationOptions.JSON:
            if not ex:
                filepath = '{}/{}.json'.format(dir_name, os.path.splitext(self.item.name)[0])
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
                filepath = '{}/{}.png'.format(dir_name, os.path.splitext(self.item.name)[0])
            image = None
            if annotation_format == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE:
                if 'video' in self.item.mimetype:
                    self._video_maker(input_filepath=img_filepath, output_filepath=filepath,
                                      thickness=thickness,
                                      )
                    return filepath
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
        if self.item is None:
            raise PlatformException('400', 'missing item to perform platform update')
        return self.item.annotations.update(annotations=self.annotations, system_metadata=system_metadata)

    def delete(self):
        if self.item is None:
            raise PlatformException('400', 'missing item to perform platform delete')
        return [self.item.annotations.delete(annotation_id=annotation.id) for annotation in self.annotations]

    def upload(self):
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

        results = [None for _ in range(len(_json))]
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

        return cls(annotations=annotations, item=item)

    @classmethod
    def from_json_file(cls, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_json(data)

    def from_vtt_file(self, filepath):
        """
            convert annotation from vtt format
            :param filepath: path to the file
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
        :param frame_num:
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
