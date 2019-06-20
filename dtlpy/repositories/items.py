import io
import os
import json
import logging
from PIL import Image
import fleep
import queue
import threading
from urllib.parse import urlencode
from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize, Percentage, FormatLabel
from multiprocessing.pool import ThreadPool
import attr

from .. import entities, PlatformException, exceptions

DEFAULT_DOWNLOAD_OPTIONS = {'overwrite': False,
                            'relative_path': True}


@attr.s
class Items:
    """
    Items repository
    """
    client_api = attr.ib()
    dataset = attr.ib()
    logger = attr.ib(default=logging.getLogger('dataloop.repositories.items'))
    # set items entity to represent the item (Item, Package, Artifact etc...)
    items_entity = attr.ib(default=entities.Item)

    def set_items_entity(self, entity):
        if entity in [entities.Item, entities.Artifact, entities.Package]:
            self.items_entity = entity
        else:
            self.logger.exception('Unable to se to given entity. Entity give: %s' % entity)
            raise PlatformException('403', 'Unable to se to given entity.')

    def get_all_items(self):
        """
        Get all items in dataset

        :return: list of all items
        """
        page = self.list(filters=entities.Filters(itemType="file"))
        items = list()
        while True:
            for item in page.items:
                items.append(item)
            if page.has_next_page:
                page.next_page()
            else:
                break
        return items

    def create_query_string(self, filters, page_offset, page_size):
        """
        Create a platform filters string

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset: starting page number
        :param page_size: number of items in each page
        :return: filters string
        """
        # using path for backward compatibility
        if filters is None:
            # default value
            filters = entities.Filters(filenames='/')
        if isinstance(filters, dict):
            filters = entities.Filters.from_dict(filters)
        elif isinstance(filters, entities.Filters):
            pass
        else:
            self.logger.exception('Unknown filters type: %s' % type(filters))
            message = 'Unknown filters type: %s' % type(filters)
            raise PlatformException('404', message)

        return urlencode(
            {'query': json.dumps(filters.prepare(), separators=(',', ':')), 'pageOffset': page_offset,
             'pageSize': page_size}).replace('%3A', ':').replace('%2F', '/').replace('%2C', ',')

    def get_list(self, filters, page_offset, page_size):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset: starting page number
        :param page_size: number of items in each page
        :return: json response
        """
        # create filters string
        query_string = self.create_query_string(filters=filters, page_offset=page_offset, page_size=page_size)

        # prepare request
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/datasets/%s/items?%s' % (self.dataset.id, query_string))
        if not success:
            self.logger.exception('Getting items list. dataset id: %s' % self.dataset.id)
            raise PlatformException(response)
        try:
            self.client_api.print_json(response.json()['items'])
            self.logger.debug('Page:%d/%d' % (1 + page_offset, response.json()['totalPagesCount']))
        except ValueError:
            # no JSON returned
            pass

        return response.json()

    def list(self, filters=None, page_offset=0, page_size=100):
        """
        List items

        :param filters: Filters entity or a dictionary containing filters parameters
        :param page_offset:
        :param page_size:
        :return: Pages object
        """
        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=page_offset,
                                       page_size=page_size,
                                       client_api=self.client_api,
                                       item_entity=self.items_entity)
        paged.get_page()
        return paged

    def get(self, filepath=None, item_id=None):
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :return: Item object
        """
        if item_id is not None:
            success, response = self.client_api.gen_request(req_type='get',
                                                            path='/datasets/%s/items/%s' % (self.dataset.id, item_id))
            if success:
                item = self.items_entity.from_json(client_api=self.client_api,
                                                   _json=response.json(),
                                                   dataset=self.dataset)
            else:
                self.logger.exception(
                    'Unable to get info from item. dataset id: %s, item id: %s' % (self.dataset.id, item_id))
                raise PlatformException(response)
        elif filepath is not None:
            paged_entity = self.list(entities.Filters(filenames=filepath))
            if len(paged_entity.items) == 0:
                self.logger.debug('Item not found. filename: %s' % filepath)
                raise PlatformException('404', 'Item not found.')
            elif len(paged_entity.items) > 1:
                self.logger.warning('More than one item with same name. Please "get" by id')
                raise PlatformException('404', 'More than one item with same name. Please "get" by id')
            else:
                item = paged_entity.items[0]
        else:
            self.logger.exception('Must choose by at least one. "filename" or "item_id"')
            raise PlatformException('400', 'Must choose by at least one. "filename" or "item_id"')
        return item

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
        annotations_filepath = os.path.join(local_path, 'json', item.filename[1:])
        name, _ = os.path.splitext(annotations_filepath)
        annotations_filepath = name + '.json'
        if os.path.isfile(annotations_filepath):
            # if exists take from json file
            with open(annotations_filepath, 'r') as f:
                data = json.load(f)
            annotations = entities.AnnotationCollection.from_json(_json=data['annotations'], item=item)
        else:
            # get from platform
            annotations = item.annotations.list()
        if item.width is not None and item.height is not None:
            img_shape = (item.height, item.width)
        else:
            img_shape = Image.open(img_filepath).size[::-1]
        for option in annotation_options:
            if option == 'json':
                continue
            annotation_filepath = os.path.join(local_path, option, annotation_rel_path)
            temp_path, ext = os.path.splitext(annotation_filepath)
            annotation_filepath = temp_path + '.png'
            if not os.path.isfile(annotation_filepath) or (os.path.isfile(annotation_filepath) and overwrite):
                # if not exists OR (exists AND overwrite)
                if not os.path.exists(os.path.dirname(annotation_filepath)):
                    # create folder if not exists
                    os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
                annotations.download(filepath=annotation_filepath,
                                     annotation_format=option,
                                     height=img_shape[0], width=img_shape[1])

    def __download_binary(self):
        pass

    def __download_video(self):
        pass

    def download_batch(self, items,
                       save_locally=True, local_path=None,
                       chunk_size=8192, download_options=None,
                       download_item=True, annotation_options=None,
                       verbose=True, show_progress=False
                       ):
        """
        Download a batch of items

        :param items: list. items to be downloaded
        :param save_locally: bool. save to file or return buffer
        :param local_path: local folder or filename to save to. if folder ends with * images with be downloaded directly
         to folder. else - an "images" folder will be create for the images
        :param chunk_size:
        :param verbose:
        :param show_progress:
        :param download_options: {'overwrite': True/False, 'relative_path': True/False}
        :param download_item:
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :return: Output (list)
        """

        def download_single(i_w_item, w_item):
            try:
                data = self.download(item_id=w_item.id,
                                     save_locally=save_locally,
                                     local_path=local_path,
                                     chunk_size=chunk_size,
                                     download_options=download_options,
                                     download_item=download_item,
                                     annotation_options=annotation_options,
                                     verbose=verbose,
                                     show_progress=show_progress)
                outputs[i_w_item] = data
            except Exception as e:
                outputs[i_w_item] = w_item.id
                success[i_w_item] = False
                errors[i_w_item] = e

        pool = ThreadPool(processes=32)
        num_items = len(items)
        success = [None for _ in range(num_items)]
        errors = [None for _ in range(num_items)]
        outputs = [None for _ in range(num_items)]
        for i_item, item in enumerate(items):
            pool.apply_async(func=download_single,
                             kwds={'i_w_item': i_item,
                                   'w_item': item})
        # log error
        pool.close()
        pool.join()
        pool.terminate()
        [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        return outputs

    def download(self, filepath=None, item_id=None,
                 save_locally=True, local_path=None,
                 chunk_size=8192, download_options=None,
                 download_item=True, annotation_options=None,
                 verbose=True, show_progress=False):
        """
        Get a single item's binary data
        Calling this method will returns the item body itself , an image for example with the proper mimetype.

        :param filepath: optional - search item by remote path
        :param item_id: optional - search item by id
        :param save_locally: bool. save to file or return buffer
        :param local_path: local folder or filename to save to. if folder ends with * images with be downloaded directly
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
            # get items
            item = self.get(filepath=filepath, item_id=item_id)
            if item is None:
                # no item to download
                return
            if item.type == 'dir':
                # item is directory
                return
            if save_locally:
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
                    include_images_in_path = True
                    if local_path.endswith('/*') or local_path.endswith('\\*'):
                        # if end with * download directly to folder
                        local_path = local_path[:-2]
                        include_images_in_path = False
                    # check if input is file or directory
                    _, ext = os.path.splitext(local_path)
                    if ext:
                        # local_path is a filename
                        local_filepath = local_path
                        local_path = os.path.dirname(local_filepath)
                    else:
                        # if directory - get item's filename
                        if include_images_in_path:
                            local_path = os.path.join(local_path, 'image')
                        if download_options['relative_path']:
                            local_filepath = os.path.join(local_path, item.filename[1:])
                        else:
                            local_filepath = os.path.join(local_path, item.name)
            else:
                local_filepath = None

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
                result, response = self.client_api.gen_request(req_type='get',
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
                if 'image' in item.mimetype:
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
            return data
        except Exception as e:
            if verbose:
                self.logger.exception(e)
            raise

    def upload_batch(self, filepaths, remote_path=None, upload_options=None):
        """
        Upload a batch of item to dataset

        :param annotations_filepath: platform format annotations file to add to the new item
        :param filepaths: local filepath of the item, can be a directory or a list of item paths
        :param remote_path: remote directory of filepath to upload
        :param upload_options: 'merge' or 'overwrite'
        :return: Output (list)
        """

        def upload_single(i_w_filepath, w_filepath):
            try:
                item = self.upload(
                    filepath=w_filepath,
                    remote_path=remote_path,
                    upload_options=upload_options
                )
                outputs[i_w_filepath] = item
            except Exception as e:

                outputs[i_w_filepath] = w_filepath
                success[i_w_filepath] = False
                errors[i_w_filepath] = e

        # if filepaths is a directory - return all directory's file paths
        if isinstance(filepaths, str):
            filepaths = [os.path.join(filepaths, f.name) for f in os.scandir(filepaths) if f.is_file()]

        pool = ThreadPool(processes=32)
        num_items = len(filepaths)
        success = [None for _ in range(num_items)]
        errors = [None for _ in range(num_items)]
        outputs = [None for _ in range(num_items)]
        for i_filepath, filepath in enumerate(filepaths):
            pool.apply_async(func=upload_single,
                             kwds={'i_w_filepath': i_filepath,
                                   'w_filepath': filepath})
        # log error
        pool.close()
        pool.join()
        pool.terminate()
        [self.logger.exception(errors[i_job]) for i_job, suc in enumerate(success) if suc is False]
        return outputs

    def upload(self, filepath, annotations_filepath=None, remote_path=None, uploaded_filename=None, callback=None,
               upload_options=None):
        """
        Upload an item to dataset

        :param annotations_filepath: platform format annotations file to add to the new item
        :param filepath: local filepath of the item
        :param remote_path: remote directory of filepath to upload
        :param uploaded_filename: optional - remote filename
        :param callback:
        :param upload_options: 'merge' or 'overwrite'
        :return: Item object
        """
        try:
            if upload_options is None:
                upload_options = 'merge'
            if remote_path is None:
                remote_path = '/'
            if not remote_path.endswith('/'):
                remote_path += '/'
            if isinstance(filepath, str):
                if not os.path.isfile(filepath):
                    self.logger.exception('Filepath doesnt exists. file: %s' % filepath)
                    message = 'Filepath doesnt exists. file: %s' % filepath
                    raise PlatformException('404', message)
                if uploaded_filename is None:
                    uploaded_filename = os.path.basename(filepath)
                name = '^' + remote_path + uploaded_filename + '$'
                try:
                    item_get = self.get(filepath=name)
                    if upload_options == 'overwrite':
                        # delete remote item
                        self.delete(item_id=item_get.id)
                    else:
                        return item_get
                except exceptions.NotFound:
                    pass
                remote_url = '/datasets/%s/items' % self.dataset.id
                result, response = self.client_api.upload_local_file(filepath=filepath,
                                                                     remote_url=remote_url,
                                                                     uploaded_filename=uploaded_filename,
                                                                     remote_path=remote_path,
                                                                     callback=callback)
            else:
                if isinstance(filepath, bytes):
                    # item is  bytes array
                    buffer = io.BytesIO(filepath)
                elif isinstance(filepath, io.BytesIO):
                    # item is  bytes array
                    buffer = filepath
                elif isinstance(filepath, io.BufferedReader):
                    # files = {'file': item, 'mimetype': 'image/jpeg'}
                    buffer = filepath
                else:
                    assert False, 'unknown file type'

                if uploaded_filename is None:
                    if hasattr(filepath, 'name'):
                        uploaded_filename = filepath.name
                    else:
                        if uploaded_filename is None:
                            self.logger.exception('Must have filename when uploading bytes array (uploaded_filename)')
                            raise ValueError('Must have filename when uploading bytes array (uploaded_filename)')
                try:
                    items = self.get(filepath=remote_path + uploaded_filename)
                    if upload_options == 'overwrite':
                        # delete remote item
                        self.delete(item_id=items.id)
                    else:
                        return items
                except exceptions.NotFound:
                    pass
                # read mime type from buffer
                info = fleep.get(buffer.read(128))
                # go back to beginning of file
                buffer.seek(0)
                files = {'file': (uploaded_filename, buffer, info.mime[0])}
                payload = {'path': os.path.join(remote_path, uploaded_filename).replace('\\', '/'),
                           'type': 'file'}
                result, response = self.client_api.gen_request(req_type='post',
                                                               path='/datasets/%s/items' % self.dataset.id,
                                                               files=files,
                                                               data=payload)
            if result:
                item = self.items_entity.from_json(client_api=self.client_api,
                                                   _json=response.json(),
                                                   dataset=self.dataset)
                if annotations_filepath is not None and os.path.isfile(annotations_filepath):
                    try:
                        with open(annotations_filepath, 'r') as f:
                            data = json.load(f)
                        if 'annotations' in data:
                            item.annotations.upload(annotations=data['annotations'])
                    except Exception:
                        msg = 'bad formatting of annotations file. cant upload, item_id: %s, annotations_filepath: %s' \
                              % (item.id, annotations_filepath)
                        self.logger.exception(msg=msg)
                self.logger.debug('Item uploaded successfully. Item id: %s' % item.id)
                return item
            else:
                self.logger.exception('error uploading')
                raise PlatformException(response)
        except Exception as e:
            self.logger.exception(e)
            raise

    def delete(self, filename=None, item_id=None):
        """
        Delete item from platform

        :param filename: optional - search item by remote path
        :param item_id: optional - search item by if
        :return: True
        """
        if item_id is not None:
            success, response = self.client_api.gen_request(req_type='delete',
                                                            path='/datasets/%s/items/%s' % (self.dataset.id, item_id))
        elif filename is not None:
            if not filename.startswith('/'):
                filename = '/' + filename
            items = self.get(filepath=filename)
            if not isinstance(items, list):
                items = [items]
            if len(items) == 0:
                raise PlatformException('404', 'Item not found')
            elif len(items) > 1:
                raise PlatformException('404', 'More the 1 item exist by the name provided')
            else:
                item_id = items[0].id
                success, response = self.client_api.gen_request(req_type='delete',
                                                                path='/datasets/%s/items/%s' % (
                                                                    self.dataset.id, item_id))
        else:
            raise PlatformException('400', 'Must provide item id or filename')
        if success:
            self.logger.debug('Item was deleted successfully. Item id: %s' % item_id)
            return success
        else:
            raise PlatformException(response)

    def update(self, item, system_metadata=False):
        """
        Update items metadata

        :param item: Item object
        :param system_metadata: bool
        :return: Item object
        """
        url_path = '/datasets/%s/items/%s' % (self.dataset.id, item.id)
        if system_metadata:
            url_path += '?system=true'
        success, response = self.client_api.gen_request(req_type='patch',
                                                        path=url_path,
                                                        json_req=item.to_json())
        if success:
            self.logger.debug('Item was updated successfully. Item id: %s' % item.id)
            return self.items_entity.from_json(client_api=self.client_api, _json=response.json(), dataset=self.dataset)
        else:
            self.logger.exception('Error while updating item')
            raise PlatformException(response)


class Progress(threading.Thread):
    def __init__(self, num_files):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('dataloop.repositories.items.progressbar')
        self.progressbar = None
        self.queue = queue.Queue(maxsize=0)
        self.progressbar_init(num_files=num_files)
        self.success = 0
        self.exist = 0
        self.error = 0

    def progressbar_init(self, num_files):
        self.progressbar = ProgressBar(widgets=[' [', Timer(), '] ', Bar(), ' (', ETA(), ')'])
        self.progressbar.max_value = num_files

    def finish(self):
        self.progressbar.finish()

    def run(self):
        self.success = 0
        self.exist = 0
        self.error = 0
        while True:
            try:
                # get item from queue
                decoded_body = self.queue.get()
                msg, = decoded_body
                if msg is None:
                    self.progressbar.finish()
                    break
                if msg == 'success':
                    self.success += 1
                elif msg == 'exist':
                    self.exist += 1
                elif msg == 'error':
                    self.error += 1
                else:
                    self.logger.exception('Unknown message type: %s' % msg)
                    # update bar
                self.progressbar.update(self.success + self.exist)
            except Exception as error:
                self.logger.exception(error)
            finally:
                self.queue.task_done()
