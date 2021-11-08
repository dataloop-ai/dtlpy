from jinja2 import Environment, PackageLoader
from multiprocessing.pool import ThreadPool
from multiprocessing import Lock
from .base_package_runner import Progress
from .. import exceptions, entities, dtlpy_services
import xml.etree.ElementTree as Et
from ..services import Reporter
from itertools import groupby
from PIL import Image
import numpy as np
import mimetypes
import traceback
import logging
import json
import copy
import tqdm
import os

logger = logging.getLogger(name=__name__)


class AnnotationFormat:
    YOLO = 'yolo'
    COCO = 'coco'
    VOC = 'voc'
    DATALOOP = 'dataloop'


class COCOUtils:

    @staticmethod
    def binary_mask_to_rle_encode(binary_mask):
        try:
            import pycocotools.mask as coco_utils_mask
        except ModuleNotFoundError:
            raise Exception('To use this functionality please install pycocotools:  "pip install pycocotools"')
        fortran_ground_truth_binary_mask = np.asfortranarray(binary_mask.astype(np.uint8))
        encoded_ground_truth = coco_utils_mask.encode(fortran_ground_truth_binary_mask)
        encoded_ground_truth['counts'] = encoded_ground_truth['counts'].decode()
        return encoded_ground_truth

    @staticmethod
    def binary_mask_to_rle(binary_mask, height, width):
        rle = {'counts': [], 'size': [height, width]}
        counts = rle.get('counts')
        for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
            if i == 0 and value == 1:
                counts.append(0)
            counts.append(len(list(elements)))
        return rle

    @staticmethod
    def polygon_to_rle(geo, height, width):
        segmentation = [float(n) for n in geo.flatten()]
        area = np.sum(entities.Segmentation.from_polygon(geo=geo, label=None, shape=(height, width)).geo > 0)
        return [segmentation], int(area)

    @staticmethod
    def rle_to_binary_mask(rle):
        rows, cols = rle['size']
        rle_numbers = rle['counts']
        if isinstance(rle_numbers, list):
            if len(rle_numbers) % 2 != 0:
                rle_numbers.append(0)

            rle_pairs = np.array(rle_numbers).reshape(-1, 2)
            img = np.zeros(rows * cols, dtype=np.uint8)
            index = 0
            for i, length in rle_pairs:
                index += i
                img[index:index + length] = 1
                index += length
            img = img.reshape(cols, rows)
            return img.T
        else:
            try:
                import pycocotools.mask as coco_utils_mask
            except ModuleNotFoundError:
                raise Exception('To use this functionality please install pycocotools:  "pip install pycocotools"')
            img = coco_utils_mask.decode(rle)
            return img

    @staticmethod
    def rle_to_binary_polygon(segmentation):
        return [segmentation[x:x + 2] for x in range(0, len(segmentation), 2)]


class Converter:
    """
    Annotation Converter
    """

    def __init__(self):
        self.known_formats = [AnnotationFormat.YOLO,
                              AnnotationFormat.COCO,
                              AnnotationFormat.VOC,
                              AnnotationFormat.DATALOOP]
        self.converter_dict = {
            AnnotationFormat.YOLO: {"from": self.from_yolo, "to": self.to_yolo},
            AnnotationFormat.COCO: {"from": self.from_coco, "to": self.to_coco},
            AnnotationFormat.VOC: {"from": self.from_voc, "to": self.to_voc},
        }
        self.dataset = None
        self.save_to_format = None
        self.xml_template_path = 'voc_annotation_template.xml'
        self.labels = dict()
        self._only_bbox = False
        self._progress = None
        self._progress_update_frequency = 5
        self._update_agent_progress = False
        self._progress_checkpoint = 0
        self._checkpoint_lock = Lock()
        self.remote_items = None

    def attach_agent_progress(self, progress: Progress, progress_update_frequency: int = None):
        self._progress = progress
        self._progress_update_frequency = progress_update_frequency if progress_update_frequency is not None \
            else self._progress_update_frequency
        self._update_agent_progress = True

    @property
    def _update_progress_active(self):
        return self._progress is not None and self._update_agent_progress and isinstance(
            self._progress_update_frequency, int)

    def __update_progress(self, total, of_total):
        if self._update_progress_active:
            try:
                progress = int((of_total / total) * 100)
                if progress > self._progress_checkpoint and (progress % self._progress_update_frequency == 0):
                    self._progress.update(progress=progress)
                    with self._checkpoint_lock:
                        self._progress_checkpoint = progress
            except Exception:
                logger.warning('[Converter] Failed to update agent progress')

    def _get_labels(self):
        self.labels = dict()
        if self.dataset:
            labels = list(self.dataset.instance_map.keys())
            labels.sort()
            self.labels = {label: i for i, label in enumerate(labels)}

    def convert_dataset(self,
                        dataset,
                        to_format,
                        local_path,
                        conversion_func=None,
                        filters=None,
                        annotation_filter=None):
        """
        Convert entire dataset

        :param annotation_filter:
        :param dataset:
        :param to_format:
        :param local_path:
        :param conversion_func: Custom conversion service
        :param filters: optional
        :return:
        """
        if to_format.lower() == AnnotationFormat.COCO:
            return self.__convert_dataset_to_coco(dataset=dataset,
                                                  local_path=local_path,
                                                  filters=filters,
                                                  annotation_filter=annotation_filter)
        num_workers = 6
        assert isinstance(dataset, entities.Dataset)
        self.dataset = dataset

        # download annotations
        if annotation_filter is None:
            logger.info('Downloading annotations...')
            dataset.download_annotations(local_path=local_path, overwrite=True)
            logger.info('Annotations downloaded')
        local_annotations_path = os.path.join(local_path, "json")
        output_annotations_path = os.path.join(local_path, to_format)
        pool = ThreadPool(processes=num_workers)
        i_item = 0
        pages = dataset.items.list(filters=filters)

        # if yolo - create labels file
        if to_format == AnnotationFormat.YOLO:
            self._get_labels()
            with open('{}/{}.names'.format(local_path, dataset.name), 'w') as fp:
                labels = list(self.labels.keys())
                labels.sort()
                for label in labels:
                    fp.write("{}\n".format(label))

        pbar = tqdm.tqdm(total=pages.items_count)
        reporter = Reporter(num_workers=pages.items_count,
                            resource=Reporter.CONVERTER,
                            print_error_logs=self.dataset._client_api.verbose.print_error_logs,
                            client_api=self.dataset._client_api)
        for page in pages:
            for item in page:
                # create input annotations json
                in_filepath = os.path.join(local_annotations_path, item.filename[1:])
                name, ext = os.path.splitext(in_filepath)
                in_filepath = name + '.json'

                save_to = os.path.dirname(in_filepath.replace(local_annotations_path, output_annotations_path))

                if not os.path.isdir(save_to):
                    os.makedirs(save_to, exist_ok=True)

                pool.apply_async(
                    func=self.__save_filtered_annotations_and_convert,
                    kwds={
                        "to_format": to_format,
                        "from_format": AnnotationFormat.DATALOOP,
                        "file_path": in_filepath,
                        "save_locally": True,
                        "save_to": save_to,
                        'conversion_func': conversion_func,
                        'item': item,
                        'pbar': pbar,
                        'filters': annotation_filter,
                        'reporter': reporter,
                        'i_item': i_item
                    }
                )
                i_item += 1
        pool.close()
        pool.join()
        pool.terminate()

        if reporter.has_errors:
            log_filepath = reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning(
                    'Converted with some errors. Please see log in {} for more information.'.format(log_filepath))

        logger.info('Total converted: {}'.format(reporter.status_count('success')))
        logger.info('Total skipped: {}'.format(reporter.status_count('skip')))
        logger.info('Total failed: {}'.format(reporter.status_count('failed')))

    def __save_filtered_annotations_and_convert(self, item: entities.Item, filters, to_format, from_format, file_path,
                                                save_locally=False,
                                                save_to=None, conversion_func=None,
                                                pbar=None, **kwargs):
        reporter = kwargs.get('reporter', None)
        i_item = kwargs.get('i_item', None)

        try:
            if item.annotated and item.type != 'dir':
                if filters is not None:
                    assert filters.resource == entities.FiltersResource.ANNOTATION
                    copy_filters = copy.deepcopy(filters)
                    copy_filters.add(field='itemId', values=item.id, method='and')
                    annotations_page = item.dataset.items.list(filters=copy_filters)
                    annotations = item.annotations.builder()
                    for page in annotations_page:
                        for annotation in page:
                            annotations.annotations.append(annotation)

                    if not os.path.isdir(os.path.dirname(file_path)):
                        os.makedirs(os.path.dirname(file_path))
                    with open(file_path, 'w') as f:
                        json.dump(annotations.to_json(), f, indent=2)

                annotations_list, errors = self.convert_file(
                    item=item,
                    to_format=to_format,
                    from_format=from_format,
                    file_path=file_path,
                    save_locally=save_locally,
                    save_to=save_to,
                    conversion_func=conversion_func,
                    pbar=pbar
                )

                if errors:
                    raise Exception('Partial conversion: \n{}'.format(errors))

                if reporter is not None and i_item is not None:
                    reporter.set_index(status='success', success=True, ref=item.id)
            else:
                if reporter is not None and i_item is not None:
                    reporter.set_index(ref=item.id, status='skip', success=True)
            if reporter is not None:
                self.__update_progress(total=reporter.num_workers, of_total=i_item)
        except Exception:
            if reporter is not None and i_item is not None:
                reporter.set_index(status='failed', success=False, error=traceback.format_exc(),
                                   ref=item.id)

    @staticmethod
    def __gen_coco_categories(instance_map, recipe):
        categories = list()
        last_id = 0
        for label, label_id in instance_map.items():
            label_name, sup = label.split('.')[-1], '.'.join(label.split('.')[0:-1])
            category = {'id': label_id, 'name': label_name}
            last_id = max(last_id, label_id)
            if sup:
                category['supercategory'] = sup
            categories.append(category)

        # add keypoint category
        collection_templates = list()
        if 'system' in recipe.metadata and 'collectionTemplates' in recipe.metadata['system']:
            collection_templates = recipe.metadata['system']['collectionTemplates']

        for template in collection_templates:
            last_id += 1
            order_dict = {key: i for i, key in enumerate(template['order'])}
            skeleton = list()
            for pair in template['arcs']:
                skeleton.append([order_dict[pair[0]], order_dict[pair[1]]])
            category = {'id': last_id,
                        'name': template['name'],
                        'templateId': template['id'],
                        'keypoints': template['order'],
                        'skeleton': skeleton}
            instance_map[template['name']] = last_id
            categories.append(category)
        return categories

    def __convert_dataset_to_coco(self, dataset: entities.Dataset, local_path, filters=None, annotation_filter=None):
        pages = dataset.items.list(filters=filters)
        dataset.download_annotations(local_path=local_path)
        path_to_dataloop_annotations_dir = os.path.join(local_path, 'json')
        label_to_id = dataset.instance_map
        recipe = dataset.recipes.list()[0]
        categories = self.__gen_coco_categories(instance_map=label_to_id, recipe=recipe)
        images = [None for _ in range(pages.items_count)]
        converted_annotations = [None for _ in range(pages.items_count)]
        item_id_counter = 0
        pool = ThreadPool(processes=11)
        pbar = tqdm.tqdm(total=pages.items_count)
        reporter = Reporter(num_workers=pages.items_count,
                            resource=Reporter.CONVERTER,
                            print_error_logs=dataset._client_api.verbose.print_error_logs,
                            client_api=dataset._client_api)
        for page in pages:
            for item in page:
                pool.apply_async(func=self.__single_item_to_coco,
                                 kwds={
                                     'item': item,
                                     'images': images,
                                     'path_to_dataloop_annotations_dir': path_to_dataloop_annotations_dir,
                                     'item_id': item_id_counter,
                                     'reporter': reporter,
                                     'converted_annotations': converted_annotations,
                                     'annotation_filter': annotation_filter,
                                     'label_to_id': label_to_id,
                                     'categories': categories,
                                     'pbar': pbar
                                 })
                item_id_counter += 1

        pool.close()
        pool.join()
        pool.terminate()

        total_converted_annotations = list()
        for ls in converted_annotations:
            if ls is not None:
                total_converted_annotations += ls

        for i_ann, ann in enumerate(total_converted_annotations):
            ann['id'] = i_ann

        info = {
            'description': dataset.name
        }

        coco_json = {'images': [image for image in images if image is not None],
                     'info': info,
                     'annotations': total_converted_annotations,
                     'categories': categories}

        with open(os.path.join(local_path, 'coco.json'), 'w+') as f:
            json.dump(coco_json, f)

        if reporter.has_errors:
            log_filepath = reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning(
                    'Converted with some errors. Please see log in {} for more information.'.format(log_filepath))

        logger.info('Total converted: {}'.format(reporter.status_count('success')))
        logger.info('Total failed: {}'.format(reporter.status_count('failed')))

        return coco_json

    @staticmethod
    def __get_item_shape(item: entities.Item = None, local_path: str = None):
        if isinstance(item, entities.Item) and (item.width is None or item.height is None):
            try:
                img = Image.open(item.download(save_locally=False)) if local_path is None else Image.open(local_path)
                item.height = img.height
                item.width = img.width
            except Exception:
                pass
        return item

    def __add_item_converted_annotation(self, item, annotation, label_to_id, item_id,
                                        i_annotation, item_converted_annotations):
        try:
            ann = self.to_coco(annotation=annotation, item=item)
            ann['category_id'] = label_to_id[annotation.label]
            ann['image_id'] = item_id
            ann['id'] = int('{}{}'.format(item_id, i_annotation))

            item_converted_annotations.append(ann)
        except Exception:
            err = 'Error converting annotation: \n' \
                  'Item: {}, annotation: {} - ' \
                  'fail to convert some of the annotation\n{}'.format(item_id,
                                                                      annotation.id,
                                                                      traceback.format_exc())
            item_converted_annotations.append(err)

    def __coco_handle_pose_annotations(self, item, item_id, pose_annotations, point_annotations,
                                       categories, label_to_id, item_converted_annotations):
        # link points to pose and convert it
        for pose in pose_annotations:
            pose_idx = pose[1]
            pose = pose[0]
            pose_category = None
            for category in categories:
                if pose.coordinates.get('templateId', "") == category.get('templateId', None):
                    pose_category = category
                    continue
            if pose_category is None:
                err = 'Error converting annotation: \n' \
                      'Item: {}, annotation: {} - ' \
                      'Pose annotation without known template\n{}'.format(item_id,
                                                                          pose.id,
                                                                          traceback.format_exc())
                item_converted_annotations.append(err)
                continue
            if pose.id not in point_annotations or (pose.id in point_annotations and
                                                    len(point_annotations[pose.id]) != len(pose_category['keypoints'])):
                err = 'Error converting annotation: \n' \
                      'Item: {}, annotation: {} - ' \
                      'Pose annotation has {} children ' \
                      'while it template has {} points\n{}'.format(item_id,
                                                                   pose.id,
                                                                   len(point_annotations[pose.id]),
                                                                   len(pose_category['keypoints']),
                                                                   traceback.format_exc())
                item_converted_annotations.append(err)
                continue
            # verify points labels are unique
            if len(point_annotations[pose.id]) != len(set([ann.label for ann in point_annotations[pose.id]])):
                err = 'Error converting annotation: \n' \
                      'Item: {}, annotation: {} - Pose annotation ' \
                      'does not have unique children points\n{}'.format(item_id,
                                                                        pose.id,
                                                                        traceback.format_exc())
                item_converted_annotations.append(err)
                continue

            ordered_points = list()
            for pose_point in pose_category['keypoints']:
                for point_annotation in point_annotations[pose.id]:
                    if point_annotation.label == pose_point:
                        ordered_points.append(point_annotation)
                        break
            pose.annotation_definition.points = ordered_points

            self.__add_item_converted_annotation(item=item, annotation=pose,
                                                 label_to_id=label_to_id,
                                                 item_id=item_id, i_annotation=pose_idx,
                                                 item_converted_annotations=item_converted_annotations)

    def __single_item_to_coco(self, item: entities.Item, images, path_to_dataloop_annotations_dir, item_id,
                              converted_annotations, annotation_filter, label_to_id, reporter, categories, pbar=None):
        try:
            if item.type != 'dir':
                item = Converter.__get_item_shape(item=item)
                images[item_id] = {'file_name': item.name,
                                   'id': item_id,
                                   'width': item.width,
                                   'height': item.height
                                   }
                if annotation_filter is None:
                    try:
                        filename, ext = os.path.splitext(item.filename)
                        filename = '{}.json'.format(filename[1:])
                        with open(os.path.join(path_to_dataloop_annotations_dir, filename), 'r', encoding="utf8") as f:
                            annotations = json.load(f)['annotations']
                        annotations = entities.AnnotationCollection.from_json(annotations)
                    except Exception:
                        annotations = item.annotations.list()
                else:
                    copy_filters = copy.deepcopy(annotation_filter)
                    copy_filters.add(field='itemId', values=item.id, method='and')
                    annotations_page = item.dataset.items.list(filters=copy_filters)
                    annotations = item.annotations.builder()
                    for page in annotations_page:
                        for annotation in page:
                            annotations.annotations.append(annotation)

                item_converted_annotations = list()
                point_annotations = dict()
                pose_annotations = list()

                for i_annotation, annotation in enumerate(annotations.annotations):
                    if annotation.type == 'point' and annotation.parent_id is not None:
                        if annotation.parent_id not in point_annotations:
                            point_annotations[annotation.parent_id] = list()
                        point_annotations[annotation.parent_id].append(annotation)
                        continue
                    if annotation.type == 'pose':
                        pose_annotations.append([annotation, i_annotation])
                        continue
                    self.__add_item_converted_annotation(item=item, annotation=annotation,
                                                         label_to_id=label_to_id,
                                                         item_id=item_id, i_annotation=i_annotation,
                                                         item_converted_annotations=item_converted_annotations)

                self.__coco_handle_pose_annotations(item=item, item_id=item_id,
                                                    pose_annotations=pose_annotations,
                                                    point_annotations=point_annotations,
                                                    categories=categories,
                                                    label_to_id=label_to_id,
                                                    item_converted_annotations=item_converted_annotations)

                success, errors = self._sort_annotations(annotations=item_converted_annotations)
                converted_annotations[item_id] = success
                if errors:
                    reporter.set_index(ref=item.id, status='failed', success=False,
                                       error=errors)
                else:
                    reporter.set_index(ref=item.id, status='success', success=True)
        except Exception:
            reporter.set_index(ref=item.id, status='failed', success=False,
                               error=traceback.format_exc())
            raise

        if pbar is not None:
            pbar.update()

        if reporter is not None:
            self.__update_progress(total=reporter.num_workers, of_total=item_id)

    def _upload_coco_labels(self, coco_json):
        labels = coco_json.get('categories', None)
        upload_labels = dict()
        for label in labels:
            if 'supercategory' in label and label['supercategory'] is not None:
                if label['supercategory'] not in upload_labels:
                    upload_labels[label['supercategory']] = entities.Label(tag=label['supercategory'])
                upload_labels[label['supercategory']].children.append(entities.Label(tag=label['name']))
                tag = '{}.{}'.format(label['supercategory'], label['name'])
            else:
                tag = label['name']
                upload_labels[label['name']] = entities.Label(tag=tag)
            self.labels[tag] = label['id']

        return upload_labels

    def _upload_coco_dataset(self, local_items_path, local_annotations_path, only_bbox=False, remote_items=False):
        logger.info('loading annotations json...')
        with open(local_annotations_path, 'r', encoding="utf8") as f:
            coco_json = json.load(f)

        labels_tags_tree = self._upload_coco_labels(coco_json=coco_json)
        try:
            logger.info('Uploading labels to dataset')
            self.dataset.add_labels(list(labels_tags_tree.values()))
        except Exception:
            logger.warning('Failed to upload labels to dataset, please add manually')

        image_annotations = dict()
        image_name_id = dict()
        for image in coco_json['images']:
            image_metadata = image
            image_annotations[image['file_name']] = {
                'id': image['id'],
                'metadata': image_metadata,
                'annotations': list()
            }
            image_name_id[image['id']] = image['file_name']
        for ann in coco_json['annotations']:
            image_annotations[image_name_id[ann['image_id']]]['annotations'].append(ann)

        if remote_items:
            return self._upload_annotations(local_annotations_path=image_annotations,
                                            from_format=AnnotationFormat.COCO,
                                            only_bbox=only_bbox)
        else:
            return self._upload_directory(local_items_path=local_items_path,
                                          local_annotations_path=image_annotations,
                                          from_format=AnnotationFormat.COCO,
                                          only_bbox=only_bbox)

    def _read_labels(self, labels_file_path):
        if labels_file_path:
            with open(labels_file_path, 'r') as fp:
                labels = [line.strip() for line in fp.readlines()]
                self.dataset.add_labels(label_list=labels)
                self.labels = {label: i_label for i_label, label in enumerate(labels)}
        else:
            logger.warning('No labels file path provided (.names), skipping labels upload')
            self._get_labels()

    def _upload_yolo_dataset(self, local_items_path, local_annotations_path, labels_file_path, remote_items=False):
        self._read_labels(labels_file_path=labels_file_path)
        if remote_items:
            return self._upload_annotations(local_annotations_path=local_annotations_path,
                                            from_format=AnnotationFormat.YOLO)
        else:
            return self._upload_directory(local_items_path=local_items_path,
                                          local_annotations_path=local_annotations_path,
                                          from_format=AnnotationFormat.YOLO)

    def _upload_voc_dataset(self, local_items_path, local_annotations_path, remote_items=False, **_):
        # TODO - implement VOC annotations upload
        logger.warning('labels upload from VOC dataset is not implemented, please upload labels manually')

        if remote_items:
            return self._upload_annotations(local_annotations_path=local_annotations_path,
                                            from_format=AnnotationFormat.VOC)
        else:
            return self._upload_directory(local_items_path=local_items_path,
                                          local_annotations_path=local_annotations_path,
                                          from_format=AnnotationFormat.VOC)

    @staticmethod
    def _find_yolo_voc_item_annotations(local_annotations_path: str, item: entities.Item, from_format: str):
        found = False
        metadata = None

        extension = '.txt' if from_format == AnnotationFormat.YOLO else '.xml'
        filename, _ = os.path.splitext(item.filename)
        annotations_filepath = os.path.join(local_annotations_path, filename[1:] + extension)
        if os.path.isfile(annotations_filepath):
            found = True

        return found, annotations_filepath, metadata

    @staticmethod
    def _find_coco_item_annotations(local_annotations_path: dict, item: entities.Item):
        found = False
        ann_dict = None
        if item.name in local_annotations_path:
            ann_dict = local_annotations_path[item.name]
            found = True
        elif item.filename in local_annotations_path:
            ann_dict = local_annotations_path[item.filename]
            found = True
        metadata = ann_dict.get('metadata', None) if found else None
        return found, ann_dict, metadata

    def _upload_annotations(self, local_annotations_path, from_format, **kwargs):
        self._only_bbox = kwargs.get('only_bbox', False)
        file_count = self.remote_items.items_count
        reporter = Reporter(num_workers=file_count,
                            resource=Reporter.CONVERTER,
                            print_error_logs=self.dataset._client_api.verbose.print_error_logs,
                            client_api=self.dataset._client_api)
        pbar = tqdm.tqdm(total=file_count)
        pool = ThreadPool(processes=6)
        i_item = 0

        for page in self.remote_items:
            for item in page:
                if from_format == AnnotationFormat.COCO:
                    found, ann_filepath, metadata = self._find_coco_item_annotations(
                        local_annotations_path=local_annotations_path,
                        item=item
                    )
                elif from_format in [AnnotationFormat.YOLO, AnnotationFormat.VOC]:
                    found, ann_filepath, metadata = self._find_yolo_voc_item_annotations(
                        local_annotations_path=local_annotations_path,
                        item=item,
                        from_format=from_format
                    )
                else:
                    raise exceptions.PlatformException('400', 'Unknown annotation format: {}'.format(from_format))
                if not found:
                    pbar.update()
                    reporter.set_index(ref=item.filename, status='skip', success=False,
                                       error='Cannot find annotations for item')
                    i_item += 1
                    continue
                pool.apply_async(
                    func=self._upload_item_and_convert,
                    kwds={
                        "from_format": from_format,
                        "item_path": item,
                        "ann_path": ann_filepath,
                        'conversion_func': None,
                        "reporter": reporter,
                        'i_item': i_item,
                        'pbar': pbar,
                        'metadata': metadata
                    }
                )
                i_item += 1
        pool.close()
        pool.join()
        pool.terminate()

        if reporter.has_errors:
            log_filepath = reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning(
                    'Converted with some errors. Please see log in {} for more information.'.format(log_filepath))

        logger.info('Total converted and uploaded: {}'.format(reporter.status_count('success')))
        logger.info('Total failed: {}'.format(reporter.status_count('failed')))

    def _upload_directory(self, local_items_path, local_annotations_path, from_format, conversion_func=None, **kwargs):
        """
        Convert annotation files in entire directory

        :param local_items_path:
        :param local_annotations_path:
        :param from_format:
        :param conversion_func:
        :return:
        """
        self._only_bbox = kwargs.get('only_bbox', False)
        file_count = sum(len([file for file in files if not file.endswith('.xml')]) for _, _, files in
                         os.walk(local_items_path))

        reporter = Reporter(num_workers=file_count,
                            resource=Reporter.CONVERTER,
                            print_error_logs=self.dataset._client_api.verbose.print_error_logs,
                            client_api=self.dataset._client_api)
        pbar = tqdm.tqdm(total=file_count)

        pool = ThreadPool(processes=6)
        i_item = 0
        metadata = None
        for path, subdirs, files in os.walk(local_items_path):
            for name in files:
                item_filepath = None
                ann_filepath = None
                if not os.path.isfile(os.path.join(path, name)):
                    continue
                if from_format == AnnotationFormat.COCO:
                    item_filepath = os.path.join(path, name)
                    ann_filepath = local_annotations_path[name]
                    metadata = {'user': local_annotations_path[name]['metadata']}
                elif from_format == AnnotationFormat.VOC:
                    if name.endswith('.xml'):
                        continue
                    else:
                        ext = os.path.splitext(name)[-1]
                        try:
                            m = mimetypes.types_map[ext.lower()]
                        except Exception:
                            m = ''

                        if ext == '' or ext is None or 'image' not in m:
                            continue

                    item_filepath = os.path.join(path, name)
                    ann_filepath = os.path.join(path, '.'.join(name.split('.')[0:-1] + ['xml'])).replace(
                        local_items_path, local_annotations_path)
                elif from_format == AnnotationFormat.YOLO:
                    item_filepath = os.path.join(path, name)
                    ann_filepath = os.path.join(path, os.path.splitext(name)[0]) + '.txt'
                    ann_filepath = ann_filepath.replace(local_items_path, local_annotations_path)
                pool.apply_async(
                    func=self._upload_item_and_convert,
                    kwds={
                        "from_format": from_format,
                        "item_path": item_filepath,
                        "ann_path": ann_filepath,
                        'conversion_func': conversion_func,
                        "reporter": reporter,
                        'i_item': i_item,
                        'pbar': pbar,
                        'metadata': metadata
                    }
                )
                i_item += 1
        pool.close()
        pool.join()
        pool.terminate()

        if reporter.has_errors:
            log_filepath = reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning(
                    'Converted with some errors. Please see log in {} for more information.'.format(log_filepath))

        logger.info('Total converted and uploaded: {}'.format(reporter.status_count('success')))
        logger.info('Total failed: {}'.format(reporter.status_count('failed')))

    def _upload_item_and_convert(self, item_path, ann_path, from_format, conversion_func=None, **kwargs):
        reporter = kwargs.get('reporter', None)
        i_item = kwargs.get('i_item', None)
        pbar = kwargs.get('pbar', None)
        metadata = kwargs.get('metadata', None)
        report_ref = item_path
        try:
            if isinstance(item_path, entities.Item):
                item = item_path
                report_ref = item.filename
            else:
                item = self.dataset.items.upload(local_path=item_path, item_metadata=metadata)
                report_ref = item.filename
            if from_format == AnnotationFormat.YOLO:
                item = Converter.__get_item_shape(item=item, local_path=item_path)
            annotations_list, errors = self.convert_file(to_format=AnnotationFormat.DATALOOP,
                                                         from_format=from_format,
                                                         item=item,
                                                         file_path=ann_path,
                                                         save_locally=False,
                                                         conversion_func=conversion_func,
                                                         upload=True,
                                                         pbar=pbar)
            if errors:
                if reporter is not None and i_item is not None:
                    reporter.set_index(ref=report_ref,
                                       status='warning',
                                       success=False,
                                       error='partial annotations upload: \n{}'.format(errors))
            else:
                if reporter is not None and i_item is not None:
                    reporter.set_index(status='success',
                                       success=True,
                                       ref=report_ref)
            if reporter is not None:
                self.__update_progress(total=reporter.num_workers, of_total=i_item)
        except Exception:
            if reporter is not None and i_item is not None:
                reporter.set_index(status='failed',
                                   success=False,
                                   error=traceback.format_exc(),
                                   ref=report_ref)

    def upload_local_dataset(self,
                             from_format,
                             dataset,
                             local_items_path=None,
                             local_labels_path=None,
                             local_annotations_path=None,
                             only_bbox=False,
                             filters=None,
                             remote_items=None
                             ):
        """
        Convert and Upload local dataset to dataloop platform

        :param remote_items:
        :param filters:
        :param only_bbox: only for coco datasets
        :param from_format:
        :param dataset:
        :param local_items_path:
        :param local_annotations_path:
        :param local_labels_path:
        :param local_items_path:
        :return:
        """
        if remote_items is None:
            remote_items = local_items_path is None

        if remote_items:
            logger.info('Getting remote items...')
            self.remote_items = dataset.items.list(filters=filters)

        self.dataset = dataset
        if from_format.lower() == AnnotationFormat.COCO:
            self._upload_coco_dataset(local_items_path=local_items_path, local_annotations_path=local_annotations_path,
                                      only_bbox=only_bbox, remote_items=remote_items)
        if from_format.lower() == AnnotationFormat.YOLO:
            self._upload_yolo_dataset(local_items_path=local_items_path, local_annotations_path=local_annotations_path,
                                      labels_file_path=local_labels_path, remote_items=remote_items)
        if from_format.lower() == AnnotationFormat.VOC:
            self._upload_voc_dataset(local_items_path=local_items_path, local_annotations_path=local_annotations_path,
                                     labels_file_path=local_labels_path, remote_items=remote_items)

    def convert_directory(self, local_path, to_format, from_format, dataset, conversion_func=None):
        """
        Convert annotation files in entire directory

        :param local_path:
        :param to_format:
        :param from_format:
        :param conversion_func:
        :param dataset:
        :return:
        """
        file_count = sum(len(files) for _, _, files in os.walk(local_path))
        reporter = Reporter(num_workers=file_count,
                            resource=Reporter.CONVERTER,
                            print_error_logs=self.dataset._client_api.verbose.print_error_logs,
                            client_api=self.dataset._client_api)
        self.dataset = dataset

        pool = ThreadPool(processes=6)
        i_item = 0
        for path, subdirs, files in os.walk(local_path):
            for name in files:
                save_to = os.path.join(os.path.split(local_path)[0], to_format)
                save_to = path.replace(local_path, save_to)
                if not os.path.isdir(save_to):
                    os.mkdir(save_to)
                file_path = os.path.join(path, name)
                pool.apply_async(
                    func=self._convert_and_report,
                    kwds={
                        "to_format": to_format,
                        "from_format": from_format,
                        "file_path": file_path,
                        "save_locally": True,
                        "save_to": save_to,
                        'conversion_func': conversion_func,
                        'reporter': reporter,
                        'i_item': i_item
                    }
                )
                i_item += 1
        pool.close()
        pool.join()
        pool.terminate()

        if reporter.has_errors:
            log_filepath = reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning(
                    'Converted with some errors. Please see log in {} for more information.'.format(log_filepath))

        logger.info('Total converted and uploaded: {}'.format(reporter.status_count('success')))
        logger.info('Total failed: {}'.format(reporter.status_count('failed')))

    def _convert_and_report(self, to_format, from_format, file_path, save_locally, save_to, conversion_func, reporter,
                            i_item):
        try:
            annotations_list, errors = self.convert_file(
                to_format=to_format,
                from_format=from_format,
                file_path=file_path,
                save_locally=save_locally,
                save_to=save_to,
                conversion_func=conversion_func
            )
            if errors:
                reporter.set_index(ref=file_path, status='warning', success=False,
                                   error='partial annotations upload')
            else:
                reporter.set_index(ref=file_path, status='success', success=True)
        except Exception:
            reporter.set_index(ref=file_path, status='failed', success=False,
                               error=traceback.format_exc())
            raise

    @staticmethod
    def _extract_annotations_from_file(file_path, from_format, item):
        item_id = None
        annotations = None
        if isinstance(file_path, dict):
            annotations = file_path['annotations']
        elif isinstance(file_path, str) and os.path.isfile(file_path):
            with open(file_path, "r") as f:
                if file_path.endswith(".json"):
                    annotations = json.load(f)
                    if from_format.lower() == AnnotationFormat.DATALOOP:
                        if item is None:
                            item_id = annotations.get('_id', annotations.get('id', None))
                        annotations = annotations["annotations"]
                elif from_format.lower() == AnnotationFormat.YOLO:
                    annotations = [[float(param.replace('\n', ''))
                                    for param in line.strip().split(' ')]
                                   for line in f.readlines()]
                elif file_path.endswith(".xml"):
                    annotations = Et.parse(f)
                    annotations = [e for e in annotations.iter('object')]
                else:
                    raise NotImplementedError('Unknown file format: {}'.format(file_path))
        else:
            raise NotImplementedError('Unknown file_path: {}'.format(file_path))

        return item_id, annotations

    def convert_file(self, to_format, from_format, file_path, save_locally=False, save_to=None, conversion_func=None,
                     item=None, pbar=None, upload=False, **_):
        """
        Convert file containing annotations

        :param to_format:
        :param from_format:
        :param file_path:
        :param pbar:
        :param upload:
        :param save_locally:
        :param save_to:
        :param conversion_func:
        :param item:
        :return:
        """
        item_id, annotations = self._extract_annotations_from_file(
            from_format=from_format,
            file_path=file_path,
            item=item
        )

        converted_annotations = self.convert(
            to_format=to_format,
            from_format=from_format,
            annotations=annotations,
            conversion_func=conversion_func,
            item=item
        )

        annotations_list, errors = self._sort_annotations(annotations=converted_annotations)

        if annotations_list:
            if save_locally:
                if item_id is not None:
                    item = self.dataset.items.get(item_id=item_id)
                filename = os.path.split(file_path)[-1]
                filename_no_ext = os.path.splitext(filename)[0]
                save_to = os.path.join(save_to, filename_no_ext)
                self.save_to_file(save_to=save_to, to_format=to_format, annotations=annotations_list, item=item)
            elif upload and to_format == AnnotationFormat.DATALOOP:
                item.annotations.upload(annotations=annotations_list)

        if pbar is not None:
            pbar.update()

        return annotations_list, errors

    @staticmethod
    def _sort_annotations(annotations):
        errors = list()
        success = list()

        for ann in annotations:
            if isinstance(ann, str) and 'Error converting annotation' in ann:
                errors.append(ann)
            else:
                success.append(ann)

        return success, errors

    def save_to_file(self, save_to, to_format, annotations, item=None):
        """
        Save annotations to a file

        :param save_to:
        :param to_format:
        :param annotations:
        :param item:
        :return:
        """
        # what file format
        if self.save_to_format is None:
            if to_format.lower() in [AnnotationFormat.DATALOOP, AnnotationFormat.COCO]:
                self.save_to_format = 'json'
            elif to_format.lower() in [AnnotationFormat.YOLO]:
                self.save_to_format = 'txt'
            else:
                self.save_to_format = 'xml'

        # save
        # JSON #
        if self.save_to_format == 'json':
            # save json
            save_to = save_to + '.json'
            with open(save_to, "w") as f:
                json.dump(annotations, f, indent=2)

        # TXT #
        elif self.save_to_format == 'txt':
            # save txt
            save_to = save_to + '.txt'
            with open(save_to, "w") as f:
                for ann in annotations:
                    if ann is not None:
                        f.write(' '.join([str(x) for x in ann]) + '\n')

        # XML #
        elif self.save_to_format == 'xml':
            item = Converter.__get_item_shape(item=item)
            output_annotation = {
                'path': item.filename,
                'filename': os.path.basename(item.filename),
                'folder': os.path.basename(os.path.dirname(item.filename)),
                'width': item.width,
                'height': item.height,
                'depth': 3,
                'database': 'Unknown',
                'segmented': 0,
                'objects': annotations
            }
            save_to = save_to + '.xml'
            environment = Environment(loader=PackageLoader('dtlpy', 'assets'),
                                      keep_trailing_newline=True)
            annotation_template = environment.get_template(self.xml_template_path)
            with open(save_to, 'w') as file:
                content = annotation_template.render(**output_annotation)
                file.write(content)
        else:
            raise exceptions.PlatformException('400', 'Unknown file format to save to')

    def _check_formats(self, from_format, to_format, conversion_func):
        if from_format.lower() not in self.known_formats and conversion_func is None:
            raise exceptions.PlatformException(
                "400",
                "Unknown annotation format: {}, possible formats: {}".format(
                    from_format, self.known_formats
                ),
            )
        if to_format.lower() not in self.known_formats and conversion_func is None:
            raise exceptions.PlatformException(
                "400",
                "Unknown annotation format: {}, possible formats: {}".format(
                    to_format, self.known_formats
                ),
            )

    def convert(self, annotations, from_format, to_format, conversion_func=None, item=None):
        """
        Convert annotations list or single annotation

        :param item:
        :param annotations:
        :param from_format:
        :param to_format:
        :param conversion_func:
        :return:
        """
        # check known format
        self._check_formats(from_format=from_format, to_format=to_format, conversion_func=conversion_func)

        # check annotations param type
        if isinstance(annotations, entities.AnnotationCollection):
            annotations = annotations.annotations
        if not isinstance(annotations, list):
            annotations = [annotations]

        if AnnotationFormat.DATALOOP not in [to_format, from_format]:
            raise exceptions.PlatformException(
                "400", "Can only convert from or to dataloop format"
            )

        # call method
        if conversion_func is None:
            if from_format == AnnotationFormat.DATALOOP:
                method = self.converter_dict[to_format]["to"]
            else:
                method = self.converter_dict[from_format]["from"]
        else:
            method = self.custom_format

        # run all annotations
        pool = ThreadPool(processes=6)
        for i_annotation, annotation in enumerate(annotations):
            pool.apply_async(
                func=self._convert_single,
                kwds={
                    "annotation": annotation,
                    "i_annotation": i_annotation,
                    "conversion_func": conversion_func,
                    'annotations': annotations,
                    'from_format': AnnotationFormat.DATALOOP,
                    'item': item,
                    'method': method
                }
            )

        pool.close()
        pool.join()
        pool.terminate()
        return annotations

    @staticmethod
    def _convert_single(method, **kwargs):
        annotations = kwargs.get('annotations', None)
        i_annotation = kwargs.get('i_annotation', None)
        try:
            ann = method(**kwargs)
            if annotations is not None and isinstance(i_annotation, int):
                annotations[i_annotation] = ann
        except Exception:
            if annotations is not None and isinstance(i_annotation, int):
                annotations[i_annotation] = 'Error converting annotation: {}'.format(traceback.format_exc())
            else:
                raise

    @staticmethod
    def from_voc(annotation, **_):
        bndbox = annotation.find('bndbox')

        if bndbox is None:
            raise Exception('No bndbox field found in annotation object')

        bottom = float(bndbox.find('ymax').text)
        top = float(bndbox.find('ymin').text)
        left = float(bndbox.find('xmin').text)
        right = float(bndbox.find('xmax').text)
        label = annotation.find('name').text

        if annotation.find('segmented'):
            if annotation.find('segmented') == '1':
                logger.warning('Only bounding box conversion is supported in voc format. Segmentation will be ignored.')

        attributes = list(annotation)
        attrs = list()
        for attribute in attributes:
            if attribute.tag not in ['bndbox', 'name'] and len(list(attribute)) == 0:
                if attribute.text not in ['0', '1']:
                    attrs.append(attribute.text)
                elif attribute.text == '1':
                    attrs.append(attribute.tag)

        ann_def = entities.Box(label=label, top=top, bottom=bottom, left=left, right=right, attributes=attrs)
        return entities.Annotation.new(annotation_definition=ann_def)

    def from_yolo(self, annotation, item=None, **kwargs):
        (label_id, x, y, w, h) = annotation
        label_id = int(label_id)

        item = Converter.__get_item_shape(item=item)
        height = kwargs.get('height', None)
        width = kwargs.get('width', None)

        if height is None or width is None:
            if item is None or item.width is None or item.height is None:
                raise Exception('Need item width and height in order to convert yolo annotation to dataloop')
            height = item.height
            width = item.width

        x_center = x * width
        y_center = y * height
        w = w * width
        h = h * height

        top = y_center - (h / 2)
        bottom = y_center + (h / 2)
        left = x_center - (w / 2)
        right = x_center + (w / 2)

        label = self._label_by_category_id(category_id=label_id)

        ann_def = entities.Box(label=label, top=top, bottom=bottom, left=left, right=right)
        return entities.Annotation.new(annotation_definition=ann_def, item=item)

    def to_yolo(self, annotation, item=None, **_):
        if not isinstance(annotation, entities.Annotation):
            if item is None:
                item = self.dataset.items.get(item_id=annotation['itemId'])
            annotation = entities.Annotation.from_json(_json=annotation, item=item)
        elif item is None:
            item = annotation.item

        if annotation.type != "box":
            raise Exception('Only box annotations can be converted')

        item = Converter.__get_item_shape(item=item)

        if item is None or item.width is None or item.height is None:
            raise Exception("Cannot get item's width and height")

        width, height = (item.width, item.height)
        if item.system.get('exif', {}).get('Orientation', 0) in [5, 6, 7, 8]:
            width, height = (item.height, item.width)

        dw = 1.0 / width
        dh = 1.0 / height
        x = (annotation.left + annotation.right) / 2.0
        y = (annotation.top + annotation.bottom) / 2.0
        w = annotation.right - annotation.left
        h = annotation.bottom - annotation.top
        x = x * dw
        w = w * dw
        y = y * dh
        h = h * dh

        label_id = self.labels[annotation.label]

        ann = (label_id, x, y, w, h)
        return ann

    def _label_by_category_id(self, category_id):
        if len(self.labels) > 0:
            for label_name, label_index in self.labels.items():
                if label_index == category_id:
                    return label_name
        raise Exception('label category id not found: {}'.format(category_id))

    def from_coco(self, annotation, **kwargs):
        item = kwargs.get('item', None)
        _id = annotation.get('id', None)
        category_id = annotation.get('category_id', None)
        segmentation = annotation.get('segmentation', None)
        iscrowd = annotation.get('iscrowd', None)
        label = self._label_by_category_id(category_id=category_id)

        if hasattr(self, '_only_bbox') and self._only_bbox:
            bbox = annotation.get('bbox', None)
            left = bbox[0]
            top = bbox[1]
            right = left + bbox[2]
            bottom = top + bbox[3]

            ann_def = entities.Box(top=top, left=left, bottom=bottom, right=right, label=label)
        else:
            if iscrowd is not None and int(iscrowd) == 1:
                ann_def = entities.Segmentation(label=label, geo=COCOUtils.rle_to_binary_mask(rle=segmentation))
            else:
                if len(segmentation) == 1:
                    segmentation = segmentation[0]
                    if segmentation:
                        ann_def = entities.Polygon(label=label,
                                                   geo=COCOUtils.rle_to_binary_polygon(segmentation=segmentation))
                    else:
                        bbox = annotation.get('bbox', None)
                        if bbox:
                            left = bbox[0]
                            top = bbox[1]
                            right = left + bbox[2]
                            bottom = top + bbox[3]
                            ann_def = entities.Box(top=top, left=left, bottom=bottom, right=right, label=label)
                        else:
                            raise Exception('Unable to convert annotation, not coordinates')

                else:
                    # TODO - support conversion of split annotations
                    raise exceptions.PlatformException('400',
                                                       'unable to convert.'
                                                       'Converter does not support split annotations: {}'.format(
                                                           _id))

        return entities.Annotation.new(annotation_definition=ann_def, item=item)

    @staticmethod
    def to_coco(annotation, item=None, **_):
        item = Converter.__get_item_shape(item=item)
        height = item.height if item is not None else None
        width = item.width if item is not None else None

        if not isinstance(annotation, entities.Annotation):
            annotation = entities.Annotation.from_json(annotation, item=item)
        area = 0
        iscrowd = 0
        segmentation = [[]]
        if annotation.type == 'polyline':
            raise Exception('Unable to convert annotation of type "polyline" to coco')

        if annotation.type in ['binary', 'segment']:
            if height is None or width is None:
                raise Exception(
                    'Item must have height and width to convert {!r} annotation to coco'.format(annotation.type))

        # build annotation
        keypoints = None
        if annotation.type in ['binary', 'box', 'segment', 'pose']:
            x = annotation.left
            y = annotation.top
            w = annotation.right - x
            h = annotation.bottom - y
            if annotation.type == 'binary':
                # segmentation = COCOUtils.binary_mask_to_rle(binary_mask=annotation.geo, height=height, width=width)
                segmentation = COCOUtils.binary_mask_to_rle_encode(binary_mask=annotation.geo)
                area = int(annotation.geo.sum())
                iscrowd = 1
            elif annotation.type in ['segment']:
                segmentation, area = COCOUtils.polygon_to_rle(geo=annotation.geo, height=height, width=width)
            elif annotation.type == 'pose':
                keypoints = list()
                for point in annotation.annotation_definition.points:
                    keypoints.append(point.x)
                    keypoints.append(point.y)
                    if isinstance(point.attributes, list):
                        if 'visible' in point.attributes and \
                                ("not-visible" in point.attributes or 'not_visible' in point.attributes):
                            keypoints.append(0)
                        elif 'not-visible' in point.attributes or 'not_visible' in point.attributes:
                            keypoints.append(1)
                        elif 'visible' in point.attributes:
                            keypoints.append(2)
                        else:
                            keypoints.append(0)
                    else:
                        list_attributes = list(point.attributes.values())
                        if 'Visible' in list_attributes:
                            keypoints.append(2)
                        else:
                            keypoints.append(0)

        else:
            raise Exception('Unable to convert annotation of type {} to coco'.format(annotation.type))

        ann = dict()
        ann['bbox'] = [float(x), float(y), float(w), float(h)]
        ann["segmentation"] = segmentation
        ann["area"] = area
        ann["iscrowd"] = iscrowd
        if keypoints is not None:
            ann["keypoints"] = keypoints
        return ann

    @staticmethod
    def to_voc(annotation, item=None, **_):
        if not isinstance(annotation, entities.Annotation):
            annotation = entities.Annotation.from_json(annotation, item=item)

        if annotation.type != 'box':
            raise exceptions.PlatformException('400', 'Annotation must be of type box')

        label = annotation.label

        if annotation.attributes is not None and isinstance(annotation.attributes, list) and len(
                annotation.attributes) > 0:
            attributes = annotation.attributes
        else:
            attributes = list()

        left = annotation.left
        top = annotation.top
        right = annotation.right
        bottom = annotation.bottom

        ann = {'name': label,
               'xmin': left,
               'ymin': top,
               'xmax': right,
               'ymax': bottom,
               'attributes': attributes,
               }

        return ann

    @staticmethod
    def custom_format(annotation, conversion_func, i_annotation=None, annotations=None, from_format=None,
                      item=None, **_):
        if from_format == AnnotationFormat.DATALOOP and isinstance(annotation, dict):
            annotation = entities.Annotation.from_json(_json=annotation, item=item)

        ann = conversion_func(annotation, item)

        if isinstance(annotations[i_annotation], entities.Annotation) and annotations[i_annotation].item is None:
            ann.item = item

        return ann
