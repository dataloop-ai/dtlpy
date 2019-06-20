"""

"""
import logging
import base64
import json
import io
import cv2
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger('dataloop.annotations')


class BaseAnnotation:
    """
     Base annotations object for image and video annotations
    """

    @staticmethod
    def create_coordinates(pts, annotation_type, color, img_shape):
        """
        Create annotations from input params

        :param pts: box, polygon or mask annotation
        :param annotation_type:
        :param color:
        :param img_shape:
        :return:
        """
        if annotation_type == 'box':
            if len(pts) == 4:
                left, top, right, bottom = pts
                coordinates = [{'x': left, 'y': top}, {'x': right, 'y': bottom}]
            elif len(pts) == 2 and isinstance(pts[0], dict):
                # input pts is a 2 point dict with 'x', 'y'
                coordinates = pts
            else:
                raise ValueError('"box" annotations must have len 2 dictionary or len 4 list. got: %d' % len(pts))

        elif annotation_type == 'segment':
            coordinates = list()
            for pt in pts:
                x, y = np.squeeze(pt)
                coordinates.append({'y': int(y), 'x': int(x)})
            coordinates = [coordinates]

        elif annotation_type == 'polyline':
            coordinates = list()
            for pt in pts:
                x, y = np.squeeze(pt)
                coordinates.append({'y': int(y), 'x': int(x)})

        elif annotation_type == 'binary':
            if color is None:
                color = np.random.randint(0, 255, 3)
            png_ann = np.stack((color[0] * pts,
                                color[1] * pts,
                                color[2] * pts), axis=2).astype(np.uint8)
            if 255 in np.unique(pts[..., np.newaxis]):
                factor = 1
            else:
                factor = 255
            png_ann = np.concatenate((png_ann, (factor * pts[..., np.newaxis]).astype(np.uint8)), axis=2)
            pil_img = Image.fromarray(png_ann)
            if img_shape is not None:
                pil_img = pil_img.resize(img_shape[::-1])
            buff = io.BytesIO()
            pil_img.save(buff, format="PNG")
            new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
            coordinates = 'data:image/png;base64,%s' % new_image_string
        elif annotation_type == 'point':
            coordinates = {'x': pts[0], 'y': pts[1]}
        else:
            logger.exception('annotation type note supported yet. type: %s' % annotation_type)
            raise ValueError('annotation type note supported yet. type: %s' % annotation_type)
        return coordinates

    @staticmethod
    def segment_to_binary(pts, img_shape=None):
        """
        Switch from polygon points to mask annotation

        :param pts:
        :param img_shape:
        :return:
        """
        assert img_shape is not None, '[ERROR] must input img_shape when switching from polygon to mask'
        new_pts = np.zeros(img_shape)
        new_pts = cv2.drawContours(new_pts, np.array(pts).astype(int), 0, 255, -1)
        return new_pts

    @staticmethod
    def binary_to_segment(pts, img_shape=None, epsilon=None):
        """
        Switch from mask annotation to polygon
        :param pts:
        :param img_shape:
        :param epsilon:
        :return:
        """
        if img_shape is not None:
            pts = cv2.resize(pts.astype(np.uint8), img_shape[::-1])
        else:
            pts = pts.astype(np.uint8)
        # threshold the mask
        ret, thresh = cv2.threshold(pts, 0.5, 255, 0)
        # find contours
        im2, contours, hierarchy = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_TREE,
                                                    cv2.CHAIN_APPROX_NONE)
        if len(contours) == 0:
            # no contours were found
            return contours
        # calculate contours area
        areas = [cv2.contourArea(cnt) for cnt in contours]
        # take onr contour with maximum area
        filtered_indices = np.asarray(areas).argsort()[::-1][:1]
        filtered_contours = [contours[filtered_indices[i_cnt]] for i_cnt, b_cnt in
                             enumerate(filtered_indices)]
        # estimate contour to reduce number of points
        if epsilon is None:
            epsilon = 0.0005 * cv2.arcLength(filtered_contours[0], True)
        new_pts = cv2.approxPolyDP(filtered_contours[0], epsilon, True)
        return new_pts


class VideoAnnotation(BaseAnnotation):
    """
    Annotation object for video annotations
    """

    def __init__(self):
        self.logger = logging.getLogger('dataloop.annotation.video')
        self.annotations = list()

    def add_snapshot(self, element_id,
                     # annotations metadata
                     pts, second, frame_num, label, annotation_type='box', attributes=None, fixed=None,
                     metadata_system=None,
                     to_annotation_type=None, color=None, img_shape=None):
        """
        Add a new snapshot to element OR create a new element if not exist

        :param element_id:
        :param pts: for box: [x, y, x, y] - upper left point and lower bottom point
                    for polygon: list of list of points: [[x1,y1], [x2,y3], ...]
                    for binary: a 2D binary mask image same shape as the image
        :param second:
        :param label:
        :param annotation_type: 'box', 'segment' or 'binary'
        :param to_annotation_type:
        :param color:
        :param img_shape:

        :return:
        """
        found = False
        annotation_type = annotation_type.lower()
        ############################
        # create annotation's data #
        ############################
        if to_annotation_type is not None:
            # convert annotation types
            to_annotation_type = to_annotation_type.lower()
            if annotation_type == 'segment' and to_annotation_type == 'binary':
                # backward compatible
                if isinstance(pts[0][0], dict):
                    pts = [[[pt['x'], pt['y']] for pt in segs] for segs in pts]
                # convert pts
                pts = self.segment_to_binary(pts=pts, img_shape=img_shape)
                # assign new annotation type
                annotation_type = to_annotation_type
            elif annotation_type == 'binary' and to_annotation_type == 'segment':
                # convert pts
                pts = self.binary_to_segment(pts=pts, img_shape=img_shape)
                # assign new annotation type
                annotation_type = to_annotation_type
            elif annotation_type == 'binary' and to_annotation_type == 'binary':
                # do nothing
                pass
            elif annotation_type == 'segment' and to_annotation_type == 'segment':
                # do nothing
                pass
            else:
                self.logger.exception('Unknown conversion from: %s to:%s', annotation_type, to_annotation_type)
                raise ValueError('Unknown conversion from: %s to:%s' % (annotation_type, to_annotation_type))

        # create platform coordinates
        data = self.create_coordinates(pts=pts,
                                       annotation_type=annotation_type,
                                       color=color,
                                       img_shape=img_shape)
        if fixed is None:
            fixed = False
        if attributes is None:
            attributes = list()

        for annotation in self.annotations:
            if annotation['element_id'] == element_id:
                # update snapshot for specific annotation
                found = True
                # update snapshot for item
                current_snapshot = {
                    'frame': frame_num,
                    'fixed': fixed,
                    'attributes': attributes,
                    'type': annotation_type,
                    'label': label,
                    'startTime': second,
                    'data': data
                }
                annotation['metadata']['system']['snapshots_'].append(current_snapshot)
                # update main endTime
                annotation['metadata']['system']['endTime'] = np.maximum(annotation['metadata']['system']['endTime'],
                                                                         second)

        if not found:
            # add new annotation
            if metadata_system is None:
                metadata_system = dict()
            if not isinstance(metadata_system, dict):
                self.logger.exception(
                    '"metadata_system" must be a dictionary with extra metadata system info. igonring.')
                metadata_system = dict()
            new_annotation = {'label': label,
                              'type': annotation_type,
                              'attributes': attributes,
                              'coordinates': data,
                              'element_id': element_id,
                              'metadata': {'system': {'snapshots_': list(),
                                                      'startTime': second,
                                                      'endTime': second,
                                                      'status': 'tbd',
                                                      **metadata_system}
                                           }
                              }
            self.annotations.append(new_annotation)

    def to_platform(self):
        """
        Create json string for platform upload
        :return:
        """
        annotations_batch = list()
        for annotation in self.annotations:
            if '_id' in annotation:
                annotation.pop('_id', None)
            annotations_batch.append(json.dumps(annotation))
        return annotations_batch

    def from_file(self, filename):
        """
        Load annotations from file
        :param filename:
        :return:
        """
        with open(filename, 'r') as f:
            self.annotations = json.load(f)['annotations']

    def get_snapshot(self, element_id, second):
        """
        Get element snapshop by time
        :param element_id:
        :param second:
        :return:
        """
        matched_snapshot = None
        for annotation in self.annotations:
            if 'snapshots_' in annotation['metadata']:
                annotation = annotation['metadata']
            elif 'snapshots_' in annotation['metadata']['system']:
                annotation = annotation['metadata']['system']
            else:
                self.logger.exception('cant find snapshots in annotation')
                break
            # find annotation by element id
            if annotation['element_id'] == element_id:
                # find closest snapshot
                snapshots_time = np.array([snapshot['startTime'] for snapshot in annotation['snapshots_']])
                snap_id = np.argmin(np.abs(snapshots_time - second))
                matched_snapshot = annotation['snapshots_'][snap_id]
        if matched_snapshot is None:
            self.logger.exception('element was not found in annotations. element_id: {}'.format(element_id))
        return matched_snapshot

    # def get_snapshots_by_time(self, second):
    #     """
    #     Get all annotations in timestamp
    #     :param second:
    #     :return:
    #     """
    #     timestamp_snapshots = list()
    #     for head_annotation in self.annotations:
    #         if 'snapshots_' in head_annotation['metadata']:
    #             annotation = head_annotation['metadata']
    #         elif 'snapshots_' in head_annotation['metadata']['system']:
    #             annotation = head_annotation['metadata']['system']
    #         else:
    #             self.logger.exception('cant find snapshots in annotation')
    #             break
    #         # find annotation by element id
    #         if annotation['startTime'] <= second <= annotation['endTime']:
    #             # find closest snapshot
    #             if not annotation['snapshots_']:
    #                 continue
    #             # add first timestamp to snapshots list
    #             attributes = list()
    #             if 'attributes' in head_annotation:
    #                 attributes = head_annotation['attributes']
    #             snapshots = [{'data': head_annotation['coordinates'],
    #                           'frame': 0,
    #                           'type': head_annotation['type'],
    #                           'startTime': annotation['startTime'],
    #                           'fixed': True,
    #                           'attributes': attributes,
    #                           'label': head_annotation['label']}]
    #             # add all other snapshots
    #             snapshots += annotation['snapshots_']
    #             # get snapshots times
    #             snapshots_time = np.array([snapshot['startTime'] for snapshot in snapshots])
    #             # find closest
    #             timestamp_diff = snapshots_time - second
    #             positive_inds = [i for i, val in enumerate(timestamp_diff) if val >= 0]
    #             if not positive_inds:
    #                 continue
    #             snap_id = np.argmin(timestamp_diff[positive_inds])
    #             # get snapshot
    #             current_snapshot = snapshots[positive_inds[snap_id]]
    #             # current_snapshot['label'] = annotation['label']
    #             # add attribut if not exist
    #             if 'attributes' not in current_snapshot:
    #                 if 'attributes' in head_annotation:
    #                     current_snapshot['attributes'] = head_annotation['attributes']
    #                 else:
    #                     current_snapshot['attributes'] = list()
    #                     # add to timestamp's list
    #             timestamp_snapshots.append(current_snapshot)
    #     return timestamp_snapshots


class ImageAnnotation(BaseAnnotation):
    """
    Image Annotation Builder
    """

    def __init__(self):
        self.logger = logging.getLogger('dataloop.annotations.builder')
        self.annotations = list()

    def add_annotation(self, pts, label, annotation_type='box', object_id=None, attributes=None,
                       to_annotation_type=None, color=None, img_shape=None, metadata=None):
        """
        Add new annotation

        :param pts: for box: [x, y, x, y] - upper left point and lower bottom point \
        for polygon: list of list of points: [[x1,y1], [x2,y3], ...] \
        for binary: a 2D binary mask image same shape as the image
        :param label:
        :param annotation_type:
        :param to_annotation_type:
        :param color:
        :param img_shape:
        :return:
        """
        annotation_type = annotation_type.lower()

        if to_annotation_type is not None:
            # convert annotation types
            to_annotation_type = to_annotation_type.lower()
            if annotation_type == 'segment' and to_annotation_type == 'box':
                pts = np.asarray([[[pt['x'], pt['y']] for pt in segs] for segs in pts])
                top = np.min(pts[:, 1])
                left = np.min(pts[:, 0])
                bottom = np.max(pts[:, 1])
                right = np.max(pts[:, 0])
                pts = [left, top, right, bottom]
                annotation_type = to_annotation_type
            elif annotation_type == 'segment' and to_annotation_type == 'binary':
                # backward compatible
                if isinstance(pts[0][0], dict):
                    pts = [[[pt['x'], pt['y']] for pt in segs] for segs in pts]
                # convert pts
                pts = self.segment_to_binary(pts=pts, img_shape=img_shape)
                # assign new annotation type
                annotation_type = to_annotation_type
            elif annotation_type == 'binary' and to_annotation_type == 'segment':
                # convert pts
                pts = self.binary_to_segment(pts=pts, img_shape=img_shape)
                # assign new annotation type
                annotation_type = to_annotation_type
            elif annotation_type == 'binary' and to_annotation_type == 'binary':
                # do nothing
                pass
            elif annotation_type == 'segment' and to_annotation_type == 'segment':
                # do nothing
                pass
            else:
                raise ValueError('Unknown conversion from: %s to:%s' % (annotation_type, to_annotation_type))

        # create platform coordinates
        if annotation_type == 'class':
            coordinates = list()
        else:
            coordinates = self.create_coordinates(pts=pts,
                                                  annotation_type=annotation_type,
                                                  color=color,
                                                  img_shape=img_shape)
        # create annotation structure

        new_annotation = {'label': label,
                          'type': annotation_type,
                          'coordinates': coordinates,
                          }
        if attributes is not None:
            new_annotation['attributes'] = attributes
        if metadata is None:
            metadata = dict()
        if object_id is not None:
            if 'system' not in metadata:
                metadata['system'] = dict()
            metadata['system']['objectId'] = object_id
        new_annotation['metadata'] = metadata

        # append to list of annotations
        self.annotations.append(new_annotation)

    def from_file(self, filename):
        """
        Load annotations from json file
        :param filename:
        :return:
        """
        with open(filename, 'r') as f:
            self.annotations = json.load(f)['annotations']

    def to_image(self, img_shape, colors_dict, with_text=False, thickness=2):
        """
        Convert items annotations to a colored mask
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param width: image width
        :param height: image height
        :return: ndarray of the annotations
        """
        height, width = img_shape
        mask = np.zeros((width, height, 4))

        for annotation in self.annotations:
            label = annotation['label']
            color = (255, 0, 0)
            if label in colors_dict:
                color = colors_dict[label]
            random_color = *tuple(map(int, np.random.randint(0, 255, 3))), 255
            if annotation['type'] == 'binary':
                decode = base64.b64decode(annotation['coordinates'][22:])
                n_mask = np.array(Image.open(io.BytesIO(decode)))
                mask[np.where(n_mask[:, :, 3] > 127)] = [*color, 255]
            elif annotation['type'] == 'box':
                left, top, right, bottom = annotation['coordinates']
                cv2.rectangle(img=mask,
                              pt1=(left, top),
                              pt2=(right, bottom),
                              color=color, thickness=thickness, lineType=cv2.LINE_AA)
                top_x = np.min(pts[:, 0])
                top_y = np.min(pts[:, 1])
                if with_text:
                    cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                thickness=1)
            elif annotation['type'] == 'segment':
                # go over all segments in annotation
                for segment in annotation['coordinates']:
                    pts = np.asarray([[pt['x'], pt['y']] for pt in segment]).astype(int)
                    # draw polygon
                    cv2.drawContours(image=mask, contours=[pts], contourIdx=-1, color=random_color,
                                     thickness=thickness)
                    top_x = np.min(pts[:, 0])
                    top_y = np.min(pts[:, 1])
                    if with_text:
                        cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                    thickness=1)
            else:
                self.logger.exception('Unknown annotation type: %s', annotation['type'])
        return mask.astype(np.uint8)

    def to_platform(self):
        """
        Create json string for platform upload
        :return:
        """
        annotations_batch = list()
        for annotation in self.annotations:
            if '_id' in annotation:
                annotation.pop('_id', None)
            annotations_batch.append(json.dumps(annotation, indent=4, sort_keys=True))
        return annotations_batch
