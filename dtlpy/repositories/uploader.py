import sys
from collections import deque
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

from . import upload_element

from .. import PlatformException, entities, repositories, exceptions
from ..services import Reporter

logger = logging.getLogger(name='dtlpy')

NUM_TRIES = 5  # try to upload 3 time before fail on item


class Uploader:
    def __init__(self, items_repository: repositories.Items, output_entity=entities.Item, no_output=False):
        assert isinstance(items_repository, repositories.Items)
        self.items_repository = items_repository
        self.remote_url = "/datasets/{}/items".format(self.items_repository.dataset.id)
        self.__stop_create_existence_dict = False
        self.mode = 'skip'
        self.num_files = 0
        self.i_item = 0
        self.pbar = tqdm.tqdm(total=0,
                              disable=self.items_repository._client_api.verbose.disable_progress_bar_upload_items,
                              file=sys.stdout, desc='Upload Items')
        self.reporter = Reporter(num_workers=0,
                                 resource=Reporter.ITEMS_UPLOAD,
                                 print_error_logs=items_repository._client_api.verbose.print_error_logs,
                                 output_entity=output_entity,
                                 client_api=items_repository._client_api,
                                 no_output=no_output)

    def upload(
            self,
            # what to upload
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path=None,
            remote_name=None,
            file_types=None,
            overwrite=False,
            item_metadata=None,
            export_version: str = entities.ExportVersion.V1,
            item_description=None
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If `*` at the end of local_path (e.g. '/images/*') items will be uploaded without head directory

        :param local_path: local file or folder to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param remote_name: remote base name to save.
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param overwrite: optional - default = False
        :param item_metadata: upload the items with the metadata dictionary
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :param str item_description: add a string description to the uploaded item

        :return: Output (list)
        """
        ###################
        # Default options #
        ###################
        if overwrite:
            self.mode = 'overwrite'
        if isinstance(local_path, pandas.DataFrame):
            futures = self._build_elements_from_df(local_path)
        else:
            futures = self._build_elements_from_inputs(local_path=local_path,
                                                       local_annotations_path=local_annotations_path,
                                                       # upload options
                                                       remote_path=remote_path,
                                                       remote_name=remote_name,
                                                       file_types=file_types,
                                                       item_metadata=item_metadata,
                                                       export_version=export_version,
                                                       item_description=item_description)
        num_files = len(futures)
        while futures:
            futures.popleft().result()
        logger.info("Uploading {} items..".format(num_files))
        self.pbar.close()
        # summary
        logger.info("Number of total files: {}".format(num_files))
        status_list = self.reporter.status_list
        for action in set(status_list):
            n_for_action = self.reporter.status_count(status=action)
            logger.info("Number of files {}: {}".format(action, n_for_action))

        # log error
        errors_count = self.reporter.failure_count
        if errors_count > 0:
            log_filepath = self.reporter.generate_log_files()
            if log_filepath is not None:
                logger.warning("Errors in {n_error} files. See {log_filepath} for full log".format(
                    n_error=errors_count, log_filepath=log_filepath))

        # TODO 2.0 always return a list
        if len(status_list) == 1:
            try:
                return next(self.reporter.output)
            except StopIteration:
                return None
        return self.reporter.output

    def _build_elements_from_inputs(self,
                                    local_path,
                                    local_annotations_path,
                                    # upload options
                                    remote_path,
                                    file_types,
                                    remote_name,
                                    item_metadata,
                                    export_version: str = entities.ExportVersion.V1,
                                    item_description=None):
        # fix remote path
        if remote_path is None:
            if isinstance(local_path, str) and local_path.startswith('external://'):
                remote_path = None
            else:
                remote_path = "/"
        if remote_path and not remote_path.startswith('/'):
            remote_path = f"/{remote_path}"
        if remote_path and not remote_path.endswith("/"):
            remote_path = f"{remote_path}/"
        if file_types is not None and not isinstance(file_types, list):
            msg = '"file_types" should be a list of file extension. e.g [".jpg", ".png"]'
            raise PlatformException(error="400", message=msg)
        if item_metadata is not None:
            if not isinstance(item_metadata, dict) and not isinstance(item_metadata, entities.ExportMetadata):
                msg = '"item_metadata" should be a metadata dictionary. Got type: {}'.format(type(item_metadata))
                raise PlatformException(error="400", message=msg)
        if item_description is not None:
            if not isinstance(item_description, str):
                msg = '"item_description" should be a string. Got type: {}'.format(type(item_description))
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

        try:
            driver_path = self.items_repository.dataset.project.drivers.get(
                driver_id=self.items_repository.dataset.driver).path
        except Exception:
            driver_path = None

        futures = deque()
        total_size = 0
        for upload_item_element, remote_name, upload_annotations_element in zip(local_path_list,
                                                                                remote_name_list,
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

            all_upload_elements = {
                'upload_item_element': upload_item_element,
                'total_size': total_size,
                'remote_name': remote_name,
                'remote_path': remote_path,
                'upload_annotations_element': upload_annotations_element,
                'item_metadata': item_metadata,
                'annotations_filepath': None,
                'with_head_folder': None,
                'filename': None,
                'root': None,
                'export_version': export_version,
                'item_description': item_description,
                'driver_path': driver_path
            }
            if isinstance(upload_item_element, str):
                with_head_folder = True
                if upload_item_element.endswith('*'):
                    with_head_folder = False
                    upload_item_element = os.path.dirname(upload_item_element)
                    all_upload_elements['upload_item_element'] = upload_item_element

                if os.path.isdir(upload_item_element):
                    for root, subdirs, files in os.walk(upload_item_element):
                        for filename in files:
                            all_upload_elements['with_head_folder'] = with_head_folder
                            all_upload_elements['filename'] = filename
                            all_upload_elements['root'] = root
                            _, ext = os.path.splitext(filename)
                            if file_types is None or ext in file_types:
                                upload_elem = upload_element.DirUploadElement(all_upload_elements=all_upload_elements)
                                futures.append(self.upload_single_element(upload_elem))
                    continue

                # add single file
                elif os.path.isfile(upload_item_element):
                    upload_elem = upload_element.FileUploadElement(all_upload_elements=all_upload_elements)

                elif upload_item_element.startswith('external://'):
                    upload_elem = upload_element.ExternalItemUploadElement(all_upload_elements=all_upload_elements)

                elif self.is_url(upload_item_element):
                    upload_elem = upload_element.UrlUploadElement(all_upload_elements=all_upload_elements)

                else:
                    raise PlatformException("404", "Unknown local path: {}".format(local_path))

            elif isinstance(upload_item_element, entities.Item):
                upload_elem = upload_element.ItemLinkUploadElement(all_upload_elements=all_upload_elements)

            elif isinstance(upload_item_element, entities.Link):
                upload_elem = upload_element.LinkUploadElement(all_upload_elements=all_upload_elements)

            elif isinstance(upload_item_element, entities.PromptItem):
                upload_elem = upload_element.PromptUploadElement(all_upload_elements=all_upload_elements)

            elif isinstance(upload_item_element, entities.ItemGis):
                buffer = io.BytesIO(json.dumps(upload_item_element.to_json()).encode('utf-8'))
                buffer.name = upload_item_element.name
                all_upload_elements['upload_item_element'] = buffer
                upload_elem = upload_element.BinaryUploadElement(all_upload_elements=all_upload_elements)

            elif isinstance(upload_item_element, bytes) or \
                    isinstance(upload_item_element, io.BytesIO) or \
                    isinstance(upload_item_element, io.BufferedReader) or \
                    isinstance(upload_item_element, io.TextIOWrapper):
                upload_elem = upload_element.BinaryUploadElement(all_upload_elements=all_upload_elements)
                # get size from binaries
                try:
                    total_size += upload_item_element.__sizeof__()
                except Exception:
                    logger.warning("Cant get binaries size")

            else:
                raise PlatformException(
                    error="400",
                    message=f"Unknown element type to upload ('local_path'). received type: {type(upload_item_element)}. "
                            "known types (or list of those types): str (dir, file, url), bytes, io.BytesIO, "
                            "numpy.ndarray, io.TextIOWrapper, Dataloop.Item, Dataloop.Link")

            futures.append(self.upload_single_element(upload_elem))
        return futures

    def upload_single_element(self, elem):
        """
        upload a signal element
        :param elem: UploadElement
        """
        self.num_files += 1
        self.i_item += 1
        self.pbar.total += 1
        self.reporter.upcount_num_workers()
        future = asyncio.run_coroutine_threadsafe(
            self.__upload_single_item_wrapper(element=elem,
                                              mode=self.mode,
                                              pbar=self.pbar,
                                              reporter=self.reporter),
            loop=self.items_repository._client_api.event_loop.loop)
        return future

    def _build_elements_from_df(self, df: pandas.DataFrame):
        futures = deque()
        for index, row in df.iterrows():
            # DEFAULTS
            elem = {'local_annotations_path': None,
                    'remote_path': None,
                    'remote_name': None,
                    'file_types': None,
                    'item_metadata': None,
                    'item_description': None}
            elem.update(row)
            future = self._build_elements_from_inputs(**elem)
            # append deque using +
            futures += future
        return futures

    async def __single_external_sync(self, element):
        storage_id = element.buffer.split('//')[1]
        req_json = dict()
        req_json['filename'] = element.remote_filepath
        req_json['storageId'] = storage_id
        success, response = self.items_repository._client_api.gen_request(req_type='post',
                                                                          path='/datasets/{}/imports'.format(
                                                                              self.items_repository.dataset.id),
                                                                          json_req=[req_json])

        if success:
            items = entities.Item.from_json(client_api=self.items_repository._client_api, _json=response.json()[0],
                                            project=self.items_repository._dataset._project,
                                            dataset=self.items_repository.dataset)
        else:
            raise exceptions.PlatformException(response)
        return items, response.headers.get('x-item-op', 'na')

    async def __single_async_upload(self,
                                    filepath,
                                    remote_path,
                                    uploaded_filename,
                                    last_try,
                                    mode,
                                    item_metadata,
                                    callback,
                                    item_description
                                    ):
        """
        Upload an item to dataset

        :param filepath: local filepath of the item
        :param remote_path: remote directory of filepath to upload
        :param uploaded_filename: optional - remote filename
        :param last_try: print log error only if last try
        :param mode: 'skip'  'overwrite'
        :param item_metadata: item metadata
        :param str item_description: add a string description to the uploaded item
        :param callback:
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
        try:
            response = await self.items_repository._client_api.upload_file_async(to_upload=to_upload,
                                                                                 item_type=item_type,
                                                                                 item_size=item_size,
                                                                                 item_metadata=item_metadata,
                                                                                 remote_url=self.remote_url,
                                                                                 uploaded_filename=uploaded_filename,
                                                                                 remote_path=remote_path,
                                                                                 callback=callback,
                                                                                 mode=mode,
                                                                                 item_description=item_description)
        except Exception:
            raise
        finally:
            if need_close:
                to_upload.close()

        if response.ok:
            if item_size != response.json().get('metadata', {}).get('system', {}).get('size', 0):
                self.items_repository.delete(item_id=response.json()['id'])
                raise PlatformException(500,
                                        "The uploaded file is corrupted. "
                                        "Please try again. If it happens again please contact support.")
            item = self.items_repository.items_entity.from_json(client_api=self.items_repository._client_api,
                                                                _json=response.json(),
                                                                dataset=self.items_repository.dataset)
        else:
            raise PlatformException(response)
        return item, response.headers.get('x-item-op', 'na')

    async def __upload_single_item_wrapper(self, element, pbar, reporter, mode):
        async with self.items_repository._client_api.event_loop.semaphore('items.upload', 5):
            # assert isinstance(element, UploadElement)
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

            for i_try in range(NUM_TRIES):
                try:
                    logger.debug("Upload item: {path}. Try {i}/{n}. Starting..".format(path=remote_name,
                                                                                       i=i_try + 1,
                                                                                       n=NUM_TRIES))
                    if element.type == 'external_file':
                        item, action = await self.__single_external_sync(element)
                    else:
                        if element.annotations_filepath is not None and \
                                element.item_metadata == entities.ExportMetadata.FROM_JSON:
                            element.item_metadata = {}
                            with open(element.annotations_filepath) as ann_f:
                                item_metadata = json.load(ann_f)
                            if 'metadata' in item_metadata:
                                element.item_metadata = item_metadata['metadata']
                        item, action = await self.__single_async_upload(filepath=element.buffer,
                                                                        mode=mode,
                                                                        item_metadata=element.item_metadata,
                                                                        remote_path=remote_folder,
                                                                        uploaded_filename=remote_name,
                                                                        last_try=(i_try + 1) == NUM_TRIES,
                                                                        callback=None,
                                                                        item_description=element.item_description)
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

                reporter.set_index(status=action,
                                   output=item.to_json(),
                                   success=True,
                                   ref=item.id)
                if pbar is not None:
                    pbar.update()
                    self.items_repository._client_api.callbacks.run_on_event(
                        event=self.items_repository._client_api.callbacks.CallbackEvent.ITEMS_UPLOAD,
                        context={'item_id': item.id, 'dataset_id': item.dataset_id},
                        progress=round(pbar.n / pbar.total * 100, 0))
            else:
                if isinstance(element.buffer, str):
                    ref = element.buffer
                elif hasattr(element.buffer, "name"):
                    ref = element.buffer.name
                else:
                    ref = 'Unknown'
                reporter.set_index(ref=ref, status='error',
                                   success=False,
                                   error="{}\n{}".format(err, trace))

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
                backoff_factor=1,
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
            temp_path = os.path.join(temp_dir, url.split('/')[-1].split('?')[0])
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
        """
        :param ref:
        :param type:
        :param mimetype:
        :param dataset_id:
        """
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
