# https://github.com/AndrewCarterUK/pascal-voc-writer
import os
import shutil
import traceback
import tempfile
import logging
from PIL import Image
import json
from jinja2 import Environment, PackageLoader
from multiprocessing.pool import ThreadPool
import dtlpy as dl

logger = logging.getLogger(name=__name__)


class BaseConverterFromPlatform:
    def __init__(self, project_name, dataset_name, output_directory, remote_path):
        self.name = ''
        self.project_name = project_name
        self.dataset_name = dataset_name
        self.remote_path = remote_path
        self.output_directory = output_directory
        self.params = None

        # for threading outputs
        self.errors = None
        self.outputs = None
        self.results = None

    def convert_single_file(self, output_directory, item, annotations, params):
        # for user to create
        pass

    def threading_wrapper(self, func, i_item,
                          # inputs for user
                          output_directory, item, annotations, params=None):
        try:
            self.outputs[i_item] = func(output_directory=output_directory,
                                        item=item,
                                        annotations=annotations,
                                        params=params)
            self.results[i_item] = True
        except Exception as err:
            logging.exception(traceback.format_exc())
            self.errors[i_item] = traceback.format_exc()
            self.results[i_item] = False

    def run(self):
        # create temp path to save dataloop annotations
        local_annotations_path = os.path.join(tempfile.gettempdir(),
                                              'dataloop_annotations_{}'.format(hash(os.times())))
        if os.path.isdir(local_annotations_path):
            raise IsADirectoryError('path already exists')

        try:
            # download annotations zip to local directory
            project = dl.projects.get(project_name=self.project_name)
            dataset = project.datasets.get(dataset_name=self.dataset_name)

            dataset.items.download_annotations(dataset_name=self.dataset_name,
                                               local_path=os.path.join(local_annotations_path, '*'))

            # get labels to ids dictionary
            if 'labels_dict' not in self.params:
                self.params['labels_dict'] = {label: i_label for i_label, label in
                                              enumerate(list(dataset.labels.keys()))}

            output_annotations_path = os.path.join(self.output_directory, 'annotations')
            # create output directories
            if not os.path.isdir(self.output_directory):
                os.makedirs(self.output_directory)
            if not os.path.isdir(output_annotations_path):
                os.makedirs(output_annotations_path)

            # save labels
            with open(os.path.join(self.output_directory, 'labels.txt'), 'w') as f:
                f.write('\n'.join(['%s:%s' % (val, key) for key, val in self.params['labels_dict'].items()]))

            # get all items (for width and height)
            filters = dl.Filters()
            filters.add(field='filename', values=self.remote_path)
            filters.add(field='type', values='file')
            pages = dataset.items.list(filters=filters)

            # init workers and results lists
            pool = ThreadPool(processes=32)
            i_item = -1
            num_items = pages.items_count
            self.outputs = [None for _ in range(num_items)]
            self.results = [None for _ in range(num_items)]
            self.errors = [None for _ in range(num_items)]

            for page in pages:
                for item in page:
                    i_item += 1
                    # create input annotations json
                    in_filepath = os.path.join(local_annotations_path, item.filename[1:])
                    name, ext = os.path.splitext(in_filepath)
                    in_filepath = name + '.json'

                    # check if annotations file exists
                    if not os.path.isfile(in_filepath):
                        self.results[i_item] = False
                        self.errors[i_item] = 'file note found: %s' % in_filepath
                        continue

                    with open(in_filepath, 'r') as f:
                        data = json.load(f)

                    pool.apply_async(self.threading_wrapper, kwds={'func': self.convert_single_file,
                                                                   'i_item': i_item,
                                                                   # input for "func"
                                                                   'output_directory': output_annotations_path,
                                                                   'item': item,
                                                                   'annotations': data['annotations'],
                                                                   'params': self.params})
            print('Done')
            pool.close()
            pool.join()
            pool.terminate()
            dummy = [logger.error(self.errors[i_job]) for i_job, suc in enumerate(self.results) if suc is False]
            return self.outputs
        except:
            raise
        finally:
            # cleanup
            if os.path.isdir(local_annotations_path):
                shutil.rmtree(local_annotations_path)


class DtlpyToVoc(BaseConverterFromPlatform):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # specific for voc
        labels = dict()
        # annotations template
        environment = Environment(loader=PackageLoader('dtlpy', 'assets'),
                                  keep_trailing_newline=True)
        annotation_template = environment.get_template('voc_annotation_template.xml')
        self.params = {'labels': labels,
                       'annotation_template': annotation_template}

    @staticmethod
    def new_annotation(path, width, height, depth=3, database='Unknown', segmented=0):
        abspath = os.path.abspath(path)
        annotation = {
            'path': abspath,
            'filename': os.path.basename(abspath),
            'folder': os.path.basename(os.path.dirname(abspath)),
            'width': width,
            'height': height,
            'depth': depth,
            'database': database,
            'segmented': segmented,
            'objects': list()
        }
        return annotation

    def convert_single_file(self, item, annotations, output_directory, params):
        # output filepath for xml
        out_filepath = os.path.join(output_directory, item.filename[1:])
        # remove ext from output filepath
        out_filepath, ext = os.path.splitext(out_filepath)
        # add xml extension
        out_filepath += '.xml'
        if not os.path.isdir(os.path.dirname(out_filepath)):
            os.makedirs(os.path.dirname(out_filepath), exist_ok=True)

        width = item.width
        height = item.height
        output_annotation = {
            'path': item.filename,
            'filename': os.path.basename(item.filename),
            'folder': os.path.basename(os.path.dirname(item.filename)),
            'width': width,
            'height': height,
            'depth': 3,
            'database': 'Unknown',
            'segmented': 0,
            'objects': list()
        }

        for annotation in annotations:
            if not annotation:
                continue
            if annotation['type'] != 'box':
                continue
            label = annotation['label']
            coordinates = annotation['coordinates']

            attributes = list()
            # get attributes if exists
            if 'attributes' in annotation:
                attributes = annotation['attributes']

            try:
                left = int(coordinates[0]['x'])
                top = int(coordinates[0]['y'])
                right = int(coordinates[1]['x'])
                bottom = int(coordinates[1]['y'])
            except Exception as err:
                print('coordinates', coordinates)
                continue

            output_annotation['objects'].append({'name': label,
                                                 'xmin': left,
                                                 'ymin': top,
                                                 'xmax': right,
                                                 'ymax': bottom,
                                                 'attributes': attributes,
                                                 })
        with open(out_filepath, 'w') as file:
            content = params['annotation_template'].render(**output_annotation)
            file.write(content)


class DtlpyToYolo(BaseConverterFromPlatform):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = {'labels': dict()}

    @staticmethod
    def convert_bb(size, box):
        dw = 1. / size[0]
        dh = 1. / size[1]
        x = (box[0] + box[1]) / 2.0
        y = (box[2] + box[3]) / 2.0
        w = box[1] - box[0]
        h = box[3] - box[2]
        x = x * dw
        w = w * dw
        y = y * dh
        h = h * dh
        return x, y, w, h

    @staticmethod
    def convert_single_file(item, annotations, output_directory, params):
        # output filepath for xml
        out_filepath = os.path.join(output_directory, item.filename[1:])
        # remove ext from filepath
        out_filepath, ext = os.path.splitext(out_filepath)
        # add txt extension
        out_filepath += '.txt'

        if not os.path.isdir(os.path.dirname(out_filepath)):
            os.makedirs(os.path.dirname(out_filepath), exist_ok=True)

        width = item.width
        height = item.height
        yolo_annotations = list()
        for annotation in annotations:
            if annotation['type'] != 'box':
                continue
            label = annotation['label']
            coordinates = annotation['coordinates']
            try:
                left = int(coordinates[0]['x'])
                top = int(coordinates[0]['y'])
                right = int(coordinates[1]['x'])
                bottom = int(coordinates[1]['y'])
            except Exception as err:
                print('coords', coordinates)
                continue
            yolo_bb = DtlpyToYolo.convert_bb((width, height), (left, right, top, bottom))
            yolo_annotations.append(
                '%d %f %f %f %f' % (params['labels_dict'][label], yolo_bb[0], yolo_bb[1], yolo_bb[2], yolo_bb[3]))

        with open(out_filepath, 'w') as f:
            f.write('\n'.join(yolo_annotations))
