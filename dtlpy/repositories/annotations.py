from copy import deepcopy
import traceback
import logging
import json
import jwt
import os

from .. import entities, exceptions, miscellaneous, services

logger = logging.getLogger(name='dtlpy')


class Annotations:
    """
        Annotations repository
    """

    def __init__(self, client_api: services.ApiClient, item=None, dataset=None, dataset_id=None):
        self._client_api = client_api
        self._item = item
        self._dataset = dataset
        self._bulk_annotation = 200
        if dataset_id is None:
            if dataset is not None:
                dataset_id = dataset.id
            elif item is not None:
                dataset_id = item.dataset_id
        self._dataset_id = dataset_id

    ############
    # entities #
    ############
    @property
    def dataset(self):
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.annotations repository')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @property
    def item(self):
        if self._item is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "item". need to set an Item entity or use item.annotations repository')
        assert isinstance(self._item, entities.Item)
        return self._item

    @item.setter
    def item(self, item: entities.Item):
        if not isinstance(item, entities.Item):
            raise ValueError('Must input a valid Item entity')
        self._item = item

    ###########
    # methods #
    ###########
    def get(self, annotation_id):
        """
            Get a single annotation

        :param annotation_id:

        :return: Annotation object or None
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/annotations/{}'.format(annotation_id))
        if success:
            annotation = entities.Annotation.from_json(_json=response.json(),
                                                       annotations=self,
                                                       dataset=self._dataset,
                                                       client_api=self._client_api,
                                                       item=self._item)
        else:
            raise exceptions.PlatformException(response)
        return annotation

    def _build_entities_from_response(self, response_items):
        pool = self._client_api.thread_pools(pool_name='entity.create')
        jobs = [None for _ in range(len(response_items))]
        # return triggers list
        for i_json, _json in enumerate(response_items):
            jobs[i_json] = pool.submit(entities.Annotation._protected_from_json,
                                       **{'client_api': self._client_api,
                                          '_json': _json,
                                          'item': self._item,
                                          'dataset': self._dataset,
                                          'annotations': self})

        # get all results
        results = [j.result() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters: entities.Filters):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param filters: Filters entity or a dictionary containing filters parameters
        :return: json response
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(self._dataset_id),
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters: entities.Filters = None, page_offset=None, page_size=None):
        """
        List Annotation

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset: starting page
        :param page_size: size of page
        :return: Pages object
        """
        if self._dataset_id is not None:
            if filters is None:
                filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)

            if not filters.resource == entities.FiltersResource.ANNOTATION:
                raise exceptions.PlatformException(error='400',
                                                   message='Filters resource must to be FiltersResource.ANNOTATION')

            if self._item is not None and not filters.has_field('itemId'):
                filters = deepcopy(filters)
                filters.page_size = 1000
                filters.add(field='itemId', values=self.item.id, method=entities.FiltersMethod.AND)

            # assert type filters
            if not isinstance(filters, entities.Filters):
                raise exceptions.PlatformException('400', 'Unknown filters type')

            # page size
            if page_size is None:
                # take from default
                page_size = filters.page_size
            else:
                filters.page_size = page_size

            # page offset
            if page_offset is None:
                # take from default
                page_offset = filters.page
            else:
                filters.page = page_offset

            paged = entities.PagedEntities(items_repository=self,
                                           filters=filters,
                                           page_offset=page_offset,
                                           page_size=page_size,
                                           client_api=self._client_api)
            paged.get_page()

            if self._item is not None:
                if paged.total_pages_count > 1:
                    annotations = list()
                    for page in paged:
                        annotations += page
                else:
                    annotations = paged.items
                return entities.AnnotationCollection(annotations=annotations, item=self._item)
            else:
                return paged
        else:
            raise exceptions.PlatformException('400',
                                               'Please use item.annotations.list() or dataset.annotations.list() '
                                               'to perform this action.')

    def show(self,
             image=None,
             thickness=1,
             with_text=False,
             height=None,
             width=None,
             annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
             alpha=None):
        """
        Show annotations

        :param image: empty or image to draw on
        :param thickness: line thickness
        :param with_text: add label to annotation
        :param height: height
        :param width: width
        :param annotation_format: options: list(dl.ViewAnnotationOptions)
        :param alpha: opacity value [0 1], default 1
        :return: ndarray of the annotations
        """
        # get item's annotations
        annotations = self.list()

        return annotations.show(image=image,
                                width=width,
                                height=height,
                                thickness=thickness,
                                alpha=alpha,
                                with_text=with_text,
                                annotation_format=annotation_format)

    def download(self, filepath,
                 annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
                 img_filepath=None,
                 height=None,
                 width=None,
                 thickness=1,
                 with_text=False,
                 alpha=None):
        """
            Save annotation format to file

        :param filepath: Target download directory
        :param annotation_format: optional - list(dl.ViewAnnotationOptions)
        :param img_filepath: img file path - needed for img_mask
        :param height: optional - image height
        :param width: optional - image width
        :param thickness: optional - annotation format, default =1
        :param with_text: optional - draw annotation with text, default = False
        :param alpha: opacity value [0 1], default 1
        :return:
        """
        # get item's annotations
        annotations = self.list()
        if 'text' in self.item.metadata.get('system').get('mimetype', ''):
            annotation_format = entities.ViewAnnotationOptions.JSON
        else:
            # height/weight
            if height is None:
                if self.item.height is None:
                    raise exceptions.PlatformException('400', 'Height must be provided')
                height = self.item.height
            if width is None:
                if self.item.width is None:
                    raise exceptions.PlatformException('400', 'Width must be provided')
                width = self.item.width

        return annotations.download(filepath=filepath,
                                    img_filepath=img_filepath,
                                    width=width,
                                    height=height,
                                    thickness=thickness,
                                    with_text=with_text,
                                    annotation_format=annotation_format,
                                    alpha=alpha)

    def _delete_single_annotation(self, w_annotation_id):
        try:
            creator = jwt.decode(self._client_api.token, algorithms=['HS256'],
                                 verify=False, options={'verify_signature': False})['email']
            payload = {'username': creator}
            success, response = self._client_api.gen_request(req_type='delete',
                                                             path='/annotations/{}'.format(w_annotation_id),
                                                             json_req=payload)

            if not success:
                raise exceptions.PlatformException(response)
            return success
        except Exception:
            logger.exception('Failed to delete annotation')
            raise

    def delete(self, annotation=None, annotation_id=None, filters: entities.Filters = None):
        """
            Remove an annotation from item

        :param annotation: Annotation object
        :param annotation_id: annotation id
        :param filters: Filters entity or a dictionary containing filters parameters
        :return: True/False
        """
        if annotation is not None:
            if isinstance(annotation, entities.Annotation):
                annotation_id = annotation.id
            elif isinstance(annotation, str) and annotation.lower() == 'all':
                if self._item is None:
                    raise exceptions.PlatformException(error='400',
                                                       message='To use "all" option repository must have an item')
                filters = entities.Filters(
                    resource=entities.FiltersResource.ANNOTATION,
                    field='itemId',
                    values=self._item.id,
                    method=entities.FiltersMethod.AND
                )
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='Unknown annotation type')

        if annotation_id is not None:
            if not isinstance(annotation_id, list):
                return self._delete_single_annotation(w_annotation_id=annotation_id)
            filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION,
                                       field='annotationId',
                                       values=annotation_id,
                                       operator=entities.FiltersOperations.IN)
            filters.pop(field="type")

        if filters is None:
            raise exceptions.PlatformException(error='400',
                                               message='Must input filter, annotation id or annotation entity')

        if not filters.resource == entities.FiltersResource.ANNOTATION:
            raise exceptions.PlatformException(error='400',
                                               message='Filters resource must to be FiltersResource.ANNOTATION')

        if self._item is not None and not filters.has_field('itemId'):
            filters = deepcopy(filters)
            filters.add(field='itemId', values=self._item.id, method=entities.FiltersMethod.AND)

        if self._dataset is not None:
            items_repo = self._dataset.items
        elif self._item is not None:
            items_repo = self._item.dataset.items
        else:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "dataset". need to set a Dataset entity or use dataset.annotations repository')

        return items_repo.delete(filters=filters)

    def _update_snapshots(self, origin, modified):
        """
        function that update the snapshots if a change is happen
        return list of the new snapshots with the flag to update
        """
        update = False
        origin_snapshots = list()
        origin_metadata = origin['metadata'].get('system', None)
        if origin_metadata:
            origin_snapshots = origin_metadata.get('snapshots_', None)
            if origin_snapshots:
                modified_snapshots = modified['metadata'].get('system', dict()).get('snapshots_', None)
                # if the number of the snapshots change
                if len(origin_snapshots) != len(modified_snapshots):
                    origin_snapshots = modified_snapshots
                    update = True

                i = 0
                # if some snapshot change
                while i < len(origin_snapshots) and not update:
                    if origin_snapshots[i] != modified_snapshots[i]:
                        origin_snapshots = modified_snapshots
                        update = True
                        break
                    i += 1
        return update, origin_snapshots

    def _update_single_annotation(self, w_annotation, system_metadata):
        try:
            if isinstance(w_annotation, entities.Annotation):
                annotation_id = w_annotation.id
            else:
                raise exceptions.PlatformException('400',
                                                   'unknown annotations type: {}'.format(type(w_annotation)))

            origin = w_annotation._platform_dict
            modified = w_annotation.to_json()
            # check snapshots
            update, updated_snapshots = self._update_snapshots(origin=origin,
                                                               modified=modified)

            # pop the snapshots to make the diff work with out them
            origin.get('metadata', dict()).get('system', dict()).pop('snapshots_', None)
            modified.get('metadata', dict()).get('system', dict()).pop('snapshots_', None)

            # check diffs in the json
            json_req = miscellaneous.DictDiffer.diff(origin=origin,
                                                     modified=modified)

            # add the new snapshots if exist
            if updated_snapshots and update:
                if 'metadata' not in json_req:
                    json_req['metadata'] = dict()
                if 'system' not in json_req['metadata']:
                    json_req['metadata']['system'] = dict()
                json_req['metadata']['system']['snapshots_'] = updated_snapshots

            # no changes happen
            if not json_req and not updated_snapshots:
                status = True
                result = w_annotation
            else:
                url_path = '/annotations/{}'.format(annotation_id)
                if system_metadata:
                    url_path += '?system=true'
                suc, response = self._client_api.gen_request(req_type='put',
                                                             path=url_path,
                                                             json_req=json_req)
                if suc:
                    result = entities.Annotation.from_json(_json=response.json(),
                                                           annotations=self,
                                                           dataset=self._dataset,
                                                           item=self._item)
                    w_annotation._platform_dict = result._platform_dict
                else:
                    raise exceptions.PlatformException(response)
                status = True
        except Exception:
            status = False
            result = traceback.format_exc()
        return status, result

    def update(self, annotations, system_metadata=False):
        """
            Update an existing annotation.

        :param annotations: annotations object
        :param system_metadata: bool - True, if you want to change metadata system
        :return: True
        """
        pool = self._client_api.thread_pools(pool_name='annotation.update')
        if not isinstance(annotations, list):
            annotations = [annotations]
        jobs = [None for _ in range(len(annotations))]
        for i_ann, ann in enumerate(annotations):
            jobs[i_ann] = pool.submit(self._update_single_annotation,
                                      **{'w_annotation': ann,
                                         'system_metadata': system_metadata})

        # get all results
        results = [j.result() for j in jobs]
        out_annotations = [r[1] for r in results if r[0] is True]
        out_errors = [r[1] for r in results if r[0] is False]
        if len(out_errors) == 0:
            logger.debug('Annotation/s updated successfully. {}/{}'.format(len(out_annotations), len(results)))
        else:
            logger.error(out_errors)
            logger.error('Annotation/s updated with {} errors'.format(len(out_errors)))
        return out_annotations

    @staticmethod
    def _annotation_encoding(annotation):
        last_frame = dict()
        metadata = annotation.get('metadata', dict())
        system = metadata.get('system', dict())
        snapshots = system.get('snapshots_', dict())
        offset = 0
        for idx, frame in enumerate(deepcopy(snapshots)):
            frame.pop("frame", None)
            if frame == last_frame:
                del snapshots[idx - offset]
                offset += 1
            else:
                last_frame = frame
        return annotation

    def _upload_annotations(self, annotations):
        bulk_annotations_list = list()
        bulk_return_annotations = list()
        annotations_list = list()

        for annotation in annotations:
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            elif isinstance(annotation, entities.Annotation):
                annotation = annotation.to_json()
            elif isinstance(annotation, dict):
                annotation = annotation
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='unknown annotations type: {}'.format(type(annotation)))
            annotation = self._annotation_encoding(annotation)
            annotations_list.append(annotation)
            if len(annotations_list) >= self._bulk_annotation:
                bulk_annotations_list.append(annotations_list)
                annotations_list = list()

        bulk_annotations_list.append(annotations_list)
        for annotations_list in bulk_annotations_list:
            suc, response = self._client_api.gen_request(req_type='post',
                                                         path='/items/{}/annotations'.format(self.item.id),
                                                         json_req=annotations_list)
            if suc:
                return_annotations = response.json()
                if not isinstance(return_annotations, list):
                    return_annotations = [return_annotations]
                bulk_return_annotations += return_annotations
            else:
                if len(bulk_return_annotations) > 0:
                    logger.warning("Only {} annotations from {} annotations have been uploaded".
                                   format(len(bulk_return_annotations), len(annotations)))
                raise exceptions.PlatformException(response)

        result = entities.AnnotationCollection.from_json(_json=bulk_return_annotations,
                                                         item=self.item)
        return result

    def upload(self, annotations):
        """
        Create a new annotation

        :param annotations: list or single annotation of type Annotation
        :return: list of annotation objects
        """
        # make list if not list
        if isinstance(annotations, entities.AnnotationCollection):
            annotations = annotations.annotations
        if not isinstance(annotations, list):
            annotations = [annotations]
            if isinstance(annotations[0], str) and os.path.isfile(annotations[0]):
                with open(annotations[0], 'r', encoding="utf8") as f:
                    annotations = json.load(f)
                if isinstance(annotations, dict):
                    if 'annotations' in annotations:
                        annotations = annotations['annotations']
                    elif 'data' in annotations:
                        annotations = annotations['data']
                    else:
                        exceptions.PlatformException('400', 'Unknown annotation file format')
        out_annotations = self._upload_annotations(annotations=annotations)
        return out_annotations

    def update_status(self, annotation: entities.Annotation = None,
                      annotation_id=None,
                      status: entities.AnnotationStatus = entities.AnnotationStatus.ISSUE):
        """
        Set status on annotation

        :param annotation: optional - Annotation entity
        :param annotation_id: optional - annotation id to set status
        :param status: can be AnnotationStatus.ISSUE, AnnotationStatus.APPROVED, AnnotationStatus.REVIEW, AnnotationStatus.CLEAR

        :return: Annotation object
        """
        if annotation is None:
            if annotation_id is None:
                raise ValueError('must input on of "annotation" or "annotation_id"')
            annotation = self.get(annotation_id=annotation_id)
        if status not in list(entities.AnnotationStatus):
            raise ValueError('status must be on of: {}'.format(', '.join(list(entities.AnnotationStatus))))
        annotation.status = status
        return annotation.update(system_metadata=True)

    def builder(self):
        return entities.AnnotationCollection(item=self.item)

    ##################
    # async function #
    ##################

    async def _async_upload_annotations(self, annotations):
        async with self._client_api.event_loops('items.upload').semaphore('annotations.upload'):
            bulk_annotations_list = list()
            bulk_return_annotations = list()
            annotations_list = list()

            for annotation in annotations:
                if isinstance(annotation, str):
                    annotation = json.loads(annotation)
                elif isinstance(annotation, entities.Annotation):
                    annotation = annotation.to_json()
                elif isinstance(annotation, dict):
                    annotation = annotation
                else:
                    raise exceptions.PlatformException(error='400',
                                                       message='unknown annotations type: {}'.format(type(annotation)))
                annotation = self._annotation_encoding(annotation)
                annotations_list.append(annotation)
                if len(annotations_list) >= self._bulk_annotation:
                    bulk_annotations_list.append(annotations_list)
                    annotations_list = list()

            bulk_annotations_list.append(annotations_list)
            for annotations_list in bulk_annotations_list:
                success, response = await self._client_api.gen_async_request(req_type='post',
                                                                             path='/items/{}/annotations'
                                                                             .format(self.item.id),
                                                                             json_req=annotations_list)
                if success:
                    return_annotations = response.json()
                    if not isinstance(return_annotations, list):
                        return_annotations = [return_annotations]
                    bulk_return_annotations += return_annotations
                else:
                    if len(bulk_return_annotations) > 0:
                        logger.warning("Only {} annotations from {} annotations have been uploaded".
                                       format(len(bulk_return_annotations), len(annotations)))
                    raise exceptions.PlatformException(response)

            result = entities.AnnotationCollection.from_json(_json=bulk_return_annotations, item=self.item)
            return result
