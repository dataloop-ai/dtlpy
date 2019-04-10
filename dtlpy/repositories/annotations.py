import io
import cv2
import json
import base64
import logging
import jwt
import numpy as np
from PIL import Image

from .. import entities, services, utilities


class Annotations:
    """
    Annotations repository
    """

    def __init__(self, dataset, item):
        self.client_api = services.ApiClient()
        self.dataset = dataset
        self.item = item
        self.logger = logging.getLogger('dataloop.annotations')
        # self.image_annotation = ImageAnnotation()

    def get(self, annotation_id):
        """
        Get a single annotation
        :param annotation_id:
        :return: Annotation object or None
        """

        success = self.client_api.gen_request(req_type='get',
                                              path='/datasets/%s/items/%s/annotations/%s' % (
                                                  self.dataset.id, self.item.id, annotation_id))
        annotation = None
        if success:
            res = self.client_api.last_response.json()
            if not res:
                annotation = entities.Annotation(entity_dict=res[0], dataset=self.dataset, item=self.item)
        return annotation

    def list(self):
        """
        Get all annotations
        :return: List of Annotation objects
        """

        success = self.client_api.gen_request(req_type='get',
                                              path='/datasets/%s/items/%s/annotations' % (
                                                  self.dataset.id, self.item.id))
        annotations = utilities.List()
        if success:
            annotations = utilities.List(
                [entities.Annotation(entity_dict=entity_dict, dataset=self.dataset, item=self.item)
                 for entity_dict in self.client_api.last_response.json()])
        return annotations

    def to_mask(self, img_shape, thickness=1, with_text=False):
        """
        Convert items annotations to a colored mask
        :param img_shape
        :param thickness: line thickness
        :param with_text: add label to annotation
        :return: ndarray of the annotations
        """

        height, width = img_shape
        mask = np.zeros((height, width, 4))
        annotations = self.list()
        if annotations is None:
            self.logger.debug('No annotations found for item. id: %s' % self.item.id)
            return mask
        for annotation in annotations:
            try:
                label = annotation.label
                color = (255, 0, 0)
                if label in self.dataset.classes:
                    color = self.dataset.classes[label]
                random_color = *tuple(map(int, np.random.randint(0, 255, 3))), 255
                if annotation.type == 'binary':
                    if isinstance(annotation.coordinates, dict):
                        coordinates = annotation.coordinates['data'][22:]
                    elif isinstance(annotation.coordinates, str):
                        coordinates = annotation.coordinates[22:]
                    else:
                        raise TypeError('Unknown annotation type in binary. type: %s' % type(annotation.coordinates))
                    decode = base64.b64decode(coordinates)
                    n_mask = np.array(Image.open(io.BytesIO(decode)))
                    mask[np.where(n_mask[:, :, 3] > 127)] = [*color, 255]
                elif annotation.type == 'box':
                    for segment in annotation.coordinates:
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
                        cv2.drawContours(image=mask, contours=[pts], contourIdx=-1, color=random_color,
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
                    cv2.polylines(img=mask, pts=[pts], color=random_color, isClosed=False, thickness=thickness)
                    top_x = np.min(pts[:, 0])
                    top_y = np.min(pts[:, 1])
                    if with_text:
                        cv2.putText(mask, text=label, org=(top_x, top_y), color=(255, 255, 255, 255),
                                    fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=0.5,
                                    thickness=1)
                else:
                    self.logger.exception('Unknown annotation type: %s' % annotation.type)
                    raise TypeError('Unknown annotation type: %s' % annotation.type)
            except Exception as err:
                self.logger.exception('Unable to get annotation\'s mask. item_id: %s, annotation_id: %s' % (annotation.item.id, annotation.id))
        return mask.astype(np.uint8)

    def to_instance(self, img_shape, thickness=1):
        """
        Convert items annotations to an instance mask (2d array with label index)
        :param thickness: line thickness
        :return: ndarray
        """

        height, width = img_shape
        mask = np.zeros((width, height))
        annotations = self.list()
        for annotation in annotations:
            label_ind = list(self.dataset.classes.keys()).index(annotation.label)
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
                for segment in annotation.coordinates:
                    pts = np.asarray([[pt['x'], pt['y']] for pt in segment]).astype(int)
                    cv2.rectangle(img=mask,
                                  pt1=(np.min(pts[:, 0]), np.min(pts[:, 1])),
                                  pt2=(np.max(pts[:, 0]), np.max(pts[:, 1])),
                                  color=label_ind, thickness=thickness, lineType=cv2.LINE_AA)
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
        :return:
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
        success = self.client_api.gen_request(req_type='delete',
                                              path='/datasets/%s/items/%s/annotations/%s' % (
                                                  self.dataset.id, self.item.id, annotation_id),
                                              json_req=payload)
        if not success:
            raise self.client_api.platform_exception
        return True

    def download(self, filepath, get_mask=False, get_instance=False, img_shape=None, thickness=1):
        """
        Save annotation mask to file
        :param filepath:
        :param get_mask:
        :param get_instance:
        :param img_shape:
        :param thickness:
        :return:
        """

        if get_mask:
            mask = self.to_mask(img_shape=img_shape, thickness=thickness)
            img = Image.fromarray(mask)
            img.save(filepath)
        if get_instance:
            mask = self.to_instance(img_shape=img_shape, thickness=thickness)
            img = Image.fromarray(mask)
            img.save(filepath)

    def edit(self, annotations, annotations_ids=None, system_metadata=False):
        """
        Edit an existing annotation.
        :param annotations:
        :param annotations_ids:
        :param system_metadata:
        :return:
        """
        # annotation = {'attributes': [],
        #               'coordinates': [[{'x': 106.74999999999999, 'y': 103.14999999999999},
        #                                {'x': 320.71530562347186, 'y': 103.14999999999999},
        #                                {'x': 320.71530562347186, 'y': 257.1853056234719},
        #                                {'x': 106.74999999999999, 'y': 257.1853056234719}]],
        #               'label': '',
        #               'type': 'box'}

        if not isinstance(annotations, list):
            annotations = [annotations]
        if annotations_ids is not None:
            if not isinstance(annotations_ids, list):
                annotations_ids = [annotations_ids]
        else:
            annotations_ids = [None for _ in range(len(annotations))]

        if len(annotations) != len(annotations_ids):
            raise ValueError('inputs must have same length. len(annotations)=%d, len(annotations_ids)=%d' % (len(annotations), len(annotations_ids)))

        def edit_single_annotation(i_annotation):
            try:
                annotation = annotations[i_annotation]
                annotation_id = annotations_ids[i_annotation]
                if isinstance(annotation, str):
                    annotation = json.loads(annotation)
                elif isinstance(annotation, entities.Annotation):
                    annotation_id = annotation_id or annotation.id
                    annotation = annotation.to_dict()
                else:
                    self.logger.exception('Unknown annotation type: %s' % type(annotation))
                    raise ValueError('Unknown annotation type: %s' % type(annotation))

                if annotation_id is None:
                    self.logger.exception('missing argument: annotation_id')
                    raise ValueError('missing argument: annotation_id')
                url_path = '/datasets/%s/items/%s/annotations/%s' % (self.dataset.id, self.item.id, annotation_id)
                if system_metadata:
                    url_path += '?system=true'
                suc = self.client_api.gen_request(req_type='put',
                                                  path=url_path,
                                                  json_req=annotation)
                if suc:
                    success[i_annotation] = True
                else:
                    raise self.client_api.platform_exception

            except Exception as e:
                success[i_annotation] = False
                errors[i_annotation] = e

        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(processes=32)
        num_annotations = len(annotations)
        success = [None for _ in range(num_annotations)]
        errors = [None for _ in range(num_annotations)]
        for i_ann in range(len(annotations)):
            pool.apply_async(func=edit_single_annotation,
                             kwds={'i_annotation': i_ann})
        # log error
        dummy = [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        return True

    def upload(self, annotations):
        """
        Create a new annotation
        :param annotations: list or single annotation - dictionary or json string
        :return:
        """

        if not isinstance(annotations, list):
            annotations = [annotations]

        def upload_single_annotation(i_w_annotation, w_annotation):
            try:
                res = self.client_api.gen_request(req_type='post',
                                                  path='/datasets/%s/items/%s/annotations' %(self.dataset.id, self.item.id),
                                                  json_req=w_annotation)
                if res:
                    success[i_w_annotation] = True
                else:
                    raise self.client_api.platform_exception
            except Exception as e:
                success[i_w_annotation] = False
                errors[i_w_annotation] = e

        from multiprocessing.pool import ThreadPool
        pool = ThreadPool(processes=32)
        num_annotations = len(annotations)
        success = [None for _ in range(num_annotations)]
        errors = [None for _ in range(num_annotations)]
        for i_annotation, annotation in enumerate(annotations):
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            elif isinstance(annotation, entities.Annotation):
                annotation = annotation.to_dict()
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
        return True
