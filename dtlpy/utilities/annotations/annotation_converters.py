# https://github.com/AndrewCarterUK/pascal-voc-writer
import os
import traceback
import tempfile
import logging
from PIL import Image
import json
from jinja2 import Environment, PackageLoader
from multiprocessing.pool import ThreadPool
from dtlpy import PlatformInterface


class DtlpyToVoc:
    def __init__(self, project_name, output_annotations_path, dataset_name, remote_path='/'):
        self.project_name = project_name
        self.dataset_name = dataset_name
        self.output_annotations_path = output_annotations_path
        self.remote_path = remote_path
        self.classes = dict()
        # for outputs
        self.outputs = None
        self.success = None
        self.errors = None
        # annotations template
        self.environment = Environment(loader=PackageLoader('dtlpy', 'assets'),
                                       keep_trailing_newline=True)
        self.annotation_template = self.environment.get_template('voc_annotation_template.xml')

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

    def convert_single_file(self, item, in_filepath, out_filepath, i_item):
        try:
            with open(in_filepath, 'r') as f:
                data = json.load(f)
            if not data['annotations']:
                return

            width = item.width
            height = item.height
            new_annotation = {
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

            for annotation in data['annotations']:
                if annotation['type'] != 'box':
                    continue
                label = annotation['label']
                attributes = annotation['attributes']
                coordinates = annotation['coordinates']
                try:
                    left = int(coordinates[0]['x'])
                    top = int(coordinates[0]['y'])
                    right = int(coordinates[1]['x'])
                    bottom = int(coordinates[1]['y'])
                except Exception as err:
                    print('coords', coordinates)
                    continue

                annotation['objects'].append({'name': label,
                                              'xmin': left,
                                              'ymin': top,
                                              'xmax': right,
                                              'ymax': bottom,
                                              'attributes': attributes,
                                              })
            with open(out_filepath, 'w') as file:
                content = self.annotation_template.render(**new_annotation)
                file.write(content)

            self.outputs[i_item] = data
        except Exception as e:
            self.outputs[i_item] = item.id
            self.success[i_item] = False
            self.errors[i_item] = e

    def run(self):
        logger = logging.getLogger('dataloop.utilities.annotations.converter.voc')

        # init platform
        dlp = PlatformInterface()

        # create temp path to save dataloop annotations
        local_annotations_path = os.path.join(tempfile.gettempdir(), 'dataloop_annotations_{}'.format(hash(os.times())))
        if os.path.isdir(local_annotations_path):
            raise IsADirectoryError('path already exists')

        # download annotations zip to local directory
        dataset = dlp.projects.get(project_name=self.project_name).datasets.get(dataset_name=self.dataset_name)
        dlp.projects.get(project_name=self.project_name).datasets.download_annotations(dataset_name=self.dataset_name,
                                                                                       local_path=local_annotations_path)
        # get all items (for width and height)
        pages = dataset.items.list(query={'filenames': [self.remote_path],
                                          'itemType': 'file'})

        # init workers and results lists
        pool = ThreadPool(processes=32)
        i_item = 0
        num_items = pages.items_count
        success = [None for _ in range(num_items)]
        errors = [None for _ in range(num_items)]
        outputs = [None for _ in range(num_items)]

        for page in pages:
            for item in page:
                # create input annotations json
                in_filepath = os.path.join(local_annotations_path, item.filename[1:])
                name, ext = os.path.splitext(in_filepath)
                in_filepath = name + '.json'
                # output filepath for xml
                out_filepath = in_filepath.replace(local_annotations_path, self.output_annotations_path)
                # replace ext from .json to .xml
                out_filepath = out_filepath.replace('.json', '.xml')

                # sanity and folder check
                if not os.path.isfile(in_filepath):
                    continue
                if not os.path.isdir(os.path.dirname(out_filepath)):
                    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
                pool.apply_async(self.convert_single_file, kwds={'item': item,
                                                                 'in_filepath': in_filepath,
                                                                 'out_filepath': out_filepath,
                                                                 'i_item': i_item})
        print('Done')
        pool.close()
        pool.join()
        pool.terminate()
        dummy = [logger.error(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        return outputs


class DtlpyToYolo:
    def __init__(self, project_name, output_annotations_path, dataset_name, remote_path='/'):
        self.project_name = project_name
        self.dataset_name = dataset_name
        self.output_annotations_path = output_annotations_path
        self.remote_path = remote_path
        self.classes = dict()
        # for outputs
        self.outputs = None
        self.success = None
        self.errors = None

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
        return (x, y, w, h)

    def convert_single_file(self, item, in_filepath, out_filepath, i_item):
        try:
            with open(in_filepath, 'r') as f:
                data = json.load(f)
            if not data['annotations']:
                return

            width = item.width
            height = item.height
            yolo_annotations = list()
            for annotation in data['annotations']:
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
                yolo_bb = self.convert_bb((width, height), (left, right, top, bottom))
                yolo_annotations.append(
                    '%d %f %f %f %f' % (self.classes[label], yolo_bb[0], yolo_bb[1], yolo_bb[2], yolo_bb[3]))

            with open(out_filepath, 'w') as f:
                f.write('\n'.join(yolo_annotations))
            self.outputs[i_item] = data

        except Exception as e:
            self.outputs[i_item] = item.id
            self.success[i_item] = False
            self.errors[i_item] = e

    def run(self):
        logger = logging.getLogger('dataloop.utilities.annotations.converter.yolo')

        # init platform
        dlp = PlatformInterface()

        # create temp path to save dataloop annotations
        local_annotations_path = os.path.join(tempfile.gettempdir(), 'dataloop_annotations_{}'.format(hash(os.times())))
        if os.path.isdir(local_annotations_path):
            raise IsADirectoryError('path already exists')

        # download annotations zip to local directory
        dataset = dlp.projects.get(project_name=self.project_name).datasets.get(dataset_name=self.dataset_name)
        dlp.projects.get(project_name=self.project_name).datasets.download_annotations(dataset_name=self.dataset_name,
                                                                                       local_path=local_annotations_path)

        # get classes and ids
        self.classes = {label: i_label for i_label, label in enumerate(list(dataset.classes.keys()))}

        # get all items (for width and height)
        pages = dataset.items.list(query={'filenames': [self.remote_path],
                                          'itemType': 'file'})

        # init workers and results lists
        pool = ThreadPool(processes=32)
        i_item = 0
        num_items = pages.items_count

        # init outputs lists
        self.success = [None for _ in range(num_items)]
        self.errors = [None for _ in range(num_items)]
        self.outputs = [None for _ in range(num_items)]

        for page in pages:
            for item in page:
                # create input annotations json
                in_filepath = os.path.join(local_annotations_path, item.filename[1:])
                name, ext = os.path.splitext(in_filepath)
                in_filepath = name + '.json'
                # output filepath for xml
                out_filepath = in_filepath.replace(local_annotations_path, self.output_annotations_path)
                # replace ext from .json to .xml
                out_filepath = out_filepath.replace('.json', '.txt')

                # sanity and folder check
                if not os.path.isfile(in_filepath):
                    continue
                if not os.path.isdir(os.path.dirname(out_filepath)):
                    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
                pool.apply_async(self.convert_single_file, kwds={'item': item,
                                                                 'in_filepath': in_filepath,
                                                                 'out_filepath': out_filepath,
                                                                 'i_item': i_item})
        print('Done')
        pool.close()
        pool.join()
        pool.terminate()
        dummy = [logger.error(self.errors[i_job]) for i_job, suc in enumerate(self.success) if suc is False]
        return self.outputs
