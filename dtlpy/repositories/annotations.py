import io
import cv2
import json
import base64
import logging
import jwt
import numpy as np
from PIL import Image
import attr

from .. import entities, utilities, PlatformException


@attr.s
class Annotations:
    """
    Annotations repository
    """
    client_api = attr.ib()
    dataset = attr.ib()
    item = attr.ib()
    logger = attr.ib()

    @logger.default
    def set_logger(self):
        return logging.getLogger('dataloop.annotations')

    def get(self, annotation_id):
        """
        Get a single annotation
        :param annotation_id:
        :return: Annotation object or None
        """
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets/%s/items/%s/annotations/%s' %
                                                             (self.dataset.id, self.item.id, annotation_id))
        if success:
            annotation = entities.Annotation.from_json(_json=response.json(), dataset=self.dataset, item=self.item)
        else:
            raise PlatformException(response)
        return annotation

    def list(self):
        """
        Get all annotations
        :return: List of Annotation objects
        """

        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets/%s/items/%s/annotations' %
                                                             (self.dataset.id, self.item.id))
        annotations = utilities.List()
        if success:
            annotations = utilities.List(
                [entities.Annotation.from_json(_json=_json,
                                               dataset=self.dataset,
                                               item=self.item)
                 for _json in response.json()])
        return annotations

    def to_mask(self, img_shape, thickness=1, with_text=False, annotation=None):
        """
        Convert items annotations to a colored mask
        :param img_shape
        :param thickness: line thickness
        :param annotation:
        :param with_text: add label to annotation
        :return: ndarray of the annotations
        """

        height, width = img_shape
        mask = np.zeros((height, width, 4))
        if annotation is None:
            annotations = self.list()
        elif isinstance(annotation, list):
            annotations = annotation
        else:
            annotations = [annotation]
        if annotations is None:
            self.logger.debug('No annotations found for item. id: %s' % self.item.id)
            return mask
        colors = {label.tag: label.rgb() for label in self.dataset.labels}
        for annotation in annotations:
            try:
                label = annotation.label
                if label in colors:
                    color = colors[label]
                    color = (color[0], color[1], color[2], 255)
                else:
                    color = *tuple(map(int, np.random.randint(0, 255, 3))), 255
                if annotation.type == 'binary':
                    if isinstance(annotation.coordinates, dict):
                        coordinates = annotation.coordinates['data'][22:]
                    elif isinstance(annotation.coordinates, str):
                        coordinates = annotation.coordinates[22:]
                    else:
                        raise TypeError('Unknown annotation type in binary. type: %s' % type(annotation.coordinates))
                    decode = base64.b64decode(coordinates)
                    n_mask = np.array(Image.open(io.BytesIO(decode)))
                    mask[np.where(n_mask[:, :, 3] > 127)] = color
                elif annotation.type == 'box':
                    segment = annotation.coordinates
                    pts = np.asarray([[pt['x'], pt['y']] for pt in segment]).astype(int)
                    cv2.rectangle(img=mask,
                                  pt1=(np.min(pts[:, 0]), np.min(pts[:, 1])),
                                  pt2=(np.max(pts[:, 0]), np.max(pts[:, 1])),
                                  color=color, thickness=thickness, lineType=cv2.LINE_AA)
                    top_x = np.min(pts[:, 0])
                    top_y = np.min(pts[:, 1])
                    if with_text:
                        cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                    thickness=1)
                elif annotation.type == 'segment':
                    # go over all segments in annotation
                    for segment in annotation.coordinates:
                        pts = np.asarray([[pt['x'], pt['y']] for pt in segment]).astype(int)
                        # draw polygon
                        cv2.drawContours(image=mask, contours=[pts], contourIdx=-1, color=color,
                                         thickness=thickness)
                        top_x = np.min(pts[:, 0])
                        top_y = np.min(pts[:, 1])
                        if with_text:
                            cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                        fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                        thickness=1)
                elif annotation.type == 'polyline':
                    pts = np.asarray([[pt['x'], pt['y']] for pt in annotation.coordinates]).astype(int)
                    # draw polygon
                    cv2.polylines(img=mask, pts=[pts], color=color, isClosed=False, thickness=thickness)
                    top_x = np.min(pts[:, 0])
                    top_y = np.min(pts[:, 1])
                    if with_text:
                        cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                    thickness=1)
                elif annotation.type == 'class':
                    pass
                else:
                    self.logger.exception('Unknown annotation type: %s' % annotation.type)
                    raise TypeError('Unknown annotation type: %s' % annotation.type)
            except Exception as err:
                self.logger.exception('Unable to get annotation\'s mask. item_id: %s, annotation_id: %s' % (
                    annotation.item.id, annotation.id))
        return mask.astype(np.uint8)

    def to_instance(self, img_shape, thickness=1, annotation=None):
        """
                Convert items annotations to an instance mask (2d array with label index)
        :param thickness: line thickness
        :param img_shape:
        :param annotation:
        :return: mask
        """

        height, width = img_shape
        mask = np.zeros((height, width))
        if annotation is None:
            annotations = self.list()
        elif isinstance(annotation, list):
            annotations = annotation
        else:
            annotations = [annotation]
        # get labels
        labels = [label.tag.lower() for label in self.dataset.labels]
        labels.sort()
        # need to change color to a format that cv2 understands
        for annotation in annotations:
            if annotation.label.lower() not in labels:
                continue
            label_ind = labels.index(annotation.label.lower()) + 1  # to avoid instance id of 0
            if annotation.type == 'binary':
                if isinstance(annotation.coordinates, dict):
                    coordinates = annotation.coordinates['data'][22:]
                elif isinstance(annotation.coordinates, str):
                    coordinates = annotation.coordinates[22:]
                else:
                    raise TypeError('Unknown annotation type in binary. type: %s' % type(annotation.coordinates))
                decode = base64.b64decode(coordinates)
                n_mask = np.array(Image.open(io.BytesIO(decode)))
                mask[np.where(n_mask[:, :, 3] > 127)] = label_ind
            elif annotation.type == 'box':
                pts = np.asarray([[pt['x'], pt['y']] for pt in annotation.coordinates]).astype(int)
                cv2.rectangle(img=mask,
                              pt1=(np.min(pts[:, 0]), np.min(pts[:, 1])),
                              pt2=(np.max(pts[:, 0]), np.max(pts[:, 1])),
                              color=label_ind, thickness=thickness, lineType=cv2.LINE_AA)
            elif annotation.type == 'point':
                pts = np.asarray([[pt['x'], pt['y']] for pt in [annotation.coordinates]]).astype(int)
                cv2.circle(img=mask,
                           center=(np.min(pts[:, 0]), np.min(pts[:, 1])),
                           radius=10,
                           color=label_ind, thickness=thickness, lineType=cv2.LINE_AA)
            elif annotation.type == 'ellipse':
                self.logger.exception('Unhandled annotation type: %s' % annotation.type)
                # To Do
            elif annotation.type == 'segment':
                # go over all segments in annotation
                for segment in annotation.coordinates:
                    pts = np.asarray([[pt['x'], pt['y']] for pt in segment]).astype(int)
                    # draw polygon
                    cv2.drawContours(image=mask, contours=[pts], contourIdx=-1, color=label_ind,
                                     thickness=thickness)
            elif annotation.type == 'polyline':
                pts = np.asarray([[pt['x'], pt['y']] for pt in annotation.coordinates]).astype(int)
                # draw polygon
                cv2.polylines(img=mask, pts=[pts], color=label_ind, isClosed=False, thickness=thickness)
            else:
                self.logger.exception('Unknown annotation type: %s' % annotation.type)
                raise TypeError('Unknown annotation type: %s' % annotation.type)
        return mask.astype(np.uint8)

    def delete(self, annotation=None, annotation_id=None):
        """
        Remove an annotation from item
        :param annotation: Annotation object
        :param annotation_id: annotation id
        :return: True/False
        """

        if annotation_id is not None:
            pass
        elif annotation is not None and isinstance(annotation, entities.Annotation):
            annotation_id = annotation.id
        else:
            assert False
        # get creator from token
        creator = jwt.decode(self.client_api.token, algorithms=['HS256'], verify=False)['email']
        payload = {'username': creator}
        success, response = self.client_api.gen_request(req_type='delete',
                                                        path='/datasets/%s/items/%s/annotations/%s' %
                                                             (self.dataset.id, self.item.id, annotation_id),
                                                        json_req=payload)
        if not success:
            raise PlatformException(response)
        self.logger.info('Annotation %s deleted successfully')
        return True

    def download(self, filepath, get_mask=False, get_instance=False, img_shape=None, thickness=1, annotation=None):
        """
        Save annotation mask to file
        :param annotation:
        :param filepath:
        :param get_mask:
        :param get_instance:
        :param img_shape:
        :param thickness:
        :return: True
        """

        if get_mask:
            mask = self.to_mask(img_shape=img_shape, thickness=thickness, annotation=annotation)
            img = Image.fromarray(mask)
            img.save(filepath)
        if get_instance:
            mask = self.to_instance(img_shape=img_shape, thickness=thickness, annotation=annotation)
            img = Image.fromarray(mask)
            img.save(filepath)
        return True

    def update(self, annotations, annotations_ids=None, system_metadata=False):
        """
        Update an existing annotation.
        :param annotations:
        :param annotations_ids:
        :param system_metadata:
        :return: True
        """
        if not isinstance(annotations, list):
            annotations = [annotations]
        if annotations_ids is not None:
            if not isinstance(annotations_ids, list):
                annotations_ids = [annotations_ids]
        else:
            annotations_ids = [None for _ in range(len(annotations))]

        if len(annotations) != len(annotations_ids):
            raise PlatformException(
                error='400',
                message='Inputs must have same length. len(annotations)={annotations}, len(annotations_ids)={annotations_ids}'.format(annotations=len(annotations),
                                                                                                                                      annotations_ids=len(annotations_ids)))

        def update_single_annotation(i_annotation):
            try:
                annotation = annotations[i_annotation]
                annotation_id = annotations_ids[i_annotation]
                if isinstance(annotation, str):
                    annotation = json.loads(annotation)
                elif isinstance(annotation, entities.Annotation):
                    annotation_id = annotation_id or annotation.id
                    annotation = annotation.to_json()
                else:
                    self.logger.exception('Unknown annotation type: %s' % type(annotation))
                    raise ValueError('Unknown annotation type: %s' % type(annotation))

                if annotation_id is None:
                    self.logger.exception('missing argument: annotation_id')
                    raise ValueError('missing argument: annotation_id')
                url_path = '/datasets/%s/items/%s/annotations/%s' % (self.dataset.id, self.item.id, annotation_id)
                if system_metadata:
                    url_path += '?system=true'
                suc, response = self.client_api.gen_request(req_type='put',
                                                            path=url_path,
                                                            json_req=annotation)
                if suc:
                    success[i_annotation] = True
                else:
                    raise PlatformException(response)

            except Exception as e:
                success[i_annotation] = False
                errors[i_annotation] = e

        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(processes=32)
        num_annotations = len(annotations)
        success = [None for _ in range(num_annotations)]
        errors = [None for _ in range(num_annotations)]
        for i_ann in range(len(annotations)):
            pool.apply_async(func=update_single_annotation,
                             kwds={'i_annotation': i_ann})
        # log error
        pool.close()
        pool.join()
        dummy = [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        self.logger.debug('Annotation/s updated successfully')
        return True

    def upload(self, annotations):
        """
        Create a new annotation
        :param annotations: list or single annotation - dictionary or json string
        :return: list of annotation objects
        """

        if not isinstance(annotations, list):
            annotations = [annotations]

        def upload_single_annotation(i_w_annotation, w_annotation):
            try:
                suc, response = self.client_api.gen_request(req_type='post',
                                                            path='/datasets/%s/items/%s/annotations' %
                                                                 (self.dataset.id, self.item.id),
                                                            json_req=w_annotation)
                if suc:
                    annotations_created[i_w_annotation] = entities.Annotation.from_json(_json=response.json(),
                                                                                        dataset=self.dataset,
                                                                                        item=self.item)
                    success[i_w_annotation] = True
                else:
                    raise PlatformException(response)
            except Exception as e:
                success[i_w_annotation] = False
                errors[i_w_annotation] = e

        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(processes=32)
        num_annotations = len(annotations)
        success = [None for _ in range(num_annotations)]
        annotations_created = [None for _ in range(num_annotations)]
        errors = [None for _ in range(num_annotations)]
        for i_annotation, annotation in enumerate(annotations):
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            elif isinstance(annotation, entities.Annotation):
                annotation = annotation.to_json()
            elif isinstance(annotation, dict):
                pass
            else:
                self.logger.exception('unknown annotations type: %s' % type(annotation))
                success[i_annotation] = False
                errors[i_annotation] = 'unknown annotations type: %s' % type(annotation)
                continue
            pool.apply_async(func=upload_single_annotation,
                             kwds={'i_w_annotation': i_annotation, 'w_annotation': annotation})
        pool.close()
        pool.join()
        # log error
        dummy = [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        self.logger.debug('Annotation/s uploaded successfully')
        return annotations_created
