import io
import os
import json
import logging
import numpy as np
from PIL import Image
import fleep
import queue
import threading
from urllib.parse import urlencode
from progressbar import Bar, ETA, ProgressBar, Timer, FileTransferSpeed, DataSize

from .. import entities, services


class Items:
    """
    Items repository
    """

    def __init__(self, dataset):
        self.logger = logging.getLogger('dataloop.repositories.items')
        self.client_api = services.ApiClient()
        self.dataset = dataset

    def get_list(self, query, page_offset, page_size):
        """
        Get dataset items list This is a browsing endpoint, for any given path item count will be returned,
        user is expected to perform another request then for every folder item to actually get the its item list.

        :param query: Query entity or a dictionary containing query parameters
        :param page_offset: starting page number
        :param page_size: number of items in each page
        :return:
        """
        # create query string
        # using path for backward compatibility
        if query is None:
            # default value
            query = entities.Query()(filename='/')
        if isinstance(query, dict):
            query = entities.Query().from_dict(query)
        elif isinstance(query, entities.Query):
            pass
        else:
            self.logger.exception('Unknown query type: %s' % type(query))
            raise ValueError('Unknown query type: %s' % type(query))

        query_string = urlencode(
            {'query': json.dumps(query.to_dict(), separators=(',', ':')), 'pageOffset': page_offset,
             'pageSize': page_size}).replace('%3A', ':').replace('%2F', '/').replace('%2C', ',')

        # prepare request
        success = self.client_api.gen_request(req_type='get',
                                              path='/datasets/%s/items?%s' % (self.dataset.id, query_string))
        if not success:
            self.logger.exception('Getting items list. dataset id: %d' % self.dataset.id)
            assert False
        try:
            self.client_api.print_json(self.client_api.last_response.json()['items'])
            self.logger.debug('Page:%d/%d' % (1 + page_offset, self.client_api.last_response.json()['totalPagesCount']))
        except ValueError:
            # no JSON returned
            pass

        return self.client_api.last_response.json()

    def list(self, query=None, page_offset=0, page_size=100):
        """
        List items

        :param query: Query entity or a dictionary containing query parameters
        :param page_offset:
        :param page_size:
        :return: Pages object
        """
        paged = entities.PagedEntities(items=self, query=query, page_offset=page_offset, page_size=page_size)
        paged.get_page()
        return paged

    def get(self, filepath=None, item_id=None):
        """
        Get Item object

        :param filepath: optional - search by remote path
        :param item_id: optional - search by id
        :return:
        """
        if item_id is not None:
            success = self.client_api.gen_request('get', '/datasets/%s/items/%s' % (self.dataset.id, item_id))
            if success:
                item = entities.Item(entity_dict=self.client_api.last_response.json(), dataset=self.dataset)
            else:
                self.logger.exception(
                    'Unable to get info from item. dataset id: %s, item id: %s' % (self.dataset.id, item_id))
                raise self.client_api.platform_exception
        elif filepath is not None:
            paged_entity = self.list(entities.Query()(filename=filepath))
            if len(paged_entity.items) == 0:
                self.logger.debug('Item not found. filename: %s' % filepath)
                item = None
            elif len(paged_entity.items) > 1:
                self.logger.warning('More than one item with same name. Please "get" by id')
                raise ValueError('More than one item with same name. Please "get" by id')
            else:
                item = paged_entity.items[0]
        else:
            self.logger.exception('Must choose by at least one. "filename" or "item_id"')
            raise ValueError('Must choose by at least one. "filename" or "item_id"')
        return item

    def download(self, filepath=None, item_id=None,
                 save_locally=True, local_path=None,
                 chunk_size=8192, download_options=None,
                 download_img=True, download_mask=False, download_img_mask=False, download_instance=False,
                 verbose=True, thickness=1, opacity=0.5):
        """
        Get a single item's binary data
        Calling this method will returns the item body itself , an image for example with the proper mimetype.

        :param filepath: optional - search item by remote path
        :param item_id: optional - search item by id
        :param save_locally: bool. save to file or return buffer
        :param local_path: path to save downloaded items
        :param download_options: 'merge' or 'overwrite'
        :param download_img: force download image
        :param download_mask: download annotations as mask
        :param download_img_mask: download annotations on image
        :param download_instance: download annotations as instances - annotations id for each label
        :param verbose: log exceptions
        :param thickness: line thickness for polygon etc
        :param opacity: alpha level when blending mask and image
        :param chunk_size:
        :return:
        """
        try:
            # get items
            item = self.get(filepath=filepath, item_id=item_id)
            if item is None:
                # no item to download
                return
            if item.type == 'dir':
                # item is directory
                return
            local_image_filename = None
            local_mask_filename = None
            local_instance_filename = None
            local_img_mask_filename = None
            if save_locally:
                # create paths
                if local_path is None:
                    # create default local file
                    main_dataset_path = self.dataset.__get_local_path__()
                    local_image_filename = os.path.join(main_dataset_path, 'images', item.filename[1:])
                    local_mask_filename = os.path.join(main_dataset_path, 'mask', item.filename[1:])
                    local_instance_filename = os.path.join(main_dataset_path, 'instance', item.filename[1:])
                    local_img_mask_filename = os.path.join(main_dataset_path, 'img_mask', item.filename[1:])
                else:
                    # check if input is file or directory
                    _, ext = os.path.splitext(local_path)
                    if not ext:
                        # if directory - get item's filename
                        local_image_filename = os.path.join(local_path, item.filename[1:])
                        local_dir = local_path
                    else:
                        local_image_filename = local_path
                        local_dir = os.path.dirname(local_image_filename)
                    local_mask_filename = os.path.join(local_dir, 'mask', item.filename[1:])
                    local_instance_filename = os.path.join(local_dir, 'instance', item.filename[1:])
                    local_img_mask_filename = os.path.join(local_dir, 'img_mask', item.filename[1:])

            overwrite = False
            if download_options == 'overwrite':
                overwrite = True

            # check if need to download image binary from platform
            if save_locally:
                # save
                if download_img:
                    # get image
                    if os.path.isfile(local_image_filename):
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

            resp = None
            if need_to_download:
                result = self.client_api.gen_request(req_type='get',
                                                     path='/datasets/%s/items/%s/stream' % (item.dataset.id, item.id),
                                                     stream=True)
                if result:
                    resp = self.client_api.last_response
                else:
                    raise self.client_api.platform_exception

            if save_locally:
                # download
                if download_img:
                    if not os.path.isfile(local_image_filename) or \
                            (os.path.isfile(local_image_filename) and overwrite):
                        if not os.path.exists(os.path.dirname(local_image_filename)):
                            os.makedirs(os.path.dirname(local_image_filename), exist_ok=True)
                        # download and save locally
                        with open(local_image_filename, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=chunk_size):
                                if chunk:  # filter out keep-alive new chunks
                                    f.write(chunk)
                # save to output variable
                data = local_image_filename
                # if image - can download annotation mask
                if 'image' in item.mimetype:
                    # get image size without opening it
                    if item.width is None or item.height is None:
                        img_shape = Image.open(data).size[::-1]
                    else:
                        img_shape = (item.height, item.width)

                    if download_mask:
                        temp_path, ext = os.path.splitext(local_mask_filename)
                        local_mask_filename = temp_path + '.png'
                        if not os.path.isfile(local_mask_filename) or \
                                (os.path.isfile(local_mask_filename) and overwrite):
                            # file doesnt exists or (file exists and overwrite)
                            if not os.path.exists(os.path.dirname(local_mask_filename)):
                                os.makedirs(os.path.dirname(local_mask_filename), exist_ok=True)
                            item.annotations.download(filepath=local_mask_filename,
                                                      get_mask=True,
                                                      img_shape=img_shape,
                                                      thickness=thickness)

                    if download_instance:
                        temp_path, ext = os.path.splitext(local_instance_filename)
                        local_instance_filename = temp_path + '.png'
                        if not os.path.isfile(local_instance_filename) or \
                                (os.path.isfile(local_instance_filename) and overwrite):
                            # file doesnt exists or (file exists and overwrite)
                            if not os.path.exists(os.path.dirname(local_instance_filename)):
                                os.makedirs(os.path.dirname(local_instance_filename), exist_ok=True)
                            item.annotations.download(filepath=local_instance_filename,
                                                      get_instance=True,
                                                      img_shape=img_shape,
                                                      thickness=thickness)

                    if download_img_mask:
                        temp_path, ext = os.path.splitext(local_img_mask_filename)
                        local_img_mask_filename = temp_path + '.png'
                        if not os.path.isfile(local_img_mask_filename) or \
                                (os.path.isfile(local_img_mask_filename) and overwrite):
                            # file doesnt exists or (file exists and overwrite)
                            if not os.path.exists(os.path.dirname(local_img_mask_filename)):
                                # create folder
                                os.makedirs(os.path.dirname(local_img_mask_filename), exist_ok=True)
                            mask = item.annotations.to_mask(img_shape=img_shape, thickness=thickness, with_text=False)
                            img = Image.open(data).convert('RGBA')
                            # set opacity
                            mask[:, :, 3] = mask[:, :, 3] * opacity
                            # create PIL
                            rgb_mask_img = Image.fromarray(mask.astype(np.uint8))
                            # combine with mask
                            img.paste(rgb_mask_img, (0, 0), rgb_mask_img)
                            img.save(local_img_mask_filename)

            else:
                # save as byte stream
                data = io.BytesIO()
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        data.write(chunk)
                # go back to the beginning of the stream
                data.seek(0)
            return data
        except Exception as e:
            if verbose:
                self.logger.exception(e)
            raise

    def upload(self, filepath, remote_path=None, uploaded_filename=None, callback=None, upload_options=None):
        """
        Upload an item to dataset

        :param filepath: local filepath of the item
        :param remote_path: remote directory of filepath to upload
        :param uploaded_filename: optional - remote filename
        :param callback:
        :param upload_options: 'merge' or 'overwrite'
        :return:
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
                    assert False
                if uploaded_filename is None:
                    uploaded_filename = os.path.basename(filepath)
                items = self.get(filepath=remote_path + uploaded_filename)
                if items is not None:
                    if upload_options == 'overwrite':
                        # delete remote item
                        self.delete(item_id=items.id)
                    else:
                        return items
                remote_url = '/datasets/%s/items' % self.dataset.id
                result = self.client_api.upload_local_file(filepath=filepath,
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
                items = self.get(filepath=remote_path + uploaded_filename)
                if items is not None:
                    if upload_options == 'overwrite':
                        # delete remote item
                        self.delete(item_id=items.id)
                    else:
                        return items
                # read mime type from buffer
                info = fleep.get(buffer.read(128))
                # go back to beginning of file
                buffer.seek(0)
                files = {'file': (uploaded_filename, buffer, info.mime)}
                payload = {'path': os.path.join(remote_path, uploaded_filename).replace('\\', '/'),
                           'type': 'file'}
                result = self.client_api.gen_request(req_type='post',
                                                     path='/datasets/%s/items' % self.dataset.id,
                                                     files=files,
                                                     data=payload)
            if result:
                return entities.Item(entity_dict=self.client_api.last_response.json(), dataset=self.dataset)
            else:
                self.logger.exception('error uploading')
                raise self.client_api.platform_exception
        except Exception as e:
            self.logger.exception(e)
            raise

    def delete(self, filename=None, item_id=None):
        """
        Delete item from platform

        :param filename: optional - search item by remote path
        :param item_id: optional - search item by if
        :return:
        """
        if item_id is not None:
            success = self.client_api.gen_request('delete', '/datasets/%s/items/%s' % (self.dataset.id, item_id))
        elif filename is not None:
            if not filename.startswith('/'):
                filename = '/' + filename
            items = self.get(filepath=filename)
            if len(items) != 1:
                assert False
            success = self.client_api.gen_request('delete', '/datasets/%s/items/%s' % (self.dataset.id, items[0].id))
        else:
            assert False
        return success

    def edit(self, item, system_metadata=False):
        """
        Edit items metadata

        :param item: Item object
        :param system_metadata: bool
        :return:
        """
        url_path = '/datasets/%s/items/%s' % (self.dataset.id, item.id)
        if system_metadata:
            url_path += '?system=true'
        success = self.client_api.gen_request('patch', url_path, json_req=item.to_dict())
        if success:
            return item
        else:
            self.logger.exception('editing item')
            assert False


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
