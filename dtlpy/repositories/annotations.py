import json
import logging
import jwt
import attr
from multiprocessing.pool import ThreadPool

from .. import entities, PlatformException


@attr.s
class Annotations:
    """
        Annotations repository
    """
    logger = logging.getLogger('dataloop.annotations')
    client_api = attr.ib()
    dataset = attr.ib()
    item = attr.ib()

    @staticmethod
    def multiprocess_wrapper(func, items, params=None):
        """
            Wrapper to tun fun con a list of items in multi threads

        :param func:
        :param items:
        :param params:
        :return:
        """
        n_items = len(items)
        success = [False for _ in range(n_items)]
        output = [None for _ in range(n_items)]
        errors = [None for _ in range(n_items)]

        pool = ThreadPool(processes=32)
        for i_item, item in enumerate(items):
            pool.apply_async(func=func,
                             kwds={'i_item': i_item,
                                   'item': item,
                                   'output': output,
                                   'errors': errors,
                                   'success': success,
                                   'params': params})
        pool.close()
        pool.join()
        pool.terminate()
        errors = {i_job: errors[i_job] for i_job, suc in enumerate(success) if suc is False}
        return output, errors

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
            annotation = entities.Annotation.from_json(_json=response.json(),
                                                       item=self.item)
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
        if success:
            annotations = entities.AnnotationCollection.from_json(_json=response.json(),
                                                                  item=self.item)
        else:
            raise PlatformException(response)
        return annotations

    def show(self, image=None, thickness=1, with_text=False, height=None, width=None, annotation_format='mask'):
        """
        Show annotations

        :param image: empty or image to draw on
        :param height: height
        :param width: width
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param annotation_format: 'mask'/'instance'
        :return: ndarray of the annotations
        """
        # get item's annotations
        annotations = self.list()

        return annotations.show(image=image,
                                width=width,
                                height=height,
                                thickness=thickness,
                                with_text=with_text,
                                annotation_format=annotation_format)

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
        success, response = self.client_api.gen_request(
            req_type='delete',
            path='/datasets/{dataset_id}/items/{item_id}/annotations/{annotations_id}'.format(
                dataset_id=self.dataset.id,
                item_id=self.item.id,
                annotations_id=annotation_id),
            json_req=payload)
        if not success:
            raise PlatformException(response)
        self.logger.info('Annotation %s deleted successfully')
        return True

    def download(self, filepath, annotation_format='mask', height=None, width=None, thickness=1, with_text=False):
        """
            Save annotation format to file

        :param filepath:
        :param annotation_format:
        :param height:
        :param width:
        :param thickness:
        :param with_text:
        :return:
        """
        # get item's annotations
        annotations = self.list()

        # height/weight
        if height is None:
            if self.item.height is None:
                raise PlatformException('400', 'Height must be provided')
            height = self.item.height
        if width is None:
            if self.item.width is None:
                raise PlatformException('400', 'Width must be provided')
            width = self.item.width

        return annotations.download(filepath=filepath,
                                    width=width,
                                    height=height,
                                    thickness=thickness,
                                    with_text=with_text,
                                    annotation_format=annotation_format)

    def update(self, annotations, system_metadata=False):
        """
            Update an existing annotation.

        :param annotations:
        :param system_metadata:
        :return: True
        """

        def update_single_annotation(i_item, item, output, success, errors, params):
            try:
                if isinstance(item, entities.Annotation):
                    annotation_id = item.id
                    annotation = item.to_json()
                else:
                    raise PlatformException('400',
                                            'unknown annotations type: {}'.format(type(item)))

                url_path = '/datasets/%s/items/%s/annotations/%s' % (self.dataset.id, self.item.id, annotation_id)
                if params['system_metadata']:
                    url_path += '?system=true'
                suc, response = self.client_api.gen_request(req_type='put',
                                                            path=url_path,
                                                            json_req=annotation)
                if suc:
                    success[i_item] = True
                    output[i_item] = entities.Annotation.from_json(_json=response.json(),
                                                                   item=self.item)
                else:
                    raise PlatformException(response)

            except Exception as e:
                success[i_item] = False
                errors[i_item] = e

        if not isinstance(annotations, list):
            annotations = [annotations]
        multi_errors, multi_output = self.multiprocess_wrapper(func=update_single_annotation,
                                                               items=annotations,
                                                               params={'system_metadata': system_metadata})
        if len(multi_errors) == 0:
            self.logger.debug('Annotation/s uploaded with {} errors'.format(len(multi_errors)))
        else:
            self.logger.debug('Annotation/s uploaded successfully')
        return multi_output

    def upload(self, annotations):
        """
        Create a new annotation

        :param annotations: list or single annotation of type Annotation
        :return: list of annotation objects
        """

        def upload_single_annotation(i_item, item, output, success, errors, params):
            try:
                if isinstance(item, str):
                    annotation = json.loads(item)
                elif isinstance(item, entities.Annotation):
                    annotation = item.to_json()
                elif isinstance(item, dict):
                    annotation = item
                else:
                    raise PlatformException('400',
                                            'unknown annotations type: {}'.format(type(item)))
                annotation.pop('id', None)
                annotation.pop('_id', None)
                suc, response = self.client_api.gen_request(
                    req_type='post',
                    path='/datasets/{}/items/{}/annotations'.format(self.dataset.id, self.item.id),
                    json_req=annotation)
                if suc:
                    output[i_item] = entities.Annotation.from_json(_json=response.json(),
                                                                   item=self.item)
                    success[i_item] = True
                else:
                    raise PlatformException(response)
            except Exception as e:
                success[i_item] = False
                errors[i_item] = e

        # make list if not list
        if isinstance(annotations, entities.AnnotationCollection):
            annotations = annotations.annotations
        if not isinstance(annotations, list):
            annotations = [annotations]
        # call multiprocess wrapper to run function on each item in list
        multi_output, multi_errors = self.multiprocess_wrapper(func=upload_single_annotation,
                                                               items=annotations)
        if len(multi_errors) == 0:
            self.logger.debug('Annotation/s uploaded successfully')
        else:
            self.logger.error(multi_errors)
            self.logger.error('Annotation/s uploaded with {} errors'.format(len(multi_errors)))
        return multi_output

    def builder(self):
        return entities.AnnotationCollection(item=self.item)
