"""
Datasets Repository
"""

import os
from multiprocessing.pool import ThreadPool
import logging
import traceback
import datetime
import json
from urllib.parse import urlencode
import threading
import queue
from progressbar import Bar, ETA, ProgressBar, Timer
import numpy as np
from .. import entities, repositories, utilities, PlatformException, exceptions
import attr


@attr.s
class Datasets:
    """
    Datasets repository
    """
    client_api = attr.ib()
    project = attr.ib()
    logger = attr.ib(default=logging.getLogger('dataloop.repositories.datasets'))

    def list(self):
        """
        List all datasets.

        :return: List of datasets
        """
        if self.project is None:
            self.logger.exception('Cant list datasets with no project. Try same command from a "project" entity')
            raise ValueError('Cant list datasets with no project. Try same command from a "project" entity')
        query_string = urlencode({'name': '', 'creator': '', 'projects': self.project.id}, doseq=True)
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets?%s' % query_string)
        if success:
            datasets = utilities.List([entities.Dataset.from_json(client_api=self.client_api,
                                                                  _json=_json,
                                                                  project=self.project)
                                       for _json in response.json()])
        else:
            raise PlatformException(response)
        return datasets

    def get(self, dataset_name=None, dataset_id=None):
        """
        Get dataset by name or id

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :return: Dataset object
        """
        if dataset_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/datasets/%s' % dataset_id)
            if success:
                dataset = entities.Dataset.from_json(client_api=self.client_api,
                                                     _json=response.json(),
                                                     project=self.project)
            else:
                raise PlatformException(response)
        elif dataset_name is not None:
            datasets = self.list()
            dataset = [dataset for dataset in datasets if dataset.name == dataset_name]
            if not dataset:
                # empty list
                self.logger.info('Dataset not found. dataset_name: %s', dataset_name)
                raise PlatformException('404', 'Dataset not found.')
                # dataset = None
            elif len(dataset) > 1:
                # more than one dataset
                self.logger.warning('More than one dataset with same name. Please "get" by id')
                raise PlatformException('400', 'More than one dataset with same name.')
            else:
                dataset = dataset[0]
        else:
            self.logger.exception('Must choose by at least one. "dataset_id" or "dataset_name"')
            raise PlatformException('400', 'Must choose by at least one. "dataset_id" or "dataset_name"')
        return dataset

    def download_annotations(self, dataset_name=None, dataset_id=None, local_path=None):
        """
        Download annotations json for entire dataset

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param local_path:
        :return:
        """
        dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets/%s/annotations/zip' % dataset.id)
        if not success:
            # platform error
            self.logger.exception('Downloading annotations zip')
            raise PlatformException(response)
        # create local path
        if local_path is None:
            if self.project is not None:
                local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                          'projects', self.project.name,
                                          'datasets', dataset.name,
                                          'json')
            else:
                local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                          'datasets', dataset.id,
                                          'json')
        else:
            if local_path.endswith('/*') or local_path.endswith(r'\*'):
                # if end with * download directly to folder
                local_path = local_path[:-2]
            else:
                local_path = os.path.join(local_path, 'json')
        # zip filepath
        annotations_zip = os.path.join(local_path, 'annotations.zip')
        if not os.path.isdir(local_path):
            os.makedirs(local_path)
        try:
            # downloading zip from platform
            with open(annotations_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            # unzipping annotations to directory
            utilities.Miscellaneous.unzip_directory(zip_filename=annotations_zip, to_directory=local_path)

        except Exception:
            self.logger.exception('Getting annotations from zip ')
            raise
        finally:
            # cleanup
            if os.path.isfile(annotations_zip):
                os.remove(annotations_zip)

    def download(self, dataset_name=None, dataset_id=None,
                 query=None, local_path=None, filetypes=None,
                 num_workers=None, download_options=None, save_locally=True,
                 download_item=True, annotation_options=None,
                 opacity=1, with_text=False, thickness=3):
        """
        Download dataset by query.
        Quering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item
        :param dataset_name: get dataset by name
        :param dataset_id: get dataset by id
        :param query: Query entity or a dictionary containing query parameters
        :param local_path: local folder or filename to save to. if folder ends with * images with be downloaded directly to folder. else - an "images" folder will be create for the images
        :param filetypes: a list of filetype to download. e.g ['.jpg', '.png']
        :param num_workers: default - 32
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param save_locally: bool. save to disk or return a buffer
        :param download_item: bool. download image
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param opacity: for img_mask
        :param with_text: add label to annotations
        :param thickness: annotation line
        :return: Output (list)
        """

        def download_single_item(i_item, item):
            try:
                w_dataset = dataset.__copy__()
                download = False
                for i_try in range(num_tries):
                    try:
                        download = w_dataset.items.download(item_id=item.id,
                                                            save_locally=save_locally,
                                                            local_path=local_path,
                                                            download_options=download_options,
                                                            download_item=download_item,
                                                            annotation_options=annotation_options,
                                                            verbose=False,
                                                            show_progress=True)
                    except:
                        if i_try > num_tries:
                            raise
                        else:
                            i_try += 1
                            continue
                status[i_item] = 'download'
                output[i_item] = download
                success[i_item] = True
            except Exception as err:
                status[i_item] = 'error'
                output[i_item] = i_item
                success[i_item] = False
                errors[i_item] = '%s\n%s' % (err, traceback.format_exc())
            finally:
                progress.queue.put((status[i_item],))

        dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
        if annotation_options is None:
            annotation_options = list()
        default_download_options = repositories.items.DEFAULT_DOWNLOAD_OPTIONS
        if download_options is None:
            download_options = default_download_options
        else:
            if not isinstance(download_options, dict):
                msg = '"download_options" must be a dict. {<option>:<value>}. default: %s' % default_download_options
                raise ValueError(msg)
            tmp_options = default_download_options
            for key, val in download_options.items():
                if key not in tmp_options:
                    raise ValueError('unknown download option: %s. known: %s' % (key, list(tmp_options.keys())))
                tmp_options[key] = val
            download_options = tmp_options
        if num_workers is None:
            num_workers = 32
        self.logger.info('Download workers number:{}'.format(num_workers))
        # which file to download
        if filetypes is None:
            # default
            # TODO
            pass
        # create local path
        num_tries = 3
        if local_path is None:
            if self.project is None:
                local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                          'datasets', '%s_%s' % (dataset.name, dataset.id))
            else:
                local_path = os.path.join(os.path.expanduser('~'), '.dataloop',
                                          'projects', self.project.name,
                                          'datasets', dataset.name)
        folder_to_check = local_path
        if local_path.endswith('/*') or local_path.endswith(r'\*'):
            folder_to_check = local_path[:-2]
        if os.path.isdir(folder_to_check):
            self.logger.info('Local folder already exists:%s. merge/overwrite according to "download_options"',
                             folder_to_check)
        else:
            self.logger.info('Creating new directory for download: %s', folder_to_check)
            os.makedirs(folder_to_check, exist_ok=True)

        # download annotations' json files
        if 'json' in annotation_options:
            # a new folder named 'json' will be created under the "local_path"
            self.download_annotations(dataset_name=dataset_name,
                                      dataset_id=dataset_id,
                                      local_path=os.path.join(local_path))
        paged_entity = dataset.items.list(query=query)
        output = [None for _ in range(paged_entity.items_count)]
        success = [None for _ in range(paged_entity.items_count)]
        status = [None for _ in range(paged_entity.items_count)]
        errors = [None for _ in range(paged_entity.items_count)]
        num_files = paged_entity.items_count
        progress = Progress(max_val=num_files, progress_type='download')
        pool = ThreadPool(processes=num_workers)
        progress.start()
        try:
            i_items = 0
            for page in paged_entity:
                for item in page:
                    if item.type == 'dir':
                        continue
                    self.logger.info('Adding:{}'.format(item.filename))
                    pool.apply_async(download_single_item, kwds={'i_item': i_items, 'item': item})
                    i_items += 1
        except Exception as e:
            self.logger.exception(e)
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None,))
            progress.queue.join()
            progress.finish()
        n_upload = status.count('download')
        n_exist = status.count('exist')
        n_error = status.count('error')
        self.logger.info('Number of files downloaded:{}'.format(n_upload))
        self.logger.info('Number of files exists: {}'.format(n_exist))
        self.logger.info('Total number of files: {}'.format(n_upload + n_exist))
        # log error
        if n_error > 0:
            log_filepath = os.path.join(folder_to_check,
                                        'log_%s.txt' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            errors_list = [errors[i_job] for i_job, suc in enumerate(success) if suc is False]
            ids_list = [output[i_job] for i_job, suc in enumerate(success) if suc is False]
            errors_json = {item_id: error for item_id, error in zip(errors_list, ids_list)}
            with open(log_filepath, 'w') as f:
                json.dump(errors_json, f, indent=4)
            self.logger.warning('Errors in {} files. See %s for full log'.format(n_error, log_filepath))

        # remove empty cells
        output = [x for x in output if x is not None]
        return output

    def upload(self, dataset_name=None, dataset_id=None,
               local_path=None, local_annotations_path=None, remote_path=None,
               upload_options=None, filetypes=None, num_workers=None):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param local_path: local files to upload
        :param local_annotations_path: path to dataloop format annotations json files.
         annotations need to be in same files structure as "local_path"
        :param remote_path: remote path to save.
        :param upload_options: 'merge' or 'overwrite'
        :param filetypes: list of filetype to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers:
        :return: Output (list)
        """

        def callback(monitor):
            progress.queue.put((monitor.encoder.fields['path'], monitor.bytes_read))

        def upload_single_file(i_item, filepath, annotations_filepath, relative_path):
            try:
                w_dataset = dataset.__copy__()
                # create remote path
                remote_path_w = os.path.join(remote_path, os.path.dirname(relative_path)).replace('\\', '/')
                uploaded_filename_w = os.path.basename(filepath)
                remote_filepath_w = os.path.join(remote_path_w, uploaded_filename_w).replace('\\', '/')
                # check if item exists
                try:
                    items = w_dataset.items.get(filepath=remote_filepath_w)
                    # items exists
                    if upload_options == 'overwrite':
                        # delete remote item
                        result, response = w_dataset.items.delete(item_id=items[0].id)
                        if not result:
                            raise PlatformException(response)
                    else:
                        status[i_item] = 'exist'
                        output[i_item] = relative_path
                        success[i_item] = True
                        return
                except exceptions.NotFound:
                    pass
                # put file in gate
                result = False
                for _ in range(num_tries):
                    result = w_dataset.items.upload(filepath=filepath,
                                                    annotations_filepath=annotations_filepath,
                                                    remote_path=remote_path_w,
                                                    uploaded_filename=uploaded_filename_w,
                                                    callback=callback)
                    if result:
                        break
                if not result:
                    raise w_dataset.items.client_api.platform_exception
                status[i_item] = 'upload'
                output[i_item] = relative_path
                success[i_item] = True
            except Exception as err:
                status[i_item] = 'error'
                output[i_item] = relative_path
                success[i_item] = False
                errors[i_item] = '%s\n%s' % (err, traceback.format_exc())

        if local_path is None:
            assert False
        if num_workers is None:
            num_workers = 32
        if remote_path is None:
            remote_path = '/'
        if upload_options is None:
            upload_options = 'merge'
        if filetypes is not None and not isinstance(filetypes, list):
            self.logger.exception('"filetypes" should be a list of file extension. e.g [".jpg", ".png"]')
            return False
        dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
        include_head_folder = True
        if local_path.endswith('/*') or local_path.endswith(r'\*'):
            local_path = local_path[:-2]
            include_head_folder = False
        if not os.path.isdir(local_path):
            self.logger.exception('Directory doest exists: %s', local_path)
            raise OSError('Directory doest exists: %s' % local_path)
        if filetypes is None:
            self.logger.info('Uploading ALL files of type!')
        else:
            self.logger.info('Uploading ONLY files of type: %s', ','.join(filetypes))

        num_tries = 3
        filepaths = list()
        annotations_filepaths = list()
        total_size = 0
        for root, subdirs, files in os.walk(local_path):
            for filename in files:
                _, ext = os.path.splitext(filename)
                if filetypes is None or ext in filetypes:
                    # get full image filepath
                    filepath = os.path.join(root, filename)
                    # extract item's size
                    total_size += os.path.getsize(filepath)
                    # append to list
                    filepaths.append(filepath)
                    # get annotations file
                    if local_annotations_path is not None:
                        # change path to annotations
                        annotations_filepath = filepath.replace(local_path, local_annotations_path)
                        # remove image extension
                        annotations_filepath, _ = os.path.splitext(annotations_filepath)
                        # add json extension
                        annotations_filepath += '.json'
                        # append to list
                        annotations_filepaths.append(annotations_filepath)
        if local_annotations_path is None:
            annotations_filepaths = [None for _ in range(len(filepaths))]
        num_files = len(filepaths)
        output = [None for _ in range(num_files)]
        status = [None for _ in range(num_files)]
        success = [None for _ in range(num_files)]
        errors = [None for _ in range(num_files)]
        progress = Progress(max_val=total_size, progress_type='upload')
        pool = ThreadPool(processes=num_workers)
        progress.start()
        try:
            for i_item in range(len(filepaths)):
                # update total files' size
                filepath = filepaths[i_item]
                # get matching annotation. None if annotations path was not in inputs
                annotations_filepath = annotations_filepaths[i_item]
                # update progressbar
                if include_head_folder:
                    relative_path = os.path.relpath(filepath, os.path.dirname(local_path))
                else:
                    relative_path = os.path.relpath(filepath, local_path)
                pool.apply_async(upload_single_file, kwds={'i_item': i_item,
                                                           'filepath': filepath,
                                                           'annotations_filepath': annotations_filepath,
                                                           'relative_path': relative_path})
        except Exception as e:
            self.logger.exception(e)
            self.logger.exception(traceback.format_exc())
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None, None))
            progress.queue.join()
            progress.finish()
        n_upload = status.count('upload')
        n_exist = status.count('exist')
        n_error = status.count('error')
        self.logger.info('Number of files uploaded: {}'.format(n_upload))
        self.logger.info('Number of files exists: {}'.format(n_exist))
        self.logger.info('Number of errors: {}'.format(n_error))
        self.logger.info('Total number of files: {}'.format(n_upload + n_exist))
        # log error
        if n_error > 0:
            log_filepath = os.path.join(local_path, 'log_%s.txt' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            errors_list = [errors[i_job] for i_job, suc in enumerate(success) if suc is False]
            with open(log_filepath, 'w') as f:
                f.write('\n'.join(errors_list))
            self.logger.warning('Errors in {n_error} files. See {log_filepath} for full log'.format(n_error=n_error,
                                                                                                    log_filepath=log_filepath))
        # remove empty cells
        output = [x for x in output if x is not None]
        return output

    def delete(self, dataset_name=None, dataset_id=None, sure=False, really=False):
        """
        Delete a dataset forever!
        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param sure: are you sure you want to delete?
        :param really: really really?

        :return: True
        """
        if sure and really:
            dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/datasets/%s' % dataset.id)
            if not success:
                raise PlatformException(response)
            self.logger.info('Dataset was deleted successfully')
            return True
        else:
            raise PlatformException(error='403',
                                    message='Cant delete dataset from SDK. Please login to platform to delete')

    def update(self, dataset, system_metadata=False):
        """
        Update dataset field
        :param dataset: Dataset entity
        :param system_metadata: bool
        :return: Dataset object
        """
        url_path = '/datasets/%s' % dataset.id
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=dataset.to_json())
        if success:
            self.logger.info('Dataset was updated successfully')
            return dataset
        else:
            self.logger.exception('Platform error updating dataset. id: %s' % dataset.id)
            raise PlatformException(response)

    def create(self, dataset_name, labels=None, driver=None, attributes=None):
        """
        Create a new dataset

        :param dataset_name: name
        :param attributes:
        :param labels: dictionary of labels and colors
        :param driver: dictionary of labels and colors
        :return: Dataset object
        """
        # labels to list
        if labels is not None:
            labels = entities.Dataset.serialize_labels(labels)
        else:
            labels = list()
        # get creator from token
        if self.project is None:
            self.logger.exception('Cant create dataset with no project. Try same command from a "project" entity')
            raise ValueError('Cant create dataset with no project. Try same command from a "project" entity')
        payload = {'name': dataset_name,
                   'projects': [self.project.id]}
        if driver is not None:
            payload['driver'] = driver
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/datasets',
                                                        json_req=payload)
        if success:
            dataset = entities.Dataset.from_json(client_api=self.client_api,
                                                 _json=response.json(),
                                                 project=self.project)
            # create ontology and recipe
            recipe = dataset.recipes.create(ontology_ids=None, labels=labels, attributes=attributes)
            # patch recipe to dataset
            dataset.metadata['system']['recipes'] = [recipe.id]
            self.update(dataset=dataset, system_metadata=True)
            dataset = self.get(dataset_name=dataset.name)
        else:
            raise PlatformException(response)
        self.logger.info('Dataset was created successfully. Dataset id: %s' % dataset.id)
        return dataset

    def set_items_metadata(self, dataset_name=None, dataset_id=None, query=None,
                           key_val_list=None, percent=None, random=True):
        """
        Set of changes metadata key for a query.

        :param dataset_name: optional - search by name
        :param dataset_id: optional - search by id
        :param query: Query entity or a dictionary containing query parameters
        :param key_val_list: list of dictioanry to set in metadata. e.g [{'split': 'training'}, {'split': 'validation'}
        :param percent: list of percentages to set the key_val_list
        :param random: bool. shuffle the items before setting the metadata
        :return: Output (list)
        """

        def set_single_item(i_item, item, key_val):
            try:
                metadata = item.to_json()
                for key, val in key_val.items():
                    metadata[key] = val
                item.from_dict(metadata)
                dataset.items.update(item)
                success[i_item] = True
            except Exception as err:
                success[i_item] = False
                errors[i_item] = '%s\n%s' % (err, traceback.format_exc())

        if key_val_list is None or percent is None:
            self.logger.exception('Must input name and percents')
            raise PlatformException('400', 'Must input name and percents')
        if not (isinstance(key_val_list, list) and isinstance(key_val_list[0], dict)):
            self.logger.exception(
                '"key_val" must be a list of dictionaries of keys and values to store in items metadata')
            raise PlatformException('400',
                                    '"key_val" must be a list of dictionaries of keys and values to store in items metadata')
        if np.sum(percent) != 1:
            self.logger.exception('"percent" must sum up to 1')
            raise PlatformException('400', '"percent" must sum up to 1')
        # start
        dataset = self.get(dataset_name=dataset_name, dataset_id=dataset_id)
        pages = dataset.items.list(query=query)
        num_items = pages.items_count
        # get list of number of items for each percent
        percent_cumsum = num_items * np.cumsum(percent)
        # add zero at index 0
        percent_cumsum = np.insert(percent_cumsum, 0, 0).astype(int)
        if random:
            indices = np.random.permutation(num_items)
        else:
            indices = np.arange(num_items)
        splits = [indices[percent_cumsum[i]:percent_cumsum[i + 1]] for i in range(len(percent_cumsum) - 1)]
        success = [None for _ in range(pages.items_count)]
        output = [None for _ in range(pages.items_count)]
        errors = [None for _ in range(pages.items_count)]
        progress = Progress(max_val=num_items, progress_type='download')
        pool = ThreadPool(processes=32)
        progress.start()
        try:
            i_items = 0
            for page in pages:
                for item in page:
                    if item.type == 'dir':
                        continue
                    item_split_name = [key_val_list[i] for i, inds in enumerate(splits) if i_items in inds]
                    output[i_items] = item.id
                    pool.apply_async(set_single_item, kwds={'i_item': i_items,
                                                            'item': item,
                                                            'key_val_list': item_split_name})
                    i_items += 1
        except Exception as e:
            self.logger.exception(e)
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None,))
            progress.queue.join()
            progress.finish()
        # remove None items (dirs)
        success = [x for x in success if x is not None]
        output = [x for x in output if x is not None]
        good = success.count(True)
        bad = success.count(False)
        self.logger.info('Set metadata succefully for %d/%d' % (good, good + bad))
        # log error
        dummy = [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        # remove empty cells
        return output


class Progress(threading.Thread):
    """
    Progressing class for downloading and uploading items
    """

    def __init__(self, max_val, progress_type):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('dataloop.repositories.datasets.progressbar')
        self.progress_type = progress_type
        self.progressbar = None

        self.queue = queue.Queue(maxsize=0)
        self.progressbar_init(max_val=max_val)
        #############
        self.upload_dict = dict()
        self.download = 0
        self.exist = 0
        self.error = 0

    def progressbar_init(self, max_val):
        """
        init progress bar

        :param max_val:
        :return:
        """
        self.progressbar = ProgressBar(widgets=[' [', Timer(), '] ', Bar(), ' (', ETA(), ')'],
                                       redirect_stdout=True,
                                       redirect_stderr=True
                                       )
        self.progressbar.max_value = max_val

    def finish(self):
        """
        close the progress bar

        :return:
        """
        self.progressbar.finish()

    def run_upload(self):
        """
        queue handling function for upload

        :return:
        """
        self.upload_dict = dict()
        while True:
            try:
                # get item from queue
                decoded_body = self.queue.get()
                remote_path, bytes_read = decoded_body
                if remote_path is None:
                    self.upload_dict = dict()
                    break
                self.upload_dict[remote_path] = bytes_read
                # update bar
                total_size = np.sum(list(self.upload_dict.values()))
                if total_size > self.progressbar.max_value:
                    self.progressbar.max_value = total_size
                self.progressbar.update(total_size)

            except Exception as e:
                self.logger.exception(e)
                self.logger.exception(traceback.format_exc())
            finally:
                self.queue.task_done()

    def run_download(self):
        """
        queue handling function for downloads

        :return:
        """
        self.download = 0
        self.exist = 0
        self.error = 0
        while True:
            try:
                # get item from queue
                decoded_body = self.queue.get()
                msg, = decoded_body
                if msg is None:
                    break
                if msg == 'download':
                    self.download += 1
                elif msg == 'exist':
                    self.exist += 1
                elif msg == 'error':
                    self.error += 1
                else:
                    self.logger.exception('Unknown message type: %s', msg)
                    # update bar
                self.progressbar.update(self.download + self.exist)
            except Exception as error:
                self.logger.exception(error)
            finally:
                self.queue.task_done()

    def run(self):
        if self.progress_type == 'upload':
            self.run_upload()
        elif self.progress_type == 'download':
            self.run_download()
        else:
            assert False
