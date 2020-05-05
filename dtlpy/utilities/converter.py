import copy
import traceback
from itertools import groupby
from multiprocessing.pool import ThreadPool
import os
import json
import tqdm
import pickle
from .. import exceptions, entities, utilities
from jinja2 import Environment, PackageLoader
import numpy as np
import logging

logger = logging.getLogger(name=__name__)


class Converter:
    """
    Annotation Converter
    """

    def __init__(self):
        self.known_formats = ["yolo", "coco", "voc", "dataloop"]
        self.converter_dict = {
            "yolo": {"from": self.from_yolo, "to": self.to_yolo},
            "coco": {"from": self.from_coco, "to": self.to_coco},
            "voc": {"from": self.from_voc, "to": self.to_voc},
        }
        self.dataset = None
        self.item = None
        self.save_to_format = None
        self.xml_template_path = 'voc_annotation_template.xml'

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
        if to_format.lower() == 'coco':
            return self.__convert_dataset_to_coco(dataset=dataset,
                                                  local_path=local_path,
                                                  filters=filters,
                                                  annotation_filter=annotation_filter)
        num_workers = 6
        assert isinstance(dataset, entities.Dataset)
        self.dataset = dataset

        # download annotations
        if annotation_filter is None:
            dataset.download_annotations(local_path=local_path, overwrite=True)
        local_annotations_path = os.path.join(local_path, "json")
        output_annotations_path = os.path.join(local_path, to_format)
        pool = ThreadPool(processes=num_workers)
        i_item = 0
        pages = dataset.items.list(filters=filters)

        # if yolo - create labels file
        if to_format == 'yolo':
            labels = [label.tag for label in dataset.labels]
            with open('{}/{}.names'.format(local_path, dataset.name), 'w') as fp:
                for label in labels:
                    fp.write("{}\n".format(label))

        pbar = tqdm.tqdm(total=pages.items_count)
        for page in pages:
            for item in page:
                i_item += 1
                # create input annotations json
                in_filepath = os.path.join(local_annotations_path, item.filename[1:])
                name, ext = os.path.splitext(in_filepath)
                in_filepath = name + '.json'

                save_to = os.path.dirname(in_filepath.replace(local_annotations_path, output_annotations_path))

                if not os.path.isdir(save_to):
                    os.makedirs(save_to, exist_ok=True)

                converter = utilities.Converter()
                converter.dataset = self.dataset
                converter.save_to_format = self.save_to_format
                converter.xml_template_path = self.xml_template_path

                if annotation_filter is None:
                    method = converter.convert_file
                else:
                    method = converter.__save_filtered_annotations_and_convert

                pool.apply_async(
                    func=method,
                    kwds={
                        "to_format": to_format,
                        "from_format": 'dataloop',
                        "file_path": in_filepath,
                        "save_locally": True,
                        "save_to": save_to,
                        'conversion_func': conversion_func,
                        'item': item,
                        'pbar': pbar,
                        'filters': annotation_filter
                    }
                )
        pool.close()
        pool.join()
        pool.terminate()
        pbar.close()

    def __save_filtered_annotations_and_convert(self, item, filters, to_format, from_format, file_path,
                                                save_locally=False,
                                                save_to=None, conversion_func=None,
                                                pbar=None):
        if item.annotated:
            assert filters.resource == 'annotations'
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
            self.convert_file(item=item, to_format=to_format, from_format=from_format, file_path=file_path,
                              save_locally=save_locally,
                              save_to=save_to, conversion_func=conversion_func,
                              pbar=pbar)

    @staticmethod
    def _binary_mask_to_rle(binary_mask):
        size = np.sum(binary_mask > 0)
        rle = {'counts': [], 'size': size}
        counts = rle.get('counts')
        for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
            if i == 0 and value == 1:
                counts.append(0)
            counts.append(len(list(elements)))
        return rle

    def __convert_dataset_to_coco(self, dataset: entities.Dataset, local_path, filters=None, annotation_filter=None):
        pages = dataset.items.list(filters=filters)
        dataset.download_annotations(local_path=local_path)
        path_to_dataloop_annotations_dir = os.path.join(local_path, 'json')

        labels = [label.tag for label in dataset.labels]
        np_labels = np.array(labels)
        class_list = np.unique(np_labels)

        label_to_id = {name: i for i, name in enumerate(class_list) if name not in ["done", 'completed', 'approved']}
        categories = [{'id': i, 'name': name} for name, i in label_to_id.items()]

        images = [None for _ in range(pages.items_count)]
        converted_annotations = [None for _ in range(pages.items_count)]
        item_id_counter = 0
        pool = ThreadPool(processes=11)
        pbar = tqdm.tqdm(total=pages.items_count)
        for page in pages:
            for item in page:
                pool.apply_async(func=self.__single_item_to_coco,
                                 kwds={
                                     'item': item,
                                     'images': images,
                                     'path_to_dataloop_annotations_dir': path_to_dataloop_annotations_dir,
                                     'item_id': item_id_counter,
                                     'converted_annotations': converted_annotations,
                                     'annotation_filter': annotation_filter,
                                     'label_to_id': label_to_id,
                                     'pbar': pbar
                                 })
                item_id_counter += 1

        pool.close()
        pool.join()
        pool.terminate()
        pbar.close()

        total_converted_annotations = list()
        for ls in converted_annotations:
            if ls is not None:
                total_converted_annotations += ls

        coco_json = {'images': [image for image in images if image is not None],
                     'annotations': total_converted_annotations,
                     'categories': categories}

        with open(os.path.join(local_path, 'coco.json'), 'w+') as f:
            json.dump(coco_json, f)

        return coco_json

    def __single_item_to_coco(self, item, images, path_to_dataloop_annotations_dir, item_id, converted_annotations,
                              annotation_filter, label_to_id, pbar=None):
        images[item_id] = {'file_name': item.filename,
                           'id': item_id,
                           'width': item.width,
                           'height': item.height
                           }
        if annotation_filter is None:
            try:
                filename, ext = os.path.splitext(item.filename)
                filename = '{}.json'.format(filename[1:])
                with open(os.path.join(path_to_dataloop_annotations_dir, filename), 'r') as f:
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
        for i_annotation, annotation in enumerate(annotations.annotations):
            try:
                if annotation.type in ['binary', 'segment']:
                    if annotation.type == 'segment':
                        annotation_def = entities.Segmentation.from_polygon(geo=annotation.geo, label=annotation.label,
                                                                            attributes=annotation.attributes,
                                                                            shape=(item.height, item.width),
                                                                            is_open=annotation.is_open)
                        annotation = entities.Annotation.new(item=item, annotation_definition=annotation_def)
                    rle = self._binary_mask_to_rle(annotation.geo)
                    segmentation = [rle['counts']]
                    area = float(rle['size'])
                    x = annotation.left
                    y = annotation.bottom
                    w = annotation.right - x
                    h = annotation.top - y
                elif annotation.type == 'box':
                    x = annotation.coordinates[0]['x']
                    y = annotation.coordinates[0]['y']
                    w = annotation.coordinates[1]['x'] - x
                    h = annotation.coordinates[1]['y'] - y
                    segmentation = [[0]]
                    area = float(h * w)
                else:
                    logger.error('Unable to convert annotation of type {} to coco'.format(annotation.type))
                    continue

                converted_ann = {'bbox': [float(x), float(y),float(w), float(h)],
                                 'segmentation': segmentation,
                                 'area': area,
                                 'category_id': label_to_id[annotation.label],
                                 'image_id': item_id,
                                 'iscrowd': 0,
                                 'id': i_annotation
                                 }
                item_converted_annotations.append(converted_ann)
                converted_annotations[item_id] = item_converted_annotations
            except Exception:
                logger.exception('Item: {}, annotation: {} - fail to convert annotation')

        if pbar is not None:
            pbar.update()

    def convert_directory(self, local_path, to_format, from_format, conversion_func=None, dataset=None):
        """
        Convert annotation files in entire directory

        :param local_path:
        :param to_format:
        :param from_format:
        :param conversion_func:
        :param dataset:
        :return:
        """
        pool = ThreadPool(processes=6)
        for path, subdirs, files in os.walk(local_path):
            for name in files:
                save_to = os.path.join(os.path.split(local_path)[0], to_format)
                save_to = path.replace(local_path, save_to)
                if not os.path.isdir(save_to):
                    os.mkdir(save_to)
                file_path = os.path.join(path, name)
                converter = utilities.Converter()
                if dataset is None:
                    converter.dataset = self.dataset
                else:
                    converter.dataset = dataset
                converter.save_to_format = self.save_to_format
                pool.apply_async(
                    func=converter.convert_file,
                    kwds={
                        "to_format": to_format,
                        "from_format": from_format,
                        "file_path": file_path,
                        "save_locally": True,
                        "save_to": save_to,
                        'conversion_func': conversion_func
                    }
                )
        pool.close()
        pool.join()
        pool.terminate()

    def convert_file(self, to_format, from_format, file_path, save_locally=False, save_to=None, conversion_func=None,
                     item=None, pbar=None, filters=None):
        """
        Convert file containing annotations

        :param to_format:
        :param from_format:
        :param file_path:
        :param save_locally:
        :param save_to:
        :param conversion_func:
        :param item:
        :return:
        """
        item_id = None
        with open(file_path, "r") as f:
            if file_path.endswith(".json"):
                annotations = json.load(f)
                if from_format.lower() == "dataloop":
                    if item is None:
                        item_id = annotations.get('_id', annotations.get('id', None))
                    annotations = annotations["annotations"]
            elif to_format.lower() == 'yolo':
                annotations = pickle.load(f)
            else:
                annotations = list()
                # TODO -  implement xml formats

        converted_annotations = self.convert(
            to_format=to_format,
            from_format=from_format,
            annotations=annotations,
            conversion_func=conversion_func,
            item=item
        )
        if save_locally:
            if item_id is not None:
                item = self.dataset.items.get(item_id=item_id)
            filename = os.path.split(file_path)[-1]
            filename_no_ext = os.path.splitext(filename)[0]
            save_to = os.path.join(save_to, filename_no_ext)
            self.save_to_file(save_to=save_to, to_format=to_format, annotations=converted_annotations, item=item)

        if pbar is not None:
            pbar.update()
        return converted_annotations

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
            if to_format.lower() in ["dataloop", "coco"]:
                self.save_to_format = 'json'
            elif to_format.lower() in ['yolo']:
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

        # check annotations param type
        if isinstance(annotations, entities.AnnotationCollection):
            annotations = annotations.annotations
        if not isinstance(annotations, list):
            annotations = [annotations]

        # call method
        if from_format == "dataloop":
            converted_annotations = self.from_dataloop(
                annotations=annotations,
                to_format=to_format.lower(),
                conversion_func=conversion_func,
                item=item
            )
        elif to_format == "dataloop":
            converted_annotations = self.to_dataloop(
                annotations=annotations,
                from_format=from_format.lower(),
                conversion_func=conversion_func
            )
        else:
            raise exceptions.PlatformException(
                "400", "Can only convert from or to dataloop format"
            )

        return converted_annotations

    def to_dataloop(self, annotations, from_format, conversion_func=None):
        pool = ThreadPool(processes=6)
        for i_annotation, annotation in enumerate(annotations):
            if conversion_func is None:
                pool.apply_async(
                    func=self.converter_dict[from_format]["from"],
                    kwds={"annotation": annotation, "i_annotation": i_annotation, 'annotations': annotations},
                )
            else:
                pool.apply_async(
                    func=self.custom_format,
                    kwds={
                        "annotation": annotation,
                        "i_annotation": i_annotation,
                        "conversion_func": conversion_func,
                        'annotations': annotations
                    },
                )
        pool.close()
        pool.join()
        pool.terminate()
        return annotations

    def from_dataloop(self, annotations, to_format, conversion_func=None, item=None):
        pool = ThreadPool(processes=6)
        for i_annotation, annotation in enumerate(annotations):
            if conversion_func is None:
                pool.apply_async(
                    func=self.converter_dict[to_format]["to"],
                    kwds={"annotation": annotation,
                          "i_annotation": i_annotation,
                          'annotations': annotations,
                          'item': item}
                )
            else:
                pool.apply_async(
                    func=self.custom_format,
                    kwds={
                        "annotation": annotation,
                        "i_annotation": i_annotation,
                        "conversion_func": conversion_func,
                        'annotations': annotations,
                        'from_format': 'dataloop'
                    },
                )
        pool.close()
        pool.join()
        pool.terminate()
        return annotations

    def from_coco(self, annotation, i_annotation, annotations=None):
        pass

    def from_voc(self, annotation, i_annotation, annotations=None):
        pass

    def from_yolo(self, annotation, i_annotation, annotations=None):
        pass

    def to_yolo(self, annotation, i_annotation, annotations=None, item=None):
        try:
            if not isinstance(annotation, entities.Annotation):
                if item is None:
                    if self.item is None:
                        self.item = self.dataset.items.get(item_id=annotation['itemId'])
                    else:
                        item = self.item
                annotation = entities.Annotation.from_json(_json=annotation, item=item)
            if annotation.type != "box":
                annotations[i_annotation] = None
                raise exceptions.PlatformException(
                    "400", "Only box annotation ca be converted to Yolo"
                )

            dw = 1.0 / annotation.item.width
            dh = 1.0 / annotation.item.height
            x = (annotation.left + annotation.right) / 2.0
            y = (annotation.top + annotation.bottom) / 2.0
            w = annotation.right - annotation.left
            h = annotation.bottom - annotation.top
            x = x * dw
            w = w * dw
            y = y * dh
            h = h * dh

            labels = {label.tag: i_label for i_label, label in enumerate(self.dataset.labels)}
            label_id = labels[annotation.label]

            annotations[i_annotation] = (label_id, x, y, w, h)
        except Exception:
            annotations[i_annotation] = 'Error converting annotation: {}'.format(traceback.format_exc())

    def to_coco(self, annotation, i_annotation, annotations=None, item=None):
        try:
            if not isinstance(annotation, entities.Annotation):
                annotation = entities.Annotation.from_json(annotation, item=item)
            # create segmentation list
            rle = self._binary_mask_to_rle(annotation.geo)

            # build annotation
            if annotation.type == 'binary':
                segmentation = [rle['counts']]
                x = annotation.left
                y = annotation.bottom
                w = annotation.right - x
                h = annotation.top - y
            elif annotation.type == 'box':
                x = annotation.coordinates[0]['x']
                y = annotation.coordinates[0]['y']
                w = annotation.coordinates[1]['x'] - x
                h = annotation.coordinates[1]['y'] - y
                segmentation = [[]]
            else:
                logger.error('Unable to convert annotation of type {} to coco'.format(annotation.type))
                raise Exception('Unable to convert annotation of type {} to coco'.format(annotation.type))

            ann = dict()
            ann['bbox'] = [x, y, w, h],
            ann["segmentation"] = segmentation
            ann["area"] = rle['size']

            # put converted annotation in self annotation
            annotations[i_annotation] = ann
        except Exception:
            annotations[i_annotation] = 'Error converting annotation: {}'.format(traceback.format_exc())

    @staticmethod
    def to_voc(annotation, i_annotation, annotations=None, item=None):
        try:
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

            annotations[i_annotation] = ann
        except Exception:
            annotations[i_annotation] = 'Error converting annotation: {}'.format(traceback.format_exc())

    def custom_format(self, annotation, i_annotation, conversion_func, annotations=None, from_format=None):
        if from_format == 'dataloop' and isinstance(annotation, dict):
            client_api = None
            if self.item is not None:
                client_api = self.item._client_api
            annotation = entities.Annotation.from_json(_json=annotation, item=self.item, client_api=client_api)

        annotations[i_annotation] = conversion_func(annotation)
        if isinstance(annotations[i_annotation], entities.Annotation) and annotations[i_annotation].item is None:
            annotations[i_annotation].item = self.item
