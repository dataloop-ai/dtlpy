import io
import os
import json
import traceback
import numpy as np
import datetime
from PIL import Image
import queue
import threading
import logging
from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize, Percentage, FormatLabel
from multiprocessing.pool import ThreadPool

from .. import entities, PlatformException, utilities

logger = logging.getLogger('dataloop.repositories.items.downloader')

DEFAULT_DOWNLOAD_OPTIONS = {
    'overwrite': False,  # merge with existing items
    'relative_path': True,  # maintain platform file system
    'num_tries': 3,  # try to download 3 time before fail on item
    'to_images_folder': True  # download to "images" folder
}


class Downloader:
    def __init__(self, items_repository):
        self.items_repository = items_repository

    def download(self,
                 # filter options
                 filters=None, items=None,
                 # download options
                 local_path=None, file_types=None, download_options=None, save_locally=True,
                 num_workers=None,
                 annotation_options=None):
        """
            Download dataset by filters.
            Filtering the dataset for items and save them local
            Optional - also download annotation, mask, instance and image mask of the item

        :param items: download Item entity or item_id (or a list of item)
        :param filters: Filters entity or a dictionary containing filters parameters
        :param local_path: local folder or filename to save to.
        :param file_types: a list of file type to download. e.g ['.jpg', '.png']
        :param num_workers: default - 32
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param save_locally: bool. save to disk or return a buffer
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :return: Output (list)
        """

        ###################
        # Default options #
        ###################
        if file_types is None:
            # default
            # TODO
            pass
        if annotation_options is None:
            annotation_options = list()
        default_download_options = DEFAULT_DOWNLOAD_OPTIONS
        if download_options is None:
            download_options = default_download_options
        else:
            if not isinstance(download_options, dict):
                msg = '"download_options" must be a dict. {<option>:<value>}. default: %s' % default_download_options
                raise PlatformException('400', msg)
            tmp_options = default_download_options
            for key, val in download_options.items():
                if key not in tmp_options:
                    raise PlatformException('400',
                                            'unknown download option: %s. known: %s' % (key, list(tmp_options.keys())))
                tmp_options[key] = val
            download_options = tmp_options
        if num_workers is None:
            num_workers = 32
        logger.debug('Download workers number:{}'.format(num_workers))
        # create default path
        if local_path is None:
            if self.items_repository.dataset.project is None:
                local_path = os.path.join(os.path.expanduser('~'),
                                          '.dataloop',
                                          'datasets',
                                          '%s_%s' % (
                                              self.items_repository.dataset.name, self.items_repository.dataset.id))
            else:
                local_path = os.path.join(os.path.expanduser('~'),
                                          '.dataloop',
                                          'projects',
                                          self.items_repository.dataset.project.name,
                                          'datasets',
                                          self.items_repository.dataset.name)
        logger.info('Downloading to: {}'.format(local_path))
        folder_to_check = local_path
        if local_path.endswith('/*') or local_path.endswith(r'\*'):
            folder_to_check = local_path[:-2]
        if os.path.isdir(folder_to_check):
            logger.info('Local folder already exists:{}. merge/overwrite according to "download_options"'.format(
                folder_to_check))
        else:
            logger.info('Creating new directory for download: {}'.format(folder_to_check))
            os.makedirs(folder_to_check, exist_ok=True)

        # Which items to download
        if items is not None:
            # convert input to a list
            if not isinstance(items, list):
                items = [items]
            if isinstance(items[0], str):
                items = [self.items_repository.get(item_id=item_id) for item_id in items]
            elif isinstance(items[0], entities.Item):
                pass
            else:
                raise PlatformException(
                    error='400',
                    message='Unknown items type to download. expecting (str) or entities.Items. Got "{}" instead'.format(
                        type(items[0]))
                )
            # convert to list of list (like pages and page)
            num_items = len(items)
            items_to_download = [items]
        else:
            items_to_download = self.items_repository.list(filters=filters)
            num_items = items_to_download.items_count

        # download annotations' json files in a new thread
        # items will start downloading and if json not exists yet - will download for each file
        if annotation_options:
            # a new folder named 'json' will be created under the "local_path"
            logger.info('Downloading annotations formats: {}'.format(annotation_options))
            thread = threading.Thread(target=self.download_annotations,
                                      kwargs={'dataset': self.items_repository.dataset,
                                              'local_path': local_path})
            thread.start()
        output = [None for _ in range(num_items)]
        success = [False for _ in range(num_items)]
        status = ['' for _ in range(num_items)]
        errors = [None for _ in range(num_items)]
        progress = Progress(max_val=num_items, progress_type='download')
        pool = ThreadPool(processes=num_workers)
        progress.start()
        try:
            i_item = 0
            for page in items_to_download:
                for item in page:
                    if item.type == 'dir':
                        continue
                    if save_locally:
                        item_local_path, item_local_filepath = self.__get_local_filepath(local_path=local_path,
                                                                                         item=item,
                                                                                         download_options=download_options)
                        if os.path.isfile(item_local_filepath) and download_options['overwrite'] is False:
                            logger.info('File Exists: {}'.format(item_local_filepath))
                            status[i_item] = 'exist'
                            output[i_item] = item_local_filepath
                            success[i_item] = True
                            progress.queue.put((status[i_item],))
                            i_item += 1
                            if annotation_options:
                                pool.apply_async(self.__download_img_annotations,
                                                 kwds={'item': item,
                                                       'img_filepath': item_local_filepath,
                                                       'download_options': download_options,
                                                       'annotation_options': annotation_options,
                                                       'local_path': local_path})
                            continue

                    else:
                        item_local_path = None
                        item_local_filepath = None
                    logger.info('File Download: {}'.format(item.filename))
                    pool.apply_async(self.__thread_download_wrapper, kwds={'i_item': i_item,
                                                                           'item': item,
                                                                           'item_local_path': item_local_path,
                                                                           'item_local_filepath': item_local_filepath,
                                                                           'save_locally': save_locally,
                                                                           'download_options': download_options,
                                                                           'annotation_options': annotation_options,
                                                                           'status': status,
                                                                           'output': output,
                                                                           'success': success,
                                                                           'errors': errors,
                                                                           'progress': progress})
                    i_item += 1
        except Exception as e:
            logger.exception(e)
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None,))
            progress.queue.join()
            progress.finish()
        n_upload = status.count('download')
        n_exist = status.count('exist')
        n_error = status.count('error')
        logger.info('Number of files downloaded:{}'.format(n_upload))
        logger.info('Number of files exists: {}'.format(n_exist))
        logger.info('Total number of files: {}'.format(n_upload + n_exist))
        # log error
        if n_error > 0:
            log_filepath = os.path.join('log_%s.txt' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            errors_list = [errors[i_job] for i_job, suc in enumerate(success) if suc is False]
            ids_list = [output[i_job] for i_job, suc in enumerate(success) if suc is False]
            errors_json = {item_id: error for item_id, error in zip(ids_list, errors_list)}
            with open(log_filepath, 'w') as f:
                json.dump(errors_json, f, indent=4)
            logger.warning('Errors in {} files. See {} for full log'.format(n_error, log_filepath))

        # remove empty cells
        output = [output[i_job] for i_job, suc in enumerate(success) if suc is True]
        if len(output) == 1:
            output = output[0]
        return output

    def __thread_download_wrapper(self, i_item, item,
                                  item_local_path, item_local_filepath,
                                  save_locally, download_options, annotation_options,
                                  status, output, success, errors,
                                  progress):
        try:
            download = False
            for i_try in range(download_options['num_tries']):
                logger.debug('download item: {}, try {}'.format(item.id, i_try))
                download = self.__thread_download(item=item,
                                                  save_locally=save_locally,
                                                  local_path=item_local_path,
                                                  local_filepath=item_local_filepath,
                                                  download_options=download_options,
                                                  annotation_options=annotation_options,
                                                  verbose=False,
                                                  show_progress=True)
                if download:
                    break
            if not download:
                raise self.items_repository.client_api.platform_exception
            status[i_item] = 'download'
            output[i_item] = download
            success[i_item] = True
        except Exception as err:
            status[i_item] = 'error'
            output[i_item] = item.id
            success[i_item] = False
            errors[i_item] = '%s\n%s' % (err, traceback.format_exc())
        finally:
            progress.queue.put((status[i_item],))

    def download_annotations(self, dataset, local_path, overwrite=False):
        """
        Download annotations json for entire dataset

        :param dataset: optional - search by name
        :param overwrite:
        :param local_path:
        :return:
        """
        # create local path to download and save to
        if local_path.endswith('/*') or local_path.endswith(r'\*'):
            # if end with * download directly to folder
            local_path = local_path[:-2]
        else:
            local_path = os.path.join(local_path, 'json')

        if not os.path.isdir(local_path) or os.path.isdir(local_path) and overwrite:
            # if folder not exists OR (exists and overwrite)
            # get zip from platform
            success, response = self.items_repository.client_api.gen_request(
                req_type='get',
                path='/datasets/%s/annotations/zip' % dataset.id)

            if not success:
                # platform error
                logger.exception('Downloading annotations zip')
                raise PlatformException(response)
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
                logger.exception('Getting annotations from zip ')
                raise
            finally:
                # cleanup
                if os.path.isfile(annotations_zip):
                    os.remove(annotations_zip)

    @staticmethod
    def __download_img_annotations(item, img_filepath, local_path, download_options, annotation_options):
        if local_path.endswith('/image') or local_path.endswith('\\image'):
            local_path = os.path.dirname(local_path)
        overwrite = download_options['overwrite']
        if download_options['relative_path']:
            annotation_rel_path = item.filename[1:]
        else:
            annotation_rel_path = item.name
        # find annotations json
        annotations_json_filepath = os.path.join(local_path, 'json', item.filename[1:])
        name, _ = os.path.splitext(annotations_json_filepath)
        annotations_json_filepath = name + '.json'
        if os.path.isfile(annotations_json_filepath):
            # if exists take from json file
            with open(annotations_json_filepath, 'r') as f:
                data = json.load(f)
            if 'annotations' in data:
                data = data['annotations']
            annotations = entities.AnnotationCollection.from_json(_json=data,
                                                                  item=item)
        else:
            # get from platform
            annotations = item.annotations.list()
        if item.width is not None and item.height is not None:
            img_shape = (item.height, item.width)
        else:
            img_shape = Image.open(img_filepath).size[::-1]

        for option in annotation_options:
            annotation_filepath = os.path.join(local_path, option, annotation_rel_path)
            if not os.path.isdir(os.path.dirname(annotation_filepath)):
                os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
            temp_path, ext = os.path.splitext(annotation_filepath)

            if option == 'json':
                if os.path.isfile(annotations_json_filepath):
                    continue
                annotations.download(filepath=annotations_json_filepath,
                                     annotation_format=option,
                                     height=img_shape[0],
                                     width=img_shape[1])
            elif option in ['mask', 'instance']:

                annotation_filepath = temp_path + '.png'
                if not os.path.isfile(annotation_filepath) or (os.path.isfile(annotation_filepath) and overwrite):
                    # if not exists OR (exists AND overwrite)
                    if not os.path.exists(os.path.dirname(annotation_filepath)):
                        # create folder if not exists
                        os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
                    annotations.download(filepath=annotation_filepath,
                                         annotation_format=option,
                                         height=img_shape[0],
                                         width=img_shape[1])
            else:
                raise PlatformException('400', 'Unknown annotation option: {}'.format(option))

    @staticmethod
    def __get_local_filepath(local_path, item, download_options):
        # create paths
        if local_path is None:
            # create default local file
            local_path = os.path.join(os.path.expanduser('~'),
                                      '.dataloop',
                                      'datasets',
                                      item.dataset.id,
                                      'image')
            if download_options['relative_path']:
                local_filepath = os.path.join(local_path, item.filename[1:])
            else:
                local_filepath = os.path.join(local_path, item.name)

        else:
            _, ext = os.path.splitext(local_path)
            if ext:
                # local_path is a filename
                local_filepath = local_path
                local_path = os.path.dirname(local_filepath)
            else:
                # if directory - get item's filename
                if download_options['to_images_folder']:
                    local_path = os.path.join(local_path, 'image')
                if download_options['relative_path']:
                    local_filepath = os.path.join(local_path, item.filename[1:])
                else:
                    local_filepath = os.path.join(local_path, item.name)
        return local_path, local_filepath

    def __thread_download(self, item,
                          save_locally, local_path, local_filepath,
                          chunk_size=8192, download_options=None,
                          download_item=True, annotation_options=None,
                          verbose=True, show_progress=False):
        """
        Get a single item's binary data
        Calling this method will returns the item body itself , an image for example with the proper mimetype.

        :param item: Item entity to download
        :param save_locally: bool. save to file or return buffer
        :param local_path: local folder or filename to save to.
         to folder. else - an "images" folder will be create for the images
        :param chunk_size:
        :param verbose:
        :param show_progress:
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param download_item:
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :return:
        """
        try:
            # default settings
            if annotation_options is None:
                annotation_options = list()
            if download_options is None:
                download_options = DEFAULT_DOWNLOAD_OPTIONS
            else:
                if not isinstance(download_options, dict):
                    raise PlatformException('400', '"download_options" must be a dict. {<option>:<value>}')
                tmp_options = DEFAULT_DOWNLOAD_OPTIONS
                for key, val in download_options.items():
                    if key not in tmp_options:
                        raise PlatformException(
                            error='400',
                            message='unknown download option: %s. known: %s' % (key, list(tmp_options.keys()))
                        )
                    tmp_options[key] = val
                download_options = tmp_options
            overwrite = False
            if 'overwrite' in download_options and download_options['overwrite']:
                overwrite = True

            # check if need to download image binary from platform
            if save_locally:
                # save
                if download_item:
                    # get image
                    if os.path.isfile(local_filepath):
                        # local file exists
                        if overwrite:
                            # overwrite local file
                            need_to_download = True
                        else:
                            need_to_download = False
                    else:
                        # local file is missing
                        need_to_download = True
                else:
                    need_to_download = False
            else:
                # get image buffer
                need_to_download = True

            response = None
            if need_to_download:
                result, response = self.items_repository.client_api.gen_request(req_type='get',
                                                                                path='/datasets/%s/items/%s/stream' % (
                                                                                    item.dataset.id, item.id),
                                                                                stream=True)
                if not result:
                    raise PlatformException(response)

            if save_locally:
                # download
                if download_item:
                    if not os.path.isfile(local_filepath) or (os.path.isfile(local_filepath) and overwrite):
                        # if not exists OR (exists AND overwrite)
                        if not os.path.exists(os.path.dirname(local_filepath)):
                            # create folder if not exists
                            os.makedirs(os.path.dirname(local_filepath), exist_ok=True)
                        # download and save locally
                        if show_progress:
                            total_length = response.headers.get('content-length')
                            pbar = ProgressBar(
                                widgets=[' [', Timer(), '] ', Bar(), FormatLabel(item.name), ' (', FileTransferSpeed(),
                                         ' | ', DataSize(), ' | ', Percentage(), ' | ', ETA(), ')'])
                            pbar.max_value = int(total_length)
                            dl = 0
                        else:
                            pbar = None
                            dl = None
                        with open(local_filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:  # filter out keep-alive new chunks
                                    if show_progress:
                                        dl += len(chunk)
                                        pbar.update(dl, force=True)
                                    f.write(chunk)
                            if show_progress:
                                pbar.finish()

                # save to output variable
                data = local_filepath
                # if image - can download annotation mask
                if 'image' in item.mimetype and item.annotated:
                    if annotation_options:
                        self.__download_img_annotations(item=item,
                                                        img_filepath=local_filepath,
                                                        download_options=download_options,
                                                        annotation_options=annotation_options,
                                                        local_path=local_path)
            else:
                # save as byte stream
                data = io.BytesIO()
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        data.write(chunk)
                # go back to the beginning of the stream
                data.seek(0)
                data.name = item.name
            return data
        except Exception as e:
            if verbose:
                logger.exception(e)
            raise


class Progress(threading.Thread):
    """
    Progressing class for downloading and uploading items
    """

    def __init__(self, max_val, progress_type):
        threading.Thread.__init__(self)
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
                logger.exception(e)
                logger.exception(traceback.format_exc())
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
                    logger.exception('Unknown message type: %s', msg)
                    # update bar
                self.progressbar.update(self.download + self.exist)
            except Exception as error:
                logger.exception(error)
            finally:
                self.queue.task_done()

    def run(self):
        if self.progress_type == 'upload':
            self.run_upload()
        elif self.progress_type == 'download':
            self.run_download()
        else:
            assert False
