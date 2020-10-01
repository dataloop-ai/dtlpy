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
    item = attr.ib()
    annotations = attr.ib()  # type: miscellaneous.List[entities.Annotation]
    _dataset = attr.ib(repr=False, default=None)
    _colors = attr.ib(repr=False, default=None)

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.item.dataset
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def colors(self):
        if self._colors is None:
            self._colors = {key.lower(): label for key, label in self.dataset.labels_flat_dict.items()}
        return self._colors

    def get_color(self, label):
        if label in self.colors:
            return self.colors[label].rgb
        else:
            return (127, 127, 127)

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
        :param fixed: video only, mark frame as fixed
        :param parent_id: set a parent for this annotation (parent annotation ID)
        :param automated:
        :param metadata: optional- metadata dictionary for annotation
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
                                         'confidence': float(model_info['confidence'])}

        # to support list of definitions with same parameters
        if not isinstance(annotation_definition, list):
            annotation_definition = [annotation_definition]

        for single_definition in annotation_definition:
            if object_id is None:
                # add new annotation to list
                annotation = entities.Annotation.new(item=self.item,
                                                     annotation_definition=single_definition,
                                                     frame_num=frame_num,
                                                     automated=automated,
                                                     metadata=metadata,
                                                     parent_id=parent_id)
                self.annotations.append(annotation)
                matched_ind = len(self.annotations) - 1
            else:
                # find matching element_id
                matched_ind = [i_annotation
                               for i_annotation, annotation in enumerate(self.annotations)
                               if annotation.object_id == object_id]
                if len(matched_ind) == 0:
                    # no matching object id found - create new one
                    annotation = entities.Annotation.new(item=self.item,
                                                         annotation_definition=single_definition,
                                                         frame_num=frame_num,
                                                         automated=automated,
                                                         metadata=metadata,
                                                         object_id=object_id,
                                                         parent_id=parent_id)
                    self.annotations.append(annotation)
                    matched_ind = len(self.annotations) - 1
                elif len(matched_ind) == 1:
                    matched_ind = matched_ind[0]
                else:
                    raise PlatformException(error='400',
                                            message='more than one annotation with same object id: {}'.format(
                                                object_id))

            #  add frame if exists
            if frame_num is not None or start_time is not None:
                self.annotations[matched_ind].add_frames(annotation_definition=single_definition,
                                                         frame_num=frame_num,
                                                         end_frame_num=end_frame_num,
                                                         start_time=start_time,
                                                         end_time=end_time,
                                                         fixed=fixed)

    ############
    # Plotting #
    ############
    def show(self, image=None, thickness=None, with_text=False, height=None, width=None,
             annotation_format=entities.ViewAnnotationOptions.MASK,
             label_instance_dict=None):
        """
            Show annotations according to annotation_format

        :param image: empty or image to draw on
        :param height: height
        :param width: width
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param annotation_format: how to show thw annotations. options: dl.ViewAnnotationOptions.list()
        :param label_instance_dict: instance label map {'Label': 1, 'More': 2}
        :return: ndarray of the annotations
        """
        # if 'video' in self.item.mimetype and (annotation_format != 'json' or annotation_format != ['json']):
        #     raise PlatformException('400', 'Cannot show mask or instance of video item')
        # height/weight
        try:
            import cv2
        except ImportError:
            logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        if height is None:
            if self.item.height is None:
                raise PlatformException('400', 'Height must be provided')
            height = self.item.height
        if width is None:
            if self.item.width is None:
                raise PlatformException('400', 'Width must be provided')
            width = self.item.width

        if annotation_format == entities.ViewAnnotationOptions.MASK:
            # create an empty mask
            if image is None:
                mask = np.zeros((height, width, 4), dtype=np.uint8)
            else:
                if len(image.shape) == 2:
                    # image is gray
                    mask = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
                elif image.shape[2] == 3:
                    mask = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
                else:
                    raise PlatformException(error='1001',
                                            message='Unknown image shape. expected depth: gray or RGB. got: {}'.format(
                                                image.shape))
        elif annotation_format == entities.ViewAnnotationOptions.INSTANCE:
            if image is None:
                # create an empty mask
                mask = np.zeros((height, width), dtype=np.uint8)
            else:
                if len(image.shape) != 2:
                    raise PlatformException(error='1001',
                                            message='Image shape must be 2d array when trying to draw instance on image')
                mask = image
            # create a dictionary of labels and ids
            if label_instance_dict is None:
                label_instance_dict = self.item.dataset.instance_map
        elif annotation_format == entities.ViewAnnotationOptions.OBJECT_ID:
            if image is None:
                # create an empty mask
                mask = np.zeros((height, width), dtype=np.uint8)
            else:
                if len(image.shape) != 2:
                    raise PlatformException(error='1001',
                                            message='Image shape must be 2d array when trying to draw instance on image')
                mask = image
        else:
            raise PlatformException(error='1001',
                                    message='unknown annotations format: "{}". known formats: "{}"'.format(
                                        annotation_format, '", "'.join(entities.ViewAnnotationOptions.list())))

        #############
        # gor over all annotations and put the id where the annotations is
        for annotation in self.annotations:
            if annotation_format == entities.ViewAnnotationOptions.MASK:
                color = self.get_color(annotation.label.lower())
            elif annotation_format == entities.ViewAnnotationOptions.INSTANCE:
                # if label not in dataset label - put it as background
                color = label_instance_dict.get(annotation.label, 0)
            elif annotation_format == entities.ViewAnnotationOptions.OBJECT_ID:
                if annotation.object_id is None:
                    raise PlatformException(error='1001',
                                            message='Try to show object_id but annotation has no value. annotation id: {}'.format(
                                                annotation.id))
                color = annotation.object_id
            else:
                raise PlatformException('404',
                                        'unknown annotations format: {}. known formats: "{}"'.format(
                                            annotation_format, '", "'.join(entities.ViewAnnotationOptions.list())))
            # get the mask of the annotation
            mask = annotation.show(thickness=thickness,
                                   color=color,
                                   with_text=with_text,
                                   height=height,
                                   width=width,
                                   annotation_format=annotation_format,
                                   image=mask)

        return mask

    def download(self, filepath, img_filepath=None, annotation_format=entities.ViewAnnotationOptions.MASK, height=None,
                 width=None, thickness=1,
                 with_text=False):
        """
            Save annotations to file

        :param filepath: path to save annotation
        :param img_filepath: img file path - needed for img_mask
        :param annotation_format:
        :param height:
        :param width:
        :param thickness:
        :param with_text:
        :return:
        """
        dir_name, ex = os.path.splitext(filepath)

        if annotation_format == entities.ViewAnnotationOptions.JSON:
            if not ex:
                filepath = '{}/{}.json'.format(dir_name, os.path.splitext(self.item.name)[0])
            _json = {'_id': self.item.id,
                     'filename': self.item.filename}
            annotations = list()
            for ann in self.annotations:
                annotations.append(ann.to_json())
            _json['annotations'] = annotations
            with open(filepath, 'w+') as f:
                json.dump(_json, f, indent=2)
        elif annotation_format in [entities.ViewAnnotationOptions.MASK,
                                   entities.ViewAnnotationOptions.INSTANCE,
                                   entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE]:
            if not ex:
                filepath = '{}/{}.png'.format(dir_name, os.path.splitext(self.item.name)[0])
            image = None
            if annotation_format == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE:
                annotation_format = entities.ViewAnnotationOptions.MASK
                image = np.asarray(Image.open(img_filepath))
            mask = self.show(image=image,
                             thickness=thickness,
                             with_text=with_text,
                             height=height,
                             width=width,
                             annotation_format=annotation_format)
            img = Image.fromarray(mask.astype(np.uint8))
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
    def _json_to_annotation(item: entities.Item, w_json: dict, is_video=None, fps=25, item_metadata=None):
        try:
            annotation = entities.Annotation.from_json(_json=w_json,
                                                       fps=fps,
                                                       item_metadata=item_metadata,
                                                       is_video=is_video,
                                                       item=item)
            status = True
        except Exception:
            annotation = traceback.format_exc()
            status = False
        return status, annotation

    @classmethod
    def from_json(cls, _json: list, item=None, is_video=None, fps=25, height=None, width=None):
        if item is None:
            if isinstance(_json, dict):
                metadata = _json.get('metadata', dict())
                system_metadata = metadata.get('system', dict())
                if is_video is None:
                    if 'mimetype' in system_metadata:
                        is_video = 'video' in system_metadata['mimetype']
                    elif 'filename' in _json:
                        ext = os.path.splitext(_json['filename'])[-1]
                        try:
                            is_video = 'video' in mimetypes.types_map[ext.lower()]
                        except Exception:
                            logger.info("Unknown annotation's item type. Default item type is set to: image")
                    else:
                        logger.info("Unknown annotation's item type. Default item type is set to: image")
                if is_video:
                    fps = system_metadata.get('fps', fps)
                    ffmpeg_info = system_metadata.get('ffmpeg', dict())
                    height = ffmpeg_info.get('height', None)
                    width = ffmpeg_info.get('width', None)
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
                                                      w_json=single_json)
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

    def from_vtt_file(self, filepath):
        for caption in webvtt.read(filepath):
            h, m, s = caption.start.split(':')
            start_time = datetime.timedelta(hours=float(h), minutes=float(m), seconds=float(s)).total_seconds()
            h, m, s = caption.end.split(':')
            end_time = datetime.timedelta(hours=float(h), minutes=float(m), seconds=float(s)).total_seconds()

            start_frame = round(start_time * self.item.fps)
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
        return miscellaneous.List(self.annotations).print(to_return=to_return, columns=columns)

    #########################
    # For video annotations #
    #########################
    def get_frame(self, frame_num):
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
