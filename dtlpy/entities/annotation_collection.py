from multiprocessing.pool import ThreadPool
from PIL import Image
import numpy as np
import traceback
import logging
import attr
import json

from .. import utilities, entities, PlatformException

logger = logging.getLogger(name=__name__)


@attr.s
class AnnotationCollection:
    """
        Collection of Annotation entity
    """
    item = attr.ib()
    annotations = attr.ib()

    @annotations.default
    def set_annotations(self):
        return list()

    def __iter__(self):
        for annotation in self.annotations:
            yield annotation

    def __getitem__(self, index):
        return self.annotations[index]

    def __len__(self):
        return len(self.annotations)

    def add(self, annotation_definition, object_id=None, frame_num=0, automated=True, fixed=True, metadata=None):
        """
        Add annotations to collection

        :param annotation_definition: dl.Polygon, dl.Segmentation, dl.Point, dl.Box etc
        :param object_id: Id of the annotation. If video - must input to match annotations between frames
        :param frame_num: video only, number of frame
        :param fixed: video only, mark frame as fixed
        :param automated:
        :param metadata: optional- metadata dictionary for annotation
        :return:
        """
        if object_id is None:
            # add new annotation to list
            annotation = entities.Annotation.new(item=self.item,
                                                 annotation_definition=annotation_definition,
                                                 automated=automated,
                                                 metadata=metadata)
            self.annotations.append(annotation)
        else:
            # find matching element_id
            matched_ind = [i_annotation
                           for i_annotation, annotation in enumerate(self.annotations)
                           if annotation.object_id == object_id]
            if len(matched_ind) == 0:
                # no matching object id found - create new one
                annotation = entities.Annotation.new(item=self.item,
                                                     annotation_definition=annotation_definition,
                                                     automated=automated,
                                                     metadata=metadata,
                                                     object_id=object_id)
                self.annotations.append(annotation)
            elif len(matched_ind) == 1:
                # found matching object id - add annotation to it
                self.annotations[matched_ind[0]].add_frame(annotation_definition=annotation_definition,
                                                           frame_num=frame_num,
                                                           fixed=fixed)
            else:
                raise PlatformException('400',
                                        'more than one annotation with same object id: {}'.format(object_id))

    ############
    # Plotting #
    ############
    def show(self, image=None, thickness=None, with_text=False, height=None, width=None, annotation_format='mask'):
        """
            Show annotations according to annotation_format

        :param image: empty or image to draw on
        :param height: height
        :param width: width
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param annotation_format: how to show thw annotations. options: 'mask'/'instance'
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

        label_instance_dict = None
        if annotation_format == 'mask':
            # create an empty mask
            if image is None:
                mask = np.zeros((height, width, 4))
            else:
                if len(image.shape) == 2:
                    # image is gray
                    mask = cv2.cvtColor(image, cv2.COLOR_GRAY2RGBA)
                elif image.shape[2] == 3:
                    mask = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
                else:
                    raise PlatformException('400', 'Unknown image type')
        elif annotation_format == 'instance':
            if image is None:
                # create an empty mask
                mask = np.zeros((height, width))
            else:
                if len(image.shape) != 2:
                    raise PlatformException('400', 'must be 2d array when trying to draw instance on image')
                mask = image
            # create a dictionary of labels and ids
            labels = [label.tag for label in self.item.dataset.labels]
            labels.sort()
            # each label gets index as instance id
            label_instance_dict = {label: (i_label + 1) for i_label, label in enumerate(labels)}
        elif annotation_format == 'object_id':
            if image is None:
                # create an empty mask
                mask = np.zeros((height, width))
            else:
                if len(image.shape) != 2:
                    raise PlatformException('400', 'must be 2d array when trying to draw instance on image')
                mask = image
        else:
            raise PlatformException('404', 'unknown annotations format: "{}". known formats: "mask", "instance"'.format(
                annotation_format))

        #############
        # gor over all annotations and put the id where the annotations is
        for annotation in self.annotations:
            if annotation_format == 'mask':
                color = None
            elif annotation_format == 'instance':
                # if label not in dataset label - put it as background
                color = label_instance_dict.get(annotation.label, 0)
            elif annotation_format == 'object_id':
                color = annotation.object_id
            else:
                raise PlatformException('404',
                                        'unknown annotations format: {}. known formats: "mask", "instance"'.format(
                                            annotation_format))
            # get the mask of the annotation
            mask = annotation.show(thickness=thickness,
                                   color=color,
                                   with_text=with_text,
                                   height=height,
                                   width=width,
                                   annotation_format=annotation_format,
                                   image=mask)

        return mask

    def download(self, filepath, annotation_format='mask', height=None, width=None, thickness=1, with_text=False):
        """
            Save annotations to file

        :param filepath:
        :param annotation_format:
        :param height:
        :param width:
        :param thickness:
        :param with_text:
        :return:
        """
        if annotation_format == 'json':
            _json = {'_id': self.item.id,
                     'filename': self.item.filename}
            annotations = list()
            for ann in self.annotations:
                annotations.append(ann.to_json())
            _json['annotations'] = annotations
            with open(filepath, 'w') as f:
                json.dump(_json, f)
        else:
            mask = self.show(thickness=thickness,
                             with_text=with_text,
                             height=height,
                             width=width,
                             annotation_format=annotation_format)
            img = Image.fromarray(mask.astype(np.uint8))
            img.save(filepath)
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

    @classmethod
    def from_json(cls, _json, item=None):

        def json_to_annotation(w_i_json, w_json):
            try:
                # ignore notes
                if w_json['type'] == 'note':
                    annotations[w_i_json] = 'note'
                    success[w_i_json] = False
                else:
                    annotations[w_i_json] = entities.Annotation.from_json(_json=w_json,
                                                                          item=item)
                    success[w_i_json] = True
            except Exception:
                logger.warning('{}\nFailed to load annotation. id: {}, item_id:{}'.format(traceback.format_exc(),
                                                                                          w_json['id'],
                                                                                          w_json['itemId']))
                success[w_i_json] = False

        pool = ThreadPool(processes=32)
        success = [False for _ in range(len(_json))]
        annotations = [False for _ in range(len(_json))]
        for i_json, single_json in enumerate(_json):
            pool.apply_async(func=json_to_annotation, kwds={"w_json": single_json,
                                                            "w_i_json": i_json})
        pool.close()
        pool.join()
        pool.terminate()
        annotations = [annotation for i_annotation, annotation in enumerate(annotations) if success[i_annotation]]
        annotations.sort(key=lambda x: x.label)
        return cls(annotations=annotations, item=item)

    def print(self):
        utilities.List([self.annotations]).print()

    def to_json(self):
        return [annotation.to_json() for annotation in self.annotations]

    #########################
    # For video annotations #
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
        a = VideoPlayer(dataset_id=self.item.dataset.id,
                        item_id=self.item.id)
