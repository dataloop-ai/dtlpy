import dtlpy as dl
from multiprocessing.pool import ThreadPool
import os
import json
import pickle


class Converter:
    def __init__(self):
        self.known_formats = ["yolo", "coco", "voc", "dataloop"]
        self.annotations = None
        self.converter_dict = {
            "yolo": {"from": self.from_yolo, "to": self.to_yolo},
            "coco": {"from": self.from_coco, "to": self.to_coco},
            "voc": {"from": self.from_voc, "to": self.to_voc},
        }
        self.dataset = None
        self.item = None
        self.save_to_format = None

    def convert_dataset(self, dataset, to_format, local_path, conversion_func=None):
        assert isinstance(dataset, dl.entities.Dataset)
        self.dataset = dataset

        # download annnotations
        dataset.download_annotations(local_path=local_path, overwrite=True)
        annotations_path = os.path.join(local_path, "json")
        self.convert_directory(from_format='dataloop', to_format=to_format,
                               local_path=annotations_path, conversion_func=conversion_func)

    def convert_directory(self, local_path, to_format, from_format, conversion_func=None, dataset=None):
        pool = ThreadPool(processes=6)
        for path, subdirs, files in os.walk(local_path):
            for name in files:
                save_to = os.path.join(os.path.split(local_path)[0], to_format)
                save_to = path.replace(local_path, save_to)
                if not os.path.isdir(save_to):
                    os.mkdir(save_to)
                file_path = os.path.join(path, name)
                converter = dl.Converter()
                converter.dataset = self.dataset
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

    def convert_file(
            self, to_format, from_format, file_path, save_locally=False, save_to=None, conversion_func=None
    ):
        with open(file_path, "r") as f:
            if file_path.endswith(".json"):
                annotations = json.load(f)
                if from_format.lower() == "dataloop":
                    annotations = annotations["annotations"]
            elif to_format.lower() == 'yolo':
                annotations = pickle.load(f)
            else:
                annotations = list()
                # TODO -  implement xml formats

        self.convert(
            to_format=to_format, from_format=from_format, annotations=annotations, conversion_func=conversion_func
        )
        if save_locally:
            save_to = os.path.join(save_to, os.path.split(file_path)[-1])
            self.save_to_file(save_to=save_to, to_format=to_format)

        return self.annotations

    def save_to_file(self, save_to, to_format):

        # what file format
        if self.save_to_format is None:
            if to_format.lower() in ["dataloop", "coco"]:
                self.save_to_format = 'json'
            elif to_format.lower() in ['yolo']:
                self.save_to_format = 'txt'
            else:
                self.save_to_format = 'xml'

        # save
        if self.save_to_format == 'json':
            # save json
            save_to = save_to + '.json'
            with open(save_to, "w") as f:
                json.dump(self.annotations, f)
        elif self.save_to_format == 'txt':
            # save txt
            save_to = save_to + '.txt'
            with open(save_to, "w") as f:
                for ann in self.annotations:
                    if ann is not None:
                        f.write(' '.join([str(x) for x in ann]) + '\n')
        elif self.save_to_format == 'xml':
            pass
            # TODO -  implement xml formats
        else:
            raise dl.PlatformException('400', 'Unknown file format to save to')

    def convert(self, annotations, from_format, to_format, conversion_func=None):

        # check params
        assert isinstance(from_format, str)
        assert isinstance(to_format, str)

        # check known format
        if from_format.lower() not in self.known_formats and conversion_func is None:
            raise dl.PlatformException(
                "400",
                "Unknown annotation format: {}, possible formats: {}".format(
                    from_format, self.known_formats
                ),
            )
        if to_format.lower() not in self.known_formats and conversion_func is None:
            raise dl.exceptions.PlatformException(
                "400",
                "Unknown annotation format: {}, possible formats: {}".format(
                    to_format, self.known_formats
                ),
            )

        # fix and save annotations globally
        if isinstance(annotations, dl.AnnotationCollection):
            annotations = annotations.annotations
        if not isinstance(annotations, list):
            annotations = [annotations]
        self.annotations = annotations

        # call method
        if from_format == "dataloop":
            self.from_dataloop(
                annotations=annotations,
                to_format=to_format.lower(),
                conversion_func=conversion_func,
            )
        elif to_format == "dataloop":
            self.to_dataloop(
                annotations=annotations,
                from_format=from_format.lower(),
                conversion_func=conversion_func,
            )
        else:
            raise dl.PlatformException(
                "400", "Can only convert from or to dataloop format"
            )

        return self.annotations

    def to_dataloop(self, annotations, from_format, conversion_func=None):
        pool = ThreadPool(processes=32)
        for i_annotation, annotation in enumerate(annotations):
            if conversion_func is None:
                pool.apply_async(
                    func=self.converter_dict[from_format]["from"],
                    kwds={"annotation": annotation, "i_annotation": i_annotation},
                )
            else:
                pool.apply_async(
                    func=self.custom_format,
                    kwds={
                        "annotation": annotation,
                        "i_annotation": i_annotation,
                        "conversion_func": conversion_func,
                    },
                )
        pool.close()
        pool.join()
        pool.terminate()

    def from_dataloop(self, annotations, to_format, conversion_func=None):
        pool = ThreadPool(processes=32)
        for i_annotation, annotation in enumerate(annotations):
            if conversion_func is None:
                pool.apply_async(
                    func=self.converter_dict[to_format]["to"],
                    kwds={"annotation": annotation, "i_annotation": i_annotation},
                )
            else:
                pool.apply_async(
                    func=self.custom_format,
                    kwds={
                        "annotation": annotation,
                        "i_annotation": i_annotation,
                        "conversion_func": conversion_func,
                    },
                )
        pool.close()
        pool.join()
        pool.terminate()

    def from_coco(self, annotation, i_annotation):
        pass

    def from_voc(self, annotation, i_annotation):
        pass

    def from_yolo(self, annotation, i_annotation):
        pass

    def to_yolo(self, annotation, i_annotation):
        if not isinstance(annotation, dl.Annotation):
            if self.item is None:
                self.item = self.dataset.items.get(item_id=annotation['itemId'])
            annotation = dl.Annotation.from_json(_json=annotation, item=self.item)
        if annotation.type != "box":
            self.annotations[i_annotation] = None
            raise dl.PlatformException(
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

        self.annotations[i_annotation] = (x, y, w, h)

    def to_coco(self, annotation, i_annotation):
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
        self.annotations[i_annotation] = ann

    def to_voc(self, annotation, i_annotation):
        pass

    def custom_format(self, annotation, i_annotation, conversion_func):
        self.annotations[i_annotation] = conversion_func(annotation)
