from multiprocessing.pool import ThreadPool
import os
import json
import pickle
from .. import exceptions, entities, utilities
from jinja2 import Environment, PackageLoader


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

    def convert_dataset(self, dataset, to_format, local_path, conversion_func=None, filters=None):
        """
        Convert entire dataset

        :param dataset:
        :param to_format:
        :param local_path:
        :param conversion_func: Custom conversion function
        :param filters: optional
        :return:
        """
        assert isinstance(dataset, entities.Dataset)
        self.dataset = dataset

        # download annotations
        dataset.download_annotations(local_path=local_path, overwrite=True)
        local_annotations_path = os.path.join(local_path, "json")
        output_annotations_path = os.path.join(local_path, to_format)
        pool = ThreadPool(processes=6)
        i_item = 0
        pages = dataset.items.list(filters=filters)
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
                pool.apply_async(
                    func=converter.convert_file,
                    kwds={
                        "to_format": to_format,
                        "from_format": 'dataloop',
                        "file_path": in_filepath,
                        "save_locally": True,
                        "save_to": save_to,
                        'conversion_func': conversion_func,
                        'item': item
                    }
                )
        pool.close()
        pool.join()
        pool.terminate()

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
                     item=None):
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
            to_format=to_format, from_format=from_format, annotations=annotations, conversion_func=conversion_func
        )
        if save_locally:
            if item_id is not None:
                item = self.dataset.items.get(item_id=item_id)
            filename = os.path.split(file_path)[-1]
            filename_no_ext = os.path.splitext(filename)[0]
            save_to = os.path.join(save_to, filename_no_ext)
            self.save_to_file(save_to=save_to, to_format=to_format, annotations=converted_annotations, item=item)

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
                json.dump(annotations, f)

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
            annotation_template = environment.get_template('voc_annotation_template.xml')
            with open(save_to, 'w') as file:
                content = annotation_template.render(**output_annotation)
                file.write(content)
        else:
            raise exceptions.PlatformException('400', 'Unknown file format to save to')

    def convert(self, annotations, from_format, to_format, conversion_func=None):
        """
        Convert annotations list or single annotation

        :param annotations:
        :param from_format:
        :param to_format:
        :param conversion_func:
        :return:
        """
        # check params
        assert isinstance(from_format, str)
        assert isinstance(to_format, str)

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

        # fix and save annotations globally
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
            )
        elif to_format == "dataloop":
            converted_annotations = self.to_dataloop(
                annotations=annotations,
                from_format=from_format.lower(),
                conversion_func=conversion_func,
            )
        else:
            raise exceptions.PlatformException(
                "400", "Can only convert from or to dataloop format"
            )

        return converted_annotations

    def to_dataloop(self, annotations, from_format, conversion_func=None):
        pool = ThreadPool(processes=32)
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

    def from_dataloop(self, annotations, to_format, conversion_func=None):
        pool = ThreadPool(processes=32)
        for i_annotation, annotation in enumerate(annotations):
            if conversion_func is None:
                pool.apply_async(
                    func=self.converter_dict[to_format]["to"],
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

    def from_coco(self, annotation, i_annotation, annotations=None):
        pass

    def from_voc(self, annotation, i_annotation, annotations=None):
        pass

    def from_yolo(self, annotation, i_annotation, annotations=None):
        pass

    def to_yolo(self, annotation, i_annotation, annotations=None):
        if not isinstance(annotation, entities.Annotation):
            if self.item is None:
                self.item = self.dataset.items.get(item_id=annotation['itemId'])
            annotation = entities.Annotation.from_json(_json=annotation, item=self.item)
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

    @staticmethod
    def to_coco(annotation, i_annotation, annotations=None):
        if not isinstance(annotation, entities.Annotation):
            annotation = entities.Annotation.from_json(annotation)
        # create segmentation list
        segmentation = list()
        counter = 0
        area = 0
        in_segment = False
        for row in annotation.geo:
            for cell in row:
                if cell == 0:
                    if in_segment:
                        in_segment = False
                        segmentation.append(counter)
                        counter = 0
                    else:
                        counter += 1
                else:
                    area += 1
                    if in_segment:
                        counter += 1
                    else:
                        in_segment = True
                        segmentation.append(counter)
                        counter = 0

        # build annotation
        ann = dict()
        ann["segmenation"] = [segmentation]
        ann["area"] = area

        # put converted annotation in self annotation
        annotations[i_annotation] = ann

    @staticmethod
    def to_voc(annotation, i_annotation, annotations=None):
        if not isinstance(annotation, entities.Annotation):
            annotation = entities.Annotation.from_json(annotation)

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

    def custom_format(self, annotation, i_annotation, conversion_func, annotations=None):
        annotations[i_annotation] = conversion_func(annotation)
        if isinstance(annotations[i_annotation], entities.Annotation) and annotations[i_annotation].item is None:
            annotations[i_annotation].item = self.item
