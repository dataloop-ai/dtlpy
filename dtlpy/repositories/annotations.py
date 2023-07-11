from copy import deepcopy
import traceback
import logging
import json
import jwt
import os

from .. import entities, exceptions, miscellaneous, _api_reference
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Annotations:
    """
    Annotations Repository

    The Annotation class allows you to manage the annotations of data items. For information on annotations explore our
    documentation at:
    `Classification SDK <https://dataloop.ai/docs/sdk-classify-item>`_,
    `Annotation Labels and Attributes <https://dataloop.ai/docs/sdk-annotation-ontology>`_,
    `Show Video with Annotations <https://dataloop.ai/docs/sdk-show-videos>`_.
    """

    def __init__(self, client_api: ApiClient, item=None, dataset=None, dataset_id=None):
        self._client_api = client_api
        self._item = item
        self._dataset = dataset
        self._upload_batch_size = 100
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
    @_api_reference.add(path='/annotations/{annotationId}', method='get')
    def get(self, annotation_id: str) -> entities.Annotation:
        """
        Get a single annotation.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param str annotation_id: The id of the annotation
        :return: Annotation object or None
        :return: Annotation object or None
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = item.annotations.get(annotation_id='annotation_id')
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
        Get a dataset's item list. This is a browsing endpoint. For any given path, item count will be returned.
        The user is then expected to perform another request for every folder to actually get its item list.

        :param dtlpy.entities.filters.Filters filters: Filter entity or a dictionary containing filters parameters

        :return: json response
        :rtype: 
        """
        # prepare request
        success, response = self._client_api.gen_request(req_type="POST",
                                                         path="/datasets/{}/query".format(self._dataset_id),
                                                         json_req=filters.prepare(),
                                                         headers={'user_query': filters._user_query}
                                                         )
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    @_api_reference.add(path='/datasets/{id}/query', method='post')
    def list(self, filters: entities.Filters = None, page_offset: int = None, page_size: int = None):
        """
        List Annotations of a specific item. You must get the item first and then list the annotations with the desired filters.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param int page_offset: starting page
        :param int page_size: size of page
        :return: Pages object
        :rtype: dtlpy.entities.paged_entities.PagedEntities

        **Example**:

        .. code-block:: python

            annotations = item.annotations.list(filters=dl.Filters(
                                         resource=dl.FiltersResource.ANNOTATION,
                                         field='type',
                                         values='box'),
                      page_size=100,
                      page_offset=0)
        """
        if self._dataset_id is not None:
            if filters is None:
                filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
                filters._user_query = 'false'

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
             thickness: int = 1,
             with_text: bool = False,
             height: float = None,
             width: float = None,
             annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.MASK,
             alpha: float = 1):
        """
        Show annotations. To use this method, you must get the item first and then show the annotations with
        the desired filters. The method returns an array showing all the annotations.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param ndarray image: empty or image to draw on
        :param int thickness: optional - line thickness, default=1
        :param bool with_text: add label to annotation
        :param float height: item height
        :param float width: item width
        :param str annotation_format: the format that want to show ,options: list(dl.ViewAnnotationOptions)
        :param float alpha: opacity value [0 1], default 1
        :return: ndarray of the annotations
        :rtype: ndarray

        **Example**:

        .. code-block:: python

            image = item.annotations.show(image='nd array',
                      thickness=1,
                      with_text=False,
                      height=100,
                      width=100,
                      annotation_format=dl.ViewAnnotationOptions.MASK,
                      alpha=1)
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

    def download(self,
                 filepath: str,
                 annotation_format: entities.ViewAnnotationOptions = entities.ViewAnnotationOptions.JSON,
                 img_filepath: str = None,
                 height: float = None,
                 width: float = None,
                 thickness: int = 1,
                 with_text: bool = False,
                 alpha: float = 1):
        """
        Save annotation to file.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param str filepath: Target download directory
        :param str annotation_format: the format that want to download ,options: list(dl.ViewAnnotationOptions)
        :param str img_filepath: img file path - needed for img_mask
        :param float height: optional - image height
        :param float width: optional - image width
        :param int thickness: optional - line thickness, default=1
        :param bool with_text: optional - draw annotation with text, default = False
        :param float alpha: opacity value [0 1], default 1
        :return: file path to where save the annotations
        :rtype: str

        **Example**:

        .. code-block:: python

            file_path = item.annotations.download(
                          filepath='file_path',
                          annotation_format=dl.ViewAnnotationOptions.MASK,
                          img_filepath='img_filepath',
                          height=100,
                          width=100,
                          thickness=1,
                          with_text=False,
                          alpha=1)
        """
        # get item's annotations
        annotations = self.list()
        if 'text' in self.item.metadata.get('system').get('mimetype', ''):
            annotation_format = entities.ViewAnnotationOptions.JSON
        elif 'audio' not in self.item.metadata.get('system').get('mimetype', ''):
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

    @_api_reference.add(path='/annotations/{annotationId}', method='delete')
    def delete(self, annotation: entities.Annotation = None,
               annotation_id: str = None,
               filters: entities.Filters = None) -> bool:
        """
        Remove an annotation from item.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param dtlpy.entities.annotation.Annotation annotation: Annotation object
        :param str annotation_id: The id of the annotation
        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :return: True/False
        :rtype: bool

        **Example**:

        .. code-block:: python

            is_deleted = item.annotations.delete(annotation_id='annotation_id')
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

    @staticmethod
    def _update_snapshots(origin, modified):
        """
        Update the snapshots if a change occurred and return a list of the new snapshots with the flag to update.
        """
        update = False
        origin_snapshots = list()
        origin_metadata = origin['metadata'].get('system', None)
        if origin_metadata:
            origin_snapshots = origin_metadata.get('snapshots_', None)
            if origin_snapshots is not None:
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
                if w_annotation.id is None:
                    raise exceptions.PlatformException(
                        '400',
                        'Cannot update annotation because it was not fetched'
                        ' from platform and therefore does not have an id'
                    )
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

    @_api_reference.add(path='/annotations/{annotationId}', method='put')
    def update(self, annotations, system_metadata=False):
        """
        Update an existing annotation. For example, you may change the annotation's label and then use the update method. 

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
         *developer* or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :param dtlpy.entities.annotation.Annotation annotations: Annotation object
        :param bool system_metadata: bool - True, if you want to change metadata system

        :return: True if successful or error if unsuccessful
        :rtype: bool

         **Example**:

        .. code-block:: python

            annotations = item.annotations.update(annotation='annotation')
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
        metadata = annotation.get('metadata', dict())
        system = metadata.get('system', dict())
        snapshots = system.get('snapshots_', list())
        last_frame = {
            'label': annotation.get('label', None),
            'attributes': annotation.get('attributes', None),
            'type': annotation.get('type', None),
            'data': annotation.get('coordinates', None),
            'fixed': snapshots[0].get('fixed', None) if (isinstance(snapshots, list) and len(snapshots) > 0) else None,
            'objectVisible': snapshots[0].get('objectVisible', None) if (
                    isinstance(snapshots, list) and len(snapshots) > 0) else None,
        }

        offset = 0
        for idx, frame in enumerate(deepcopy(snapshots)):
            frame.pop("frame", None)
            if frame == last_frame and not frame['fixed']:
                del snapshots[idx - offset]
                offset += 1
            else:
                last_frame = frame
        return annotation

    def _create_batches_for_upload(self, annotations):
        """
        receives a list of annotations and split them into batches to optimize the upload

        :param annotations: list of all annotations
        :return: batch_annotations: list of list of annotation. each batch with size self._upload_batch_size
        """
        annotation_batches = list()
        single_batch = list()
        for annotation in annotations:
            if isinstance(annotation, str):
                annotation = json.loads(annotation)
            elif isinstance(annotation, entities.Annotation):
                if annotation._item is None and self._item is not None:
                    # if annotation is without item - set one (affects the binary annotation color)
                    annotation._item = self._item
                annotation = annotation.to_json()
            elif isinstance(annotation, dict):
                pass
            else:
                raise exceptions.PlatformException(error='400',
                                                   message='unknown annotations type: {}'.format(type(annotation)))
            annotation = self._annotation_encoding(annotation)
            single_batch.append(annotation)
            if len(single_batch) >= self._upload_batch_size:
                annotation_batches.append(single_batch)
                single_batch = list()
        if len(single_batch) > 0:
            annotation_batches.append(single_batch)
        return annotation_batches

    def _upload_single_batch(self, annotation_batch):
        try:
            suc, response = self._client_api.gen_request(req_type='post',
                                                         path='/items/{}/annotations'.format(self.item.id),
                                                         json_req=annotation_batch)
            if suc:
                return_annotations = response.json()
                if not isinstance(return_annotations, list):
                    return_annotations = [return_annotations]
            else:
                raise exceptions.PlatformException(response)

            status = True
            result = return_annotations
        except Exception:
            status = False
            result = traceback.format_exc()

        return status, result

    def _upload_annotations_batches(self, annotation_batches):
        if len(annotation_batches) == 1:
            # no need for threads
            status, result = self._upload_single_batch(annotation_batch=annotation_batches[0])
            if status is False:
                logger.error(result)
                logger.error('Annotation/s uploaded with errors')
                # TODO need to raise errors?
            uploaded_annotations = result
        else:
            # threading
            pool = self._client_api.thread_pools(pool_name='annotation.upload')
            jobs = [None for _ in range(len(annotation_batches))]
            for i_ann, annotations_batch in enumerate(annotation_batches):
                jobs[i_ann] = pool.submit(self._upload_single_batch,
                                          annotation_batch=annotations_batch)
            # get all results
            results = [j.result() for j in jobs]
            uploaded_annotations = [ann for ann_list in results for ann in ann_list[1] if ann_list[0] is True]
            out_errors = [r[1] for r in results if r[0] is False]
            if len(out_errors) != 0:
                logger.error(out_errors)
                logger.error('Annotation/s uploaded with errors')
                # TODO need to raise errors?
        logger.info('Annotation/s uploaded successfully. num: {}'.format(len(uploaded_annotations)))
        return uploaded_annotations

    async def _async_upload_annotations(self, annotations):
        """
        Async function to run from the uploader. will use asyncio to not break the async
        :param annotations:
        :return:
        """
        async with self._client_api.event_loop.semaphore('annotations.upload'):
            annotation_batch = self._create_batches_for_upload(annotations=annotations)
            output_annotations = list()
            for annotations_list in annotation_batch:
                success, response = await self._client_api.gen_async_request(req_type='post',
                                                                             path='/items/{}/annotations'
                                                                             .format(self.item.id),
                                                                             json_req=annotations_list)
                if success:
                    return_annotations = response.json()
                    if not isinstance(return_annotations, list):
                        return_annotations = [return_annotations]
                    output_annotations.extend(return_annotations)
                else:
                    if len(output_annotations) > 0:
                        logger.warning("Only {} annotations from {} annotations have been uploaded".
                                       format(len(output_annotations), len(annotations)))
                    raise exceptions.PlatformException(response)

            result = entities.AnnotationCollection.from_json(_json=output_annotations, item=self.item)
            return result

    @_api_reference.add(path='/items/{itemId}/annotations', method='post')
    def upload(self, annotations) -> entities.AnnotationCollection:
        """
        Upload a new annotation/annotations. You must first create the annotation using the annotation *builder* method.

        **Prerequisites**: Any user can upload annotations.

        :param List[dtlpy.entities.annotation.Annotation] or dtlpy.entities.annotation.Annotation annotations: list or
        single annotation of type Annotation
        :return: list of annotation objects
        :rtype: entities.AnnotationCollection

        **Example**:

        .. code-block:: python

            annotations = item.annotations.upload(annotations='builder')
        """
        # make list if not list
        if isinstance(annotations, entities.AnnotationCollection):
            # get the annotation from a collection
            annotations = annotations.annotations
        elif isinstance(annotations, str) and os.path.isfile(annotations):
            # load annotation filepath and get list of annotations
            with open(annotations, 'r', encoding="utf8") as f:
                annotations = json.load(f)
            annotations = annotations.get('annotations', [])
            # annotations = entities.AnnotationCollection.from_json_file(filepath=annotations).annotations
        elif isinstance(annotations, entities.Annotation) or isinstance(annotations, dict):
            # convert the single Annotation to a list
            annotations = [annotations]
        elif isinstance(annotations, list):
            pass
        else:
            exceptions.PlatformException(error='400',
                                         message='Unknown annotation format. type: {}'.format(type(annotations)))
        if len(annotations) == 0:
            logger.warning('Annotation upload receives 0 annotations. Not doing anything')
            out_annotations = list()
        else:
            annotation_batches = self._create_batches_for_upload(annotations=annotations)
            out_annotations = self._upload_annotations_batches(annotation_batches=annotation_batches)
        out_annotations = entities.AnnotationCollection.from_json(_json=out_annotations,
                                                                  item=self.item)
        return out_annotations

    def update_status(self,
                      annotation: entities.Annotation = None,
                      annotation_id: str = None,
                      status: entities.AnnotationStatus = entities.AnnotationStatus.ISSUE
                      ) -> entities.Annotation:
        """
        Set status on annotation.

        **Prerequisites**: You must have an item that has been annotated. You must have the role of an *owner* or
        *developer* or be assigned a task that includes that item as an *annotation manager*.

        :param dtlpy.entities.annotation.Annotation annotation: Annotation object
        :param str annotation_id: optional - annotation id to set status
        :param str status: can be AnnotationStatus.ISSUE, APPROVED, REVIEW, CLEAR
        :return: Annotation object
        :rtype: dtlpy.entities.annotation.Annotation

        **Example**:

        .. code-block:: python

            annotation = item.annotations.update_status(annotation_id='annotation_id', status=dl.AnnotationStatus.ISSUE)
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
        """
        Create Annotation collection.

        **Prerequisites**: You must have an item to be annotated. You must have the role of an *owner* or *developer*
         or be assigned a task that includes that item as an *annotation manager* or *annotator*.

        :return: Annotation collection object
        :rtype: dtlpy.entities.annotation_collection.AnnotationCollection

        **Example**:

        .. code-block:: python

            annotation_collection = item.annotations.builder()
        """
        return entities.AnnotationCollection(item=self.item)

    ##################
    # async function #
    ##################
