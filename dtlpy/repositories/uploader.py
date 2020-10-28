import validators
import traceback
import tempfile
import requests
import asyncio
import logging
import pandas
import shutil
import json
import time
import tqdm
import os
import io
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from PIL import Image

from .. import PlatformException, entities, repositories
from ..services import Reporter

logger = logging.getLogger(name=__name__)

NUM_TRIES = 5  # try to upload 3 time before fail on item


class UploadElement:
    def __init__(self,
                 element_type,
                 buffer,
                 remote_filepath,
                 annotations_filepath,
                 remote_name=None,
                 link_dataset_id=None,
                 item_metadata=None):
        self.type = element_type
        self.buffer = buffer
        self.remote_filepath = remote_filepath
        self.remote_name = remote_name
        self.item_metadata = item_metadata
        self.exists_in_remote = False
        self.checked_in_remote = False
        self.annotations_filepath = annotations_filepath
        self.link_dataset_id = link_dataset_id


class Uploader:
    def __init__(self, items_repository: repositories.Items):
        assert isinstance(items_repository, repositories.Items)
        self.items_repository = items_repository
        self.__stop_create_existence_dict = False

    def upload(
            self,
            # what to upload
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path=None,
            remote_name=None,
            file_types=None,
            num_workers=None,
            overwrite=False,
            item_metadata=None
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param overwrite: optional - default = False
        :param local_path: local file or folder to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param remote_name: remote base name to save.
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers: NOT USED deprecated
        :param item_metadata: upload the items with the metadata dictionary
        :return: Output (list)
        """
        ###################
        # Default options #
        ###################
        mode = 'skip'
        if overwrite:
            mode = 'overwrite'
        if num_workers is not None:
            logger.warning('[DeprecationWarning] input argument "num_workers"'
                           ' will be deprecated from upload() after version 1.17.0\n'
                           'To set number of processes use "dtlpy.client_api.num_processes=int()"')
            self.items_repository._client_api.num_processes = num_workers

        if isinstance(local_path, pandas.DataFrame):
            elements = self._build_elements_from_df(local_path)
        else:
            elements = self._build_elements_from_inputs(local_path=local_path,
                                                        local_annotations_path=local_annotations_path,
                                                        # upload options
                                                        remote_path=remote_path,
                                                        remote_name=remote_name,
                                                        file_types=file_types,
                                                        item_metadata=item_metadata)
        num_files = len(elements)
        logger.info("Uploading {} items..".format(num_files))
        reporter = Reporter(num_workers=num_files, resource=Reporter.ITEMS_UPLOAD)
        disable_pbar = self.items_repository._client_api.verbose.disable_progress_bar or num_files == 1
        pbar = tqdm.tqdm(total=num_files, disable=disable_pbar)
        futures = [None for _ in range(num_files)]
        for i_item in range(num_files):
            element = elements[i_item]
            # upload
            futures[i_item] = asyncio.run_coroutine_threadsafe(
                self.__upload_single_item_wrapper(i_item=i_item,
                                                  element=element,
                                                  mode=mode,
                                                  pbar=pbar,
                                                  reporter=reporter),
                loop=self.items_repository._client_api.event_loops('items.upload').loop)

        _ = [future.result() for future in futures]
        pbar.close()
        # summary
        logger.info("Number of total files: {}".format(num_files))
        for action in reporter.status_list:
            n_for_action = reporter.status_count(status=action)
            logger.info("Number of files {}: {}".format(action, n_for_action))

        # log error
        errors_count = reporter.failure_count
        if errors_count > 0:
            log_filepath = reporter.generate_log_files()
            logger.warning("Errors in {n_error} files. See {log_filepath} for full log".format(
                n_error=errors_count, log_filepath=log_filepath))

        # TODO 2.0 always return a list
        return reporter.output

    def _build_elements_from_inputs(self,
                                    local_path,
                                    local_annotations_path,
                                    # upload options
                                    remote_path,
                                    file_types,
                                    remote_name,
                                    item_metadata):
        if remote_path is None:
            remote_path = '/'
        if not remote_path.endswith("/"):
            remote_path += "/"
        if file_types is not None and not isinstance(file_types, list):
            msg = '"file_types" should be a list of file extension. e.g [".jpg", ".png"]'
            raise PlatformException(error="400", message=msg)
        if item_metadata is not None:
            if not isinstance(item_metadata, dict):
                msg = '"item_metadata" should be a metadata dictionary. Got type: {}'.format(type(item_metadata))
                raise PlatformException(error="400", message=msg)

        ##########################
        # Convert inputs to list #
        ##########################
        local_annotations_path_list = None
        remote_name_list = None
        if not isinstance(local_path, list):
            local_path_list = [local_path]
            if remote_name is not None:
                if not isinstance(remote_name, str):
                    raise PlatformException(error="400",
                                            message='remote_name must be a string, got: {}'.format(type(remote_name)))
                remote_name_list = [remote_name]
            if local_annotations_path is not None:
                if not isinstance(local_annotations_path, str):
                    raise PlatformException(error="400",
                                            message='local_annotations_path must be a string, got: {}'.format(
                                                type(local_annotations_path)))
                local_annotations_path_list = [local_annotations_path]
        else:
            local_path_list = local_path
            if remote_name is not None:
                if not isinstance(remote_name, list):
                    raise PlatformException(error="400",
                                            message='remote_name must be a list, got: {}'.format(type(remote_name)))
                if not len(remote_name) == len(local_path_list):
                    raise PlatformException(error="400",
                                            message='remote_name and local_path_list must be of same length. '
                                                    'Received: remote_name: {}, '
                                                    'local_path_list: {}'.format(len(remote_name),
                                                                                 len(local_path_list)))
                remote_name_list = remote_name
            if local_annotations_path is not None:
                if not len(local_annotations_path) == len(local_path_list):
                    raise PlatformException(error="400",
                                            message='local_annotations_path and local_path_list must be of same lenght.'
                                                    ' Received: local_annotations_path: {}, '
                                                    'local_path_list: {}'.format(len(local_annotations_path),
                                                                                 len(local_path_list)))
                local_annotations_path_list = local_annotations_path

        if local_annotations_path is None:
            local_annotations_path_list = [None] * len(local_path_list)

        if remote_name is None:
            remote_name_list = [None] * len(local_path_list)

        elements = list()
        total_size = 0
        for upload_item_element, remote_name, upload_annotations_element in zip(local_path_list, remote_name_list,
                                                                                local_annotations_path_list):
            if isinstance(upload_item_element, np.ndarray):
                # convert numpy.ndarray to io.BytesI
                if remote_name is None:
                    raise PlatformException(
                        error="400",
                        message='Upload element type was numpy.ndarray. providing param "remote_name" is mandatory')
                file_extension = os.path.splitext(remote_name)
                if file_extension[1].lower() in ['.jpg', '.jpeg']:
                    item_format = 'JPEG'
                elif file_extension[1].lower() == '.png':
                    item_format = 'PNG'
                else:
                    raise PlatformException(
                        error="400",
                        message='"remote_name" with  .jpg/.jpeg or .png extension are supported '
                                'when upload element of numpy.ndarray type.')

                buffer = io.BytesIO()
                Image.fromarray(upload_item_element).save(buffer, format=item_format)
                buffer.seek(0)
                buffer.name = remote_name
                upload_item_element = buffer

            if isinstance(upload_item_element, str):
                with_head_folder = True
                if upload_item_element.endswith('*'):
                    with_head_folder = False
                    upload_item_element = os.path.dirname(upload_item_element)

                if os.path.isdir(upload_item_element):
                    # create a list of all the items to upload
                    for root, subdirs, files in os.walk(upload_item_element):
                        for filename in files:
                            _, ext = os.path.splitext(filename)
                            if file_types is None or ext in file_types:
                                filepath = os.path.join(root, filename)  # get full image filepath
                                # extract item's size
                                total_size += os.path.getsize(filepath)
                                # get annotations file
                                if upload_annotations_element is not None:
                                    # change path to annotations
                                    annotations_filepath = filepath.replace(upload_item_element,
                                                                            upload_annotations_element)
                                    # remove image extension
                                    annotations_filepath, _ = os.path.splitext(annotations_filepath)
                                    # add json extension
                                    annotations_filepath += ".json"
                                else:
                                    annotations_filepath = None
                                if with_head_folder:
                                    remote_filepath = remote_path + os.path.relpath(filepath, os.path.dirname(
                                        upload_item_element))
                                else:
                                    remote_filepath = remote_path + os.path.relpath(filepath, upload_item_element)
                                element = UploadElement(element_type='file',
                                                        buffer=filepath,
                                                        remote_filepath=remote_filepath.replace("\\", "/"),
                                                        annotations_filepath=annotations_filepath,
                                                        item_metadata=item_metadata)
                                elements.append(element)

                # add single file
                elif os.path.isfile(upload_item_element):
                    filepath = upload_item_element
                    # extract item's size
                    total_size += os.path.getsize(filepath)
                    # determine item's remote base name
                    if remote_name is None:
                        remote_name = os.path.basename(filepath)
                    # get annotations file
                    if upload_annotations_element is not None:
                        # change path to annotations
                        annotations_filepath = filepath.replace(upload_item_element, upload_annotations_element)
                        # remove image extension
                        annotations_filepath, _ = os.path.splitext(annotations_filepath)
                        # add json extension
                        annotations_filepath += ".json"
                    else:
                        annotations_filepath = None
                    # append to list
                    remote_filepath = remote_path + remote_name
                    element = UploadElement(element_type='file',
                                            buffer=filepath,
                                            remote_filepath=remote_filepath,
                                            annotations_filepath=annotations_filepath,
                                            item_metadata=item_metadata)
                    elements.append(element)
                elif self.is_url(upload_item_element):
                    # noinspection PyTypeChecker
                    if remote_name is None:
                        remote_name = str(upload_item_element.split('/')[-1])
                    remote_filepath = remote_path + remote_name

                    element = UploadElement(element_type='url',
                                            buffer=upload_item_element,
                                            remote_filepath=remote_filepath,
                                            annotations_filepath=upload_annotations_element,
                                            item_metadata=item_metadata)
                    elements.append(element)
                else:
                    raise PlatformException("404", "Unknown local path: {}".format(local_path))
            elif isinstance(upload_item_element, entities.Item):
                link = entities.Link(ref=upload_item_element.id, type='id', dataset_id=upload_item_element.datasetId,
                                     name='{}_link.json'.format(upload_item_element.name))
                if remote_name is None:
                    remote_name = link.name

                remote_filepath = '{}{}'.format(remote_path, remote_name)

                element = UploadElement(element_type='link',
                                        buffer=link,
                                        remote_filepath=remote_filepath,
                                        annotations_filepath=upload_annotations_element,
                                        item_metadata=item_metadata)
                elements.append(element)
            elif isinstance(upload_item_element, entities.Link):
                if remote_name is None:
                    remote_name = upload_item_element.name

                remote_filepath = '{}{}_link.json'.format(remote_path, remote_name)

                element = UploadElement(element_type='link',
                                        buffer=upload_item_element,
                                        remote_filepath=remote_filepath,
                                        annotations_filepath=upload_annotations_element,
                                        item_metadata=item_metadata)
                elements.append(element)
            elif isinstance(upload_item_element, entities.Similarity):
                if remote_name:
                    upload_item_element.name = remote_name
                if upload_item_element.name is None:
                    upload_item_element.name = '{}_similarity.json'.format(upload_item_element.ref)

                if not upload_item_element.name.endswith('.json'):
                    remote_filepath = '{}{}.json'.format(remote_path, upload_item_element.name)
                else:
                    remote_filepath = '{}{}'.format(remote_path, upload_item_element.name)

                element = UploadElement(element_type='collection',
                                        buffer=upload_item_element,
                                        remote_filepath=remote_filepath,
                                        annotations_filepath=upload_annotations_element,
                                        item_metadata=item_metadata)
                elements.append(element)
            elif isinstance(upload_item_element, entities.MultiView):
                if remote_name:
                    upload_item_element.name = remote_name

                if not upload_item_element.name.endswith('.json'):
                    upload_item_element.name = '{}.json'.format(upload_item_element.name)

                remote_filepath = '{}{}'.format(remote_path, upload_item_element.name)
                element = UploadElement(element_type='collection',
                                        buffer=upload_item_element,
                                        remote_filepath=remote_filepath,
                                        annotations_filepath=upload_annotations_element,
                                        item_metadata=item_metadata)
                elements.append(element)
            elif isinstance(upload_item_element, bytes) or \
                    isinstance(upload_item_element, io.BytesIO) or \
                    isinstance(upload_item_element, io.BufferedReader) or \
                    isinstance(upload_item_element, io.TextIOWrapper):
                # binary element
                if not hasattr(upload_item_element, "name") and remote_name is None:
                    raise PlatformException(
                        error="400",
                        message='Upload element type was bytes. Must put attribute "name" on buffer (with file name) '
                                'when uploading buffers or providing param "remote_name"')
                if remote_name is None:
                    remote_name = upload_item_element.name
                remote_filepath = remote_path + remote_name
                element = UploadElement(element_type='buffer',
                                        buffer=upload_item_element,
                                        remote_filepath=remote_filepath,
                                        annotations_filepath=upload_annotations_element,
                                        item_metadata=item_metadata)
                elements.append(element)
                # get size from binaries
                try:
                    total_size += upload_item_element.__sizeof__()
                except Exception:
                    logger.warning("Cant get binaries size")
            else:
                raise PlatformException(
                    error="400",
                    message="Unknown element type to upload ('local_path'). received type: {}. "
                            "known types (or list of those types): str (dir, file, url), bytes, io.BytesIO, "
                            "numpy.ndarray, io.TextIOWrapper, Dataloop.Item, Dataloop.Link, "
                            "Dataloop.Similarity".format(type(upload_item_element)))
        return elements

    def _build_elements_from_df(self, df: pandas.DataFrame):
        elements = list()
        for index, row in df.iterrows():
            upload_item_element = row.get('local_path')
            remote_path = row.get('remote_path', '/')
            remote_name = row.get('remote_name', None)
            annotations_filepath = row.get('local_annotations_path', None)
            item_metadata = row.get('item_metadata', None)
            if not remote_path.endswith('/'):
                remote_path += '/'

            if os.path.isfile(upload_item_element):
                element_type = 'file'
                if remote_name is None:
                    remote_name = os.path.basename(upload_item_element)
            elif self.is_url(upload_item_element):
                element_type = 'url'
                if remote_name is None:
                    remote_name = str(upload_item_element.split('/')[-1])
            else:
                raise PlatformException("404", "Unknown local path: {}".format(upload_item_element))
            elements.append(UploadElement(element_type=element_type,
                                          buffer=upload_item_element,
                                          remote_filepath=remote_path + remote_name,
                                          annotations_filepath=annotations_filepath,
                                          item_metadata=item_metadata))

        return elements

    async def __single_async_upload(self,
                                    filepath,
                                    remote_path,
                                    uploaded_filename,
                                    last_try,
                                    mode,
                                    item_metadata,
                                    callback
                                    ):
        """
        Upload an item to dataset

        :param filepath: local filepath of the item
        :param remote_path: remote directory of filepath to upload
        :param uploaded_filename: optional - remote filename
        :param last_try: print log error only if last try
        :return: Item object
        """

        need_close = False
        if isinstance(filepath, str):
            # upload local file
            if not os.path.isfile(filepath):
                raise PlatformException(error="404", message="Filepath doesnt exists. file: {}".format(filepath))
            if uploaded_filename is None:
                uploaded_filename = os.path.basename(filepath)
            if os.path.isfile(filepath):
                item_type = 'file'
            else:
                item_type = 'dir'
            item_size = os.stat(filepath).st_size
            to_upload = open(filepath, 'rb')
            need_close = True

        else:
            # upload from buffer
            if isinstance(filepath, bytes):
                to_upload = io.BytesIO(filepath)
            elif isinstance(filepath, io.BytesIO):
                to_upload = filepath
            elif isinstance(filepath, io.BufferedReader):
                to_upload = filepath
            elif isinstance(filepath, io.TextIOWrapper):
                to_upload = filepath
            else:
                raise PlatformException("400", "Unknown input filepath type received: {}".format(type(filepath)))

            if uploaded_filename is None:
                if hasattr(filepath, "name"):
                    uploaded_filename = filepath.name
                else:
                    raise PlatformException(error="400",
                                            message="Must have filename when uploading bytes array (uploaded_filename)")

            item_size = to_upload.seek(0, 2)
            to_upload.seek(0)
            item_type = 'file'
        remote_url = "/datasets/{}/items".format(self.items_repository.dataset.id)
        try:
            response = await self.items_repository._client_api.upload_file_async(to_upload=to_upload,
                                                                                 item_type=item_type,
                                                                                 item_size=item_size,
                                                                                 item_metadata=item_metadata,
                                                                                 remote_url=remote_url,
                                                                                 uploaded_filename=uploaded_filename,
                                                                                 remote_path=remote_path,
                                                                                 callback=callback,
                                                                                 mode=mode)
        except Exception:
            raise
        finally:
            if need_close:
                to_upload.close()

        if response.ok:
            item = self.items_repository.items_entity.from_json(client_api=self.items_repository._client_api,
                                                                _json=response.json(),
                                                                dataset=self.items_repository.dataset)
        else:
            raise PlatformException(response)
        return item, response.headers.get('x-item-op', 'na')

    async def __upload_single_item_wrapper(self, i_item, element, pbar, reporter, mode):
        async with self.items_repository._client_api.event_loops('items.upload').semaphore('items.upload'):
            assert isinstance(element, UploadElement)
            item = False
            err = None
            trace = None
            saved_locally = False
            temp_dir = None
            action = 'na'
            remote_folder, remote_name = os.path.split(element.remote_filepath)

            if element.type == 'url':
                saved_locally, element.buffer, temp_dir = self.url_to_data(element.buffer)
            elif element.type == 'link':
                element.buffer = self.link(ref=element.buffer.ref, dataset_id=element.buffer.dataset_id,
                                           type=element.buffer.type, mimetype=element.buffer.mimetype)
            elif element.type == 'collection':
                element.buffer = element.buffer.to_bytes_io()

            for i_try in range(NUM_TRIES):
                try:
                    logger.debug("Upload item: {path}. Try {i}/{n}. Starting..".format(path=remote_name,
                                                                                       i=i_try + 1,
                                                                                       n=NUM_TRIES))
                    item, action = await self.__single_async_upload(filepath=element.buffer,
                                                                    mode=mode,
                                                                    item_metadata=element.item_metadata,
                                                                    remote_path=remote_folder,
                                                                    uploaded_filename=remote_name,
                                                                    last_try=(i_try + 1) == NUM_TRIES,
                                                                    callback=None)
                    logger.debug("Upload item: {path}. Try {i}/{n}. Success. Item id: {id}".format(path=remote_name,
                                                                                                   i=i_try + 1,
                                                                                                   n=NUM_TRIES,
                                                                                                   id=item.id))
                    if isinstance(item, entities.Item):
                        break
                    time.sleep(0.3 * (2 ** i_try))
                except Exception as e:
                    err = e
                    trace = traceback.format_exc()
                    logger.debug("Upload item: {path}. Try {i}/{n}. Fail.\n{trace}".format(path=remote_name,
                                                                                           i=i_try + 1,
                                                                                           n=NUM_TRIES,
                                                                                           trace=trace))

                finally:
                    if saved_locally and os.path.isdir(temp_dir):
                        shutil.rmtree(temp_dir)
            if item:
                if action in ['overwrite', 'created'] and element.annotations_filepath is not None:
                    try:
                        await self.__async_upload_annotations(annotations_filepath=element.annotations_filepath,
                                                              item=item)
                    except Exception:
                        logger.exception('Error uploading annotations to item id: {}'.format(item.id))

                reporter.set_index(i_item=i_item, status=action, output=item, success=True, ref=item.id)
            else:
                if isinstance(element.buffer, str):
                    ref = element.buffer
                elif hasattr(element.buffer, "name"):
                    ref = element.buffer.name
                else:
                    ref = 'Unknown'
                reporter.set_index(i_item=i_item, status='error', success=False,
                                   error="{}\n{}".format(err, trace), ref=ref)
            pbar.update()

    async def __async_upload_annotations(self, annotations_filepath, item):
        with open(annotations_filepath, 'r', encoding="utf8") as f:
            annotations = json.load(f)
        # wait for coroutines on the current event loop
        return await item.annotations._async_upload_annotations(annotations=annotations['annotations'])

    @staticmethod
    def url_to_data(url):
        chunk_size = 8192
        max_size = 30000000
        temp_dir = None

        # This will download the binaries from the URL user provided
        prepared_request = requests.Request(method='GET', url=url).prepare()
        with requests.Session() as s:
            retry = Retry(
                total=3,
                read=3,
                connect=3,
                backoff_factor=0.3,
            )
            adapter = HTTPAdapter(max_retries=retry)
            s.mount('http://', adapter)
            s.mount('https://', adapter)
            response = s.send(request=prepared_request, stream=True)

        total_length = response.headers.get("content-length")
        save_locally = int(total_length) > max_size

        if save_locally:
            # save to file
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, url.split('/')[-1])
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            # save to output variable
            data = temp_path
        else:
            # save as byte stream
            data = io.BytesIO()
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep-alive new chunks
                    data.write(chunk)
            # go back to the beginning of the stream
            data.seek(0)
            data.name = url.split('/')[-1]

        return save_locally, data, temp_dir

    @staticmethod
    def is_url(url):
        try:
            return validators.url(url)
        except Exception:
            return False

    @staticmethod
    def link(ref, type, mimetype=None, dataset_id=None):

        link_info = {'type': type,
                     'ref': ref}

        if mimetype:
            link_info['mimetype'] = mimetype

        if dataset_id is not None:
            link_info['datasetId'] = dataset_id

        _json = {'type': 'link',
                 'shebang': 'dataloop',
                 'metadata': {'dltype': 'link',
                              'linkInfo': link_info}}

        uploaded_byte_io = io.BytesIO()
        uploaded_byte_io.write(json.dumps(_json).encode())
        uploaded_byte_io.seek(0)

        return uploaded_byte_io
