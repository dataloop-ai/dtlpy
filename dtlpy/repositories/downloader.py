import copy
import io
import json
import logging
import multiprocessing
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from urllib.parse import unquote, urlparse

import numpy as np
import requests
import tqdm
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .. import entities, repositories, miscellaneous, PlatformException, exceptions
from ..services import Reporter

logger = logging.getLogger(name='dtlpy')

NUM_TRIES = 3  # try to download 3 time before fail on item
DOWNLOAD_MAX_ITEMS_PER_SUBSET = 1000

class Downloader:
    def __init__(self, items_repository):
        self.items_repository = items_repository

    def _process_download_results(self, reporter, raise_on_error=False):
        """
        Process download results and generate summary report.

        :param reporter: Reporter instance containing download results
        :param raise_on_error: If True, raise exception on download errors
        :return: Output from reporter
        """
        # reporting
        n_download = reporter.status_count(status='download')
        n_exist = reporter.status_count(status='exist')
        n_error = reporter.status_count(status='error')
        logger.info(f"Number of files downloaded:{n_download}")
        logger.info(f"Number of files exists: {n_exist}")
        logger.info(f"Total number of files: {n_download + n_exist}")

        # log error
        if n_error > 0:
            log_filepath = reporter.generate_log_files()
            # Get up to 5 error examples for the exception message
            error_text = ""
            error_counter = 0
            if reporter._errors:
                for _id, error in reporter._errors.items():
                    error_counter += 1
                    error_text += f"Item ID: {_id}, Error: {error} | "
                    if error_counter >= 5:
                        break
            error_message = f"Errors in {n_error} files. Errors: {error_text}"
            if log_filepath is not None:
                error_message += f", see {log_filepath} for full log"
            if raise_on_error is True:
                raise PlatformException(
                    error="400", message=error_message
                )
            else:
                logger.warning(error_message)
        
        if int(n_download) <= 1 and int(n_exist) <= 1:
            try:
                return next(reporter.output)
            except StopIteration:
                return None
        return reporter.output

    def _process_item_json(self, local_path, item_json, reporter, pbar, overwrite=False):
        """
        Process a single item JSON for download, saving both the item file and metadata.

        :param local_path: Local path to save files
        :param item_json: Item JSON metadata
        :param reporter: Reporter instance for tracking progress
        :param pbar: Progress bar instance
        :param overwrite: Whether to overwrite existing files
        :return: Error message, traceback, and downloaded filepath
        """
        err = None
        trace = None
        downloaded_filepath = None
        item_id = item_json['id']
        filename = item_json['filename'].lstrip('/')
        
        for i_try in range(NUM_TRIES):
            try:
                # Download the image
                image_path = Path(local_path) / 'items' / filename
                # Ensure the directory for the image file exists (in case filename has subdirectories)
                image_path.parent.mkdir(parents=True, exist_ok=True)
                item = entities.Item.from_json(_json = item_json, client_api=self.items_repository._client_api, is_fetched=False)
                downloaded_data = self.__thread_download(
                    item=item,
                    local_path=str(image_path.parent),
                    local_filepath=str(image_path),
                    save_locally=True,
                    to_array=False,
                    overwrite=overwrite,
                    annotation_options=[],
                    annotation_filters=None,
                )

                if downloaded_data is None:
                    err = 'Failed to download image'
                    trace = ''
                else:
                    # Save the item JSON directly
                    json_filename = Path(filename).stem + '.json'
                    json_path = Path(local_path) / 'json' / Path(filename).parent / json_filename

                    # Ensure the directory for the JSON file exists (in case filename has subdirectories)
                    json_path.parent.mkdir(parents=True, exist_ok=True)

                    # Save the original item_json directly
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(item_json, f, indent=2, ensure_ascii=False)

                    downloaded_filepath = str(image_path)
                
                if downloaded_filepath is not None:
                    break

            except Exception as e:
                logger.debug(f"Download item: {filename}. Try {i_try + 1}/{NUM_TRIES}. Fail.")
                err = e
                trace = traceback.format_exc()

        pbar.update()
        if downloaded_filepath is None:
            if err is None:
                err = self.items_repository._client_api.platform_exception
            reporter.set_index(status="error", ref=item_id, success=False, error=f"{err}\n{trace}")
        else:
            reporter.set_index(ref=item_id, status="download", output=downloaded_filepath, success=True)

    def _download_recursive(
        self,
        local_path=None,
        filters: entities.Filters = None,
        annotation_filters: entities.Filters = None,
        file_types=None,
        overwrite=False,
        raise_on_error=False,
        dataset_lock=False,
        lock_timeout_sec=None,
    ):
        """
        Download items recursively from a dataset.
        
        :param local_path: Local path to save downloaded items
        :param filters: Filters entity to filter items
        :param annotation_filters: Filters entity to filter annotations
        :param file_types: List of file types to download
        :param overwrite: Whether to overwrite existing files
        :param raise_on_error: Raise error if download fails
        :param dataset_lock: Lock dataset during download
        :param lock_timeout_sec: Lock timeout in seconds
        """
        filters, annotation_filters = self._prepare_filters(filters=filters,annotation_filters=annotation_filters,file_types=file_types)
        filter_copy = copy.deepcopy(filters)
        filter_copy.page_size = 0
        num_items = self.items_repository.list(filters=filter_copy).items_count
        if num_items == 0:
            return list()
        client_api = self.items_repository._client_api
        reporter = Reporter(
            num_workers=num_items,
            resource=Reporter.ITEMS_DOWNLOAD,
            print_error_logs=client_api.verbose.print_error_logs,
            client_api=client_api,
        )

        # Create directories once using pathlib
        local_path_obj = Path(local_path)
        items_dir = local_path_obj / 'items'
        jsons_dir = local_path_obj / 'json'
        items_dir.mkdir(parents=True, exist_ok=True)
        jsons_dir.mkdir(parents=True, exist_ok=True)

        jobs = [None for _ in range(num_items)]
        # crrently keep the thread count to default.
        # client_api._thread_pools_names['item.download'] = 5 * multiprocessing.cpu_count()
        pool = client_api.thread_pools(pool_name='item.download')
        pbar = tqdm.tqdm(
            total=num_items,
            disable=client_api.verbose.disable_progress_bar_download_dataset,
            file=sys.stdout,
            desc='Download Items',
        )
        try:
            i_item = 0
            import time
            start_time = time.time()
            for json_file in self.items_repository.dataset.project.datasets._export_recursive(
                dataset=self.items_repository.dataset,
                local_path=tempfile.mkdtemp(prefix='download_recursive_jsons_'),
                max_items_per_subset=DOWNLOAD_MAX_ITEMS_PER_SUBSET,
                include_annotations=True,
                filters=filters,
                annotation_filters=annotation_filters,
                dataset_lock=dataset_lock,
                lock_timeout_sec=lock_timeout_sec,
            ):
                end_time = time.time()
                with open(json_file, 'r') as f:
                    data = json.load(f)
                for item_json in data:
                    jobs[i_item] = pool.submit(
                        self._process_item_json,
                        **{
                            "local_path": local_path,
                            "item_json": item_json,
                            "reporter": reporter,
                            "pbar": pbar,
                            "overwrite": overwrite,
                        },
                    )
                    i_item += 1
        finally:
            _ = [j.result() for j in jobs if j is not None]
            pbar.close()
        return self._process_download_results(reporter=reporter, raise_on_error=raise_on_error)

    @staticmethod
    def _prepare_filters(filters: entities.Filters = None,
                        annotation_filters: entities.Filters = None,
                        file_types=None):
        """
        Prepare and merge filters with annotation filters.

        :param filters: Filters entity or None
        :param annotation_filters: Annotation filters to merge with item filters
        :param file_types: List of file types to filter
        :return: Prepared filters entity
        """
        # filters
        if filters is None:
            filters = entities.Filters()
            filters._user_query = 'false'
        # file types
        if file_types is not None:
            filters.add(field='metadata.system.mimetype', values=file_types, operator=entities.FiltersOperations.IN)
        if annotation_filters is not None:
            if len(annotation_filters.and_filter_list) > 0 or len(annotation_filters.or_filter_list) > 0:
                for annotation_filter_and in annotation_filters.and_filter_list:
                    filters.add_join(field=annotation_filter_and.field,
                                    values=annotation_filter_and.values,
                                    operator=annotation_filter_and.operator,
                                    method=entities.FiltersMethod.AND)
                for annotation_filter_or in annotation_filters.or_filter_list:
                    filters.add_join(field=annotation_filter_or.field,
                                    values=annotation_filter_or.values,
                                    operator=annotation_filter_or.operator,
                                    method=entities.FiltersMethod.OR)
            elif annotation_filters.custom_filter is not None:
                annotation_query_dict = annotation_filters.prepare()
                items_query_dict = filters.prepare()
                items_query_dict["join"] = annotation_query_dict
                filters.reset()
                filters.custom_filter = items_query_dict

        else:
            annotation_filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
            filters._user_query = 'false'

        return filters, annotation_filters

    def download(self,
                 # filter options
                 filters: entities.Filters = None,
                 items=None,
                 # download options
                 local_path=None,
                 file_types=None,
                 save_locally=True,
                 to_array=False,
                 overwrite=False,
                 annotation_filters: entities.Filters = None,
                 annotation_options: entities.ViewAnnotationOptions = None,
                 to_items_folder=True,
                 thickness=1,
                 with_text=False,
                 without_relative_path=None,
                 avoid_unnecessary_annotation_download=False,
                 include_annotations_in_output=True,
                 export_png_files=False,
                 filter_output_annotations=False,
                 alpha=1,
                 export_version=entities.ExportVersion.V1,
                 dataset_lock=False,
                 lock_timeout_sec=None,
                 export_summary=False,
                 raise_on_error=False
                 ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param dtlpy.entities.filters.Filters filters: Filters entity or a dictionary containing filters parameters
        :param items: download Item entity or item_id (or a list of item)
        :param local_path: local folder or filename to save to.
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param save_locally: bool. save to disk or return a buffer
        :param to_array: returns Ndarray when True and local_path = False
        :param overwrite: optional - default = False
        :param annotation_options: download annotations options. options: list(dl.ViewAnnotationOptions)
        :param annotation_filters: Filters entity to filter annotations for download
        :param to_items_folder: Create 'items' folder and download items to it
        :param with_text: optional - add text to annotations, default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param without_relative_path: bool - download items without the relative path from platform
        :param avoid_unnecessary_annotation_download: DEPRECATED only items and annotations in filters are downloaded
        :param include_annotations_in_output: default - False , if export should contain annotations
        :param export_png_files: default - True, if semantic annotations should be exported as png files
        :param filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param alpha: opacity value [0 1], default 1
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :param bool dataset_lock: optional - default = False
        :param bool export_summary: optional - default = False
        :param int lock_timeout_sec: optional
        :param bool raise_on_error: raise an exception if an error occurs
        :return: Output (list)
        """

        ###################
        # Default options #
        ###################
        # annotation options
        if annotation_options is None:
            annotation_options = list()
        elif not isinstance(annotation_options, list):
            annotation_options = [annotation_options]
        for ann_option in annotation_options:
            if not isinstance(ann_option, entities.ViewAnnotationOptions):
                if ann_option not in list(entities.ViewAnnotationOptions):
                    raise PlatformException(
                        error='400',
                        message='Unknown annotation download option: {}, please choose from: {}'.format(
                            ann_option, list(entities.ViewAnnotationOptions)))
        # normalize items argument: treat empty list as “no items specified”
        if isinstance(items, list) and len(items) == 0:
            items = None
        #####################
        # items to download #
        #####################
        if items is not None:
            # convert input to a list
            if not isinstance(items, list):
                items = [items]
            # get items by id
            if isinstance(items[0], str):
                items = [self.items_repository.get(item_id=item_id) for item_id in items]
            elif isinstance(items[0], entities.Item):
                pass
            else:
                raise PlatformException(
                    error="400",
                    message='Unknown items type to download. Expecting str or Item entities. Got "{}" instead'.format(
                        type(items[0])
                    )
                )
            # create filters to download annotations
            filters = entities.Filters(field='id',
                                       values=[item.id for item in items],
                                       operator=entities.FiltersOperations.IN)
            filters._user_query = 'false'

            # convert to list of list (like pages and page)
            items_to_download = [items]
            num_items = len(items)
        else:
            # Prepare and merge filters
            filters, annotation_filters = self._prepare_filters(
                filters=filters,
                annotation_filters=annotation_filters,
                file_types=file_types
            )

            items_to_download = self.items_repository.list(filters=filters)
            num_items = items_to_download.items_count

        if num_items == 0:
            logger.warning('No items found! Nothing was downloaded')
            return list()

        ##############
        # local path #
        ##############
        is_folder = False
        if local_path is None:
            # create default local path
            local_path = self.__default_local_path()

        if os.path.isdir(local_path):
            logger.info('Local folder already exists:{}. merge/overwrite according to "overwrite option"'.format(
                local_path))
            is_folder = True
        else:
            # check if filename
            _, ext = os.path.splitext(local_path)
            if num_items > 1:
                is_folder = True
            else:
                item_to_download = items_to_download[0][0]
                file_name = item_to_download.name
                _, ext_download = os.path.splitext(file_name)
                if ext_download != ext:
                    is_folder = True
            if is_folder and save_locally:
                path_to_create = local_path
                if local_path.endswith('*'):
                    path_to_create = os.path.dirname(local_path)
                logger.info("Creating new directory for download: {}".format(path_to_create))
                os.makedirs(path_to_create, exist_ok=True)

        ####################
        # annotations json #
        ####################
        # download annotations' json files in a new thread
        # items will start downloading and if json not exists yet - will download for each file
        if num_items > 1 and annotation_options:
            # a new folder named 'json' will be created under the "local_path"
            logger.info("Downloading annotations formats: {}".format(annotation_options))
            self.download_annotations(**{
                "dataset": self.items_repository.dataset,
                "filters": filters,
                "annotation_filters": annotation_filters,
                "local_path": local_path,
                'overwrite': overwrite,
                'include_annotations_in_output': include_annotations_in_output,
                'export_png_files': export_png_files,
                'filter_output_annotations': filter_output_annotations,
                'export_version': export_version,
                'dataset_lock': dataset_lock,
                'lock_timeout_sec': lock_timeout_sec,
                'export_summary': export_summary
            })
        ###############
        # downloading #
        ###############
        # create result lists
        client_api = self.items_repository._client_api

        reporter = Reporter(num_workers=num_items,
                            resource=Reporter.ITEMS_DOWNLOAD,
                            print_error_logs=client_api.verbose.print_error_logs,
                            client_api=client_api)
        jobs = [None for _ in range(num_items)]
        # pool
        pool = client_api.thread_pools(pool_name='item.download')
        # download
        pbar = tqdm.tqdm(total=num_items, disable=client_api.verbose.disable_progress_bar_download_dataset,
                         file=sys.stdout,
                         desc='Download Items')
        try:
            i_item = 0
            for page in items_to_download:
                for item in page:
                    if item.type == "dir":
                        continue
                    if save_locally:
                        # get local file path
                        item_local_path, item_local_filepath = self.__get_local_filepath(
                            local_path=local_path,
                            without_relative_path=without_relative_path,
                            item=item,
                            to_items_folder=to_items_folder,
                            is_folder=is_folder)

                        if os.path.isfile(item_local_filepath) and not overwrite:
                            logger.debug("File Exists: {}".format(item_local_filepath))
                            reporter.set_index(ref=item.id, status='exist', output=item_local_filepath, success=True)
                            pbar.update()
                            if annotation_options and item.annotated:
                                # download annotations only
                                jobs[i_item] = pool.submit(
                                    self._download_img_annotations,
                                    **{
                                        "item": item,
                                        "img_filepath": item_local_filepath,
                                        "overwrite": overwrite,
                                        "annotation_options": annotation_options,
                                        "annotation_filters": annotation_filters,
                                        "local_path": item_local_path,
                                        "thickness": thickness,
                                        "alpha": alpha,
                                        "with_text": with_text,
                                        "export_version": export_version,
                                    },
                                )
                            i_item += 1
                            continue
                    else:
                        item_local_path = None
                        item_local_filepath = None

                    # download single item
                    jobs[i_item] = pool.submit(
                        self.__thread_download_wrapper,
                        **{
                            "i_item": i_item,
                            "item": item,
                            "item_local_path": item_local_path,
                            "item_local_filepath": item_local_filepath,
                            "save_locally": save_locally,
                            "to_array": to_array,
                            "annotation_options": annotation_options,
                            "annotation_filters": annotation_filters,
                            "reporter": reporter,
                            "pbar": pbar,
                            "overwrite": overwrite,
                            "thickness": thickness,
                            "alpha": alpha,
                            "with_text": with_text,
                            "export_version": export_version
                        },
                    )
                    i_item += 1
        except Exception:
            logger.exception('Error downloading:')
        finally:
            _ = [j.result() for j in jobs if j is not None]
            pbar.close()

        return self._process_download_results(reporter=reporter, raise_on_error=raise_on_error)

    def __thread_download_wrapper(self, i_item,
                                  # item params
                                  item, item_local_path, item_local_filepath,
                                  save_locally, to_array, overwrite,
                                  # annotations params
                                  annotation_options, annotation_filters, with_text, thickness,
                                  # threading params
                                  reporter, pbar, alpha, export_version):

        download = None
        err = None
        trace = None
        for i_try in range(NUM_TRIES):
            try:
                logger.debug("Download item: {path}. Try {i}/{n}. Starting..".format(path=item.filename,
                                                                                     i=i_try + 1,
                                                                                     n=NUM_TRIES))
                download = self.__thread_download(item=item,
                                                  save_locally=save_locally,
                                                  to_array=to_array,
                                                  local_path=item_local_path,
                                                  local_filepath=item_local_filepath,
                                                  annotation_options=annotation_options,
                                                  annotation_filters=annotation_filters,
                                                  overwrite=overwrite,
                                                  thickness=thickness,
                                                  alpha=alpha,
                                                  with_text=with_text,
                                                  export_version=export_version)
                logger.debug("Download item: {path}. Try {i}/{n}. Success. Item id: {id}".format(path=item.filename,
                                                                                                 i=i_try + 1,
                                                                                                 n=NUM_TRIES,
                                                                                                 id=item.id))
                if download is not None:
                    break
            except Exception as e:
                logger.debug("Download item: {path}. Try {i}/{n}. Fail.".format(path=item.filename,
                                                                                i=i_try + 1,
                                                                                n=NUM_TRIES))
                err = e
                trace = traceback.format_exc()
        pbar.update()
        if download is None:
            if err is None:
                err = self.items_repository._client_api.platform_exception
            reporter.set_index(status="error", ref=item.id, success=False,
                               error="{}\n{}".format(err, trace))
        else:
            reporter.set_index(ref=item.id, status="download", output=download, success=True)

    @staticmethod
    def download_annotations(dataset: entities.Dataset,
                             local_path: str,
                             filters: entities.Filters = None,
                             annotation_filters: entities.Filters = None,
                             overwrite=False,
                             include_annotations_in_output=True,
                             export_png_files=False,
                             filter_output_annotations=False,
                             export_version=entities.ExportVersion.V1,
                             dataset_lock=False,
                             lock_timeout_sec=None,
                             export_summary=False
                             ):
        """
        Download annotations json for entire dataset

        :param dataset: Dataset entity
        :param local_path:
        :param dtlpy.entities.filters.Filters filters: dl.Filters entity to filters items
        :param annotation_filters: dl.Filters entity to filters items' annotations
        :param overwrite: optional - overwrite annotations if exist, default = false
        :param include_annotations_in_output: default - True , if export should contain annotations
        :param export_png_files: default - if True, semantic annotations should be exported as png files
        :param filter_output_annotations: default - False, given an export by filter - determine if to filter out annotations
        :param str export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :param bool dataset_lock: optional - default = False
        :param bool export_summary: optional - default = False
        :param int lock_timeout_sec: optional
        :return:
        """
        local_path = os.path.join(local_path, "json")
        zip_filepath = None
        # only if json folder does not exist or exist and overwrite
        if not os.path.isdir(os.path.join(local_path, 'json')) or overwrite:
            # create local path to download and save to
            if not os.path.isdir(local_path):
                os.makedirs(local_path)

        try:
            payload = dict()
            if filters is not None:
                payload['itemsQuery'] = filters.prepare()
            payload['annotations'] = {
                "include": include_annotations_in_output,
                "convertSemantic": export_png_files
            }
            payload['exportVersion'] = export_version
            if annotation_filters is not None:
                payload['annotationsQuery'] = annotation_filters.prepare()
                payload['annotations']['filter'] = filter_output_annotations
            if dataset_lock:
                payload['datasetLock'] = dataset_lock

            if export_summary:
                payload['summary'] = export_summary

            if lock_timeout_sec:
                payload['lockTimeoutSec'] = lock_timeout_sec

            success, response = dataset._client_api.gen_request(req_type='post',
                                                                path='/datasets/{}/export'.format(dataset.id),
                                                                json_req=payload,
                                                                headers={'user_query': filters._user_query})
            if not success:
                raise exceptions.PlatformException(response)
            command = entities.Command.from_json(_json=response.json(),
                                                 client_api=dataset._client_api)
            command = command.wait(timeout=0)
            if 'outputItemId' not in command.spec:
                raise exceptions.PlatformException(
                    error='400',
                    message="outputItemId key is missing in command response: {}".format(response))
            item_id = command.spec['outputItemId']
            annotation_zip_item = repositories.Items(client_api=dataset._client_api).get(item_id=item_id)
            zip_filepath = annotation_zip_item.download(local_path=local_path, export_version=export_version)
            # unzipping annotations to directory
            if isinstance(zip_filepath, list) or not os.path.isfile(zip_filepath):
                raise exceptions.PlatformException(
                    error='404',
                    message='error downloading annotation zip file. see above for more information. item id: {!r}'.format(
                        annotation_zip_item.id))
            try:
                miscellaneous.Zipping.unzip_directory(zip_filename=zip_filepath,
                                                      to_directory=local_path)
            except Exception as e:
                logger.warning("Failed to extract zip file error: {}".format(e))

        finally:
            # cleanup
            if isinstance(zip_filepath, str) and os.path.isfile(zip_filepath):
                os.remove(zip_filepath)

    @staticmethod
    def _download_img_annotations(item: entities.Item,
                                  img_filepath,
                                  local_path,
                                  overwrite,
                                  annotation_options,
                                  annotation_filters,
                                  thickness=1,
                                  with_text=False,
                                  alpha=1,
                                  export_version=entities.ExportVersion.V1
                                  ):

        # check if local_path is a file name
        _, ext = os.path.splitext(local_path)
        if ext:
            # take the dir of the file for the annotations save
            local_path = os.path.dirname(local_path)

        # fix local path
        if local_path.endswith("/items") or local_path.endswith("\\items"):
            local_path = os.path.dirname(local_path)

        annotation_rel_path = item.filename[1:]
        if img_filepath is not None:
            dir_name = os.path.dirname(annotation_rel_path)
            base_name = os.path.basename(img_filepath)
            annotation_rel_path = os.path.join(dir_name, base_name)

        # find annotations json
        annotations_json_filepath = os.path.join(local_path, "json", annotation_rel_path)
        if export_version == entities.ExportVersion.V1:
            name, _ = os.path.splitext(annotations_json_filepath)
        else:
            name = annotations_json_filepath
        annotations_json_filepath = name + ".json"

        if os.path.isfile(annotations_json_filepath) and annotation_filters is None:
            # if exists take from json file
            with open(annotations_json_filepath, "r", encoding="utf8") as f:
                data = json.load(f)
            if "annotations" in data:
                data = data["annotations"]
            annotations = entities.AnnotationCollection.from_json(_json=data, item=item)
            # no need to use the filters here because the annotations were already downloaded with annotation_filters
        else:
            # if json file doesnt exist get the annotations from platform
            annotations = item.annotations.list(filters=annotation_filters)

        # get image shape
        is_url_item = item.metadata. \
                          get('system', dict()). \
                          get('shebang', dict()). \
                          get('linkInfo', dict()). \
                          get('type', None) == 'url'

        if item is not None:
            orientation = item.system.get('exif', {}).get('Orientation', 0)
        else:
            orientation = 0
        if item.width is not None and item.height is not None:
            if orientation in [5, 6, 7, 8]:
                img_shape = (item.width, item.height)
            else:
                img_shape = (item.height, item.width)
        elif ('image' in item.mimetype and img_filepath is not None) or \
                (is_url_item and img_filepath is not None):
            img_shape = Image.open(img_filepath).size[::-1]
        else:
            img_shape = (0, 0)

        # download all annotation options
        for option in annotation_options:
            # get path and create dirs
            annotation_filepath = os.path.join(local_path, option, annotation_rel_path)
            if not os.path.isdir(os.path.dirname(annotation_filepath)):
                os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)

            if export_version == entities.ExportVersion.V1:
                temp_path, ext = os.path.splitext(annotation_filepath)
            else:
                temp_path = annotation_filepath

            if option == entities.ViewAnnotationOptions.JSON:
                if not os.path.isfile(annotations_json_filepath):
                    annotations.download(
                        filepath=annotations_json_filepath,
                        annotation_format=option,
                        height=img_shape[0],
                        width=img_shape[1],
                    )
            elif option in [entities.ViewAnnotationOptions.MASK,
                            entities.ViewAnnotationOptions.INSTANCE,
                            entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE,
                            entities.ViewAnnotationOptions.OBJECT_ID,
                            entities.ViewAnnotationOptions.VTT]:
                if option == entities.ViewAnnotationOptions.VTT:
                    annotation_filepath = temp_path + ".vtt"
                else:
                    if 'video' in item.mimetype:
                        annotation_filepath = temp_path + ".mp4"
                    else:
                        annotation_filepath = temp_path + ".png"
                if not os.path.isfile(annotation_filepath) or overwrite:
                    # if not exists OR (exists AND overwrite)
                    if not os.path.exists(os.path.dirname(annotation_filepath)):
                        # create folder if not exists
                        os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
                    if option == entities.ViewAnnotationOptions.ANNOTATION_ON_IMAGE and img_filepath is None:
                        raise PlatformException(
                            error="1002",
                            message="Missing image for annotation option dl.ViewAnnotationOptions.ANNOTATION_ON_IMAGE")
                    annotations.download(
                        filepath=annotation_filepath,
                        img_filepath=img_filepath,
                        annotation_format=option,
                        height=img_shape[0],
                        width=img_shape[1],
                        thickness=thickness,
                        alpha=alpha,
                        with_text=with_text,
                        orientation=orientation
                    )
            else:
                raise PlatformException(error="400", message="Unknown annotation option: {}".format(option))

    @staticmethod
    def __get_local_filepath(local_path, item, to_items_folder, without_relative_path=None, is_folder=False):
        # create paths
        _, ext = os.path.splitext(local_path)
        if ext and not is_folder:
            # local_path is a filename
            local_filepath = local_path
            local_path = os.path.dirname(local_filepath)
        else:
            # if directory - get item's filename
            if to_items_folder:
                local_path = os.path.join(local_path, "items")
            elif is_folder:
                local_path = os.path.join(local_path, "")
            if without_relative_path is not None:
                local_filepath = os.path.join(local_path, item.name)
            else:
                local_filepath = os.path.join(local_path, item.filename[1:])
        return local_path, local_filepath

    @staticmethod
    def __get_link_source(item):
        assert isinstance(item, entities.Item)
        is_url = False
        url = item.resolved_stream
        if item.metadata.get('system', {}).get('shebang', {}).get('linkInfo', {}).get('type', '') == 'url':
            is_url = True

        return item, url, is_url, url.startswith('file://')

    def __file_validation(self, item, downloaded_file):
        res = False
        resume = True
        if isinstance(downloaded_file, io.BytesIO):
            file_size = downloaded_file.getbuffer().nbytes
        else:
            file_size = os.stat(downloaded_file).st_size
        expected_size = item.metadata['system']['size']
        size_diff = file_size - expected_size
        if size_diff == 0:
            res = True
        if size_diff > 0:
            resume = False
        return res, file_size, resume

    def __thread_download(self,
                          item,
                          save_locally,
                          local_path,
                          to_array,
                          local_filepath,
                          overwrite,
                          annotation_options,
                          annotation_filters,
                          chunk_size=8192,
                          thickness=1,
                          with_text=False,
                          alpha=1,
                          export_version=entities.ExportVersion.V1
                          ):
        """
        Get a single item's binary data
        Calling this method will returns the item body itself , an image for example with the proper mimetype.
  
        :param item: Item entity to download
        :param save_locally: bool. save to file or return buffer
        :param local_path: item local folder to save to.
        :param to_array: returns Ndarray when True and local_path = False
        :param local_filepath: item local filepath
        :param overwrite: overwrite the file is existing
        :param annotation_options: download annotations options: list(dl.ViewAnnotationOptions)
        :param annotation_filters: Filters entity to filter item's annotation
        :param chunk_size: size of chunks to download - optional. default = 8192
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :param with_text: optional - add text to annotations, default = False
        :param alpha: opacity value [0 1], default 1
        :param ExportVersion export_version:  exported items will have original extension in filename, `V1` - no original extension in filenames
        :return:
        """
        # check if need to download image binary from platform
        need_to_download = True
        if save_locally and os.path.isfile(local_filepath):
            need_to_download = overwrite

        item, url, is_url, is_local_link = self.__get_link_source(item=item)

        # save as byte stream
        data = io.BytesIO()
        if need_to_download:
            chunk_resume = {0: 0}
            start_point = 0
            download_done = False
            while chunk_resume.get(start_point, '') != 3 and not download_done:
                if not is_url:
                    headers = {'x-dl-sanitize': '0', 'Range': 'bytes={}-'.format(start_point)}
                    result, response = self.items_repository._client_api.gen_request(req_type="get",
                                                                                     headers=headers,
                                                                                     path="/items/{}/stream".format(
                                                                                         item.id),
                                                                                     stream=True,
                                                                                     dataset_id=item.dataset_id)
                    if not result:
                        if os.path.isfile(local_filepath + '.download'):
                            os.remove(local_filepath + '.download')
                        raise PlatformException(response)
                else:
                    _, ext = os.path.splitext(item.metadata['system']['shebang']['linkInfo']['ref'].split('?')[0])
                    if local_filepath:
                        local_filepath += ext
                    response = self.get_url_stream(url=url)

                if save_locally:
                    # save to file
                    if not os.path.exists(os.path.dirname(local_filepath)):
                        # create folder if not exists
                        os.makedirs(os.path.dirname(local_filepath), exist_ok=True)

                    # decide if create progress bar for item
                    if not is_local_link:
                        total_length = response.headers.get("content-length")
                    else:
                        response.seek(0, 2)
                        total_length = response.tell()
                        response.seek(0)
                    one_file_pbar = None
                    try:
                        one_file_progress_bar = total_length is not None and int(
                            total_length) > 10e6  # size larger than 10 MB
                        if one_file_progress_bar:
                            one_file_pbar = tqdm.tqdm(total=int(total_length),
                                                      unit='B',
                                                      unit_scale=True,
                                                      unit_divisor=1024,
                                                      position=1,
                                                      file=sys.stdout,
                                                      disable=self.items_repository._client_api.verbose.disable_progress_bar_download_item,
                                                      desc='Download Item')
                    except Exception as err:
                        one_file_progress_bar = False
                        logger.debug('Cant decide downloaded file length, bar will not be presented: {}'.format(err))

                    # start download
                    if self.items_repository._client_api.sdk_cache.use_cache and \
                            self.items_repository._client_api.cache is not None:
                        response_output = os.path.normpath(response.content)
                        if isinstance(response_output, bytes):
                            response_output = response_output.decode('utf-8')[1:-1]

                        if os.path.isfile(os.path.normpath(response_output)):
                            if response_output != local_filepath:
                                source_path = os.path.normpath(response_output)
                                shutil.copyfile(source_path, local_filepath)
                        download_done = True
                    else:
                        try:
                            temp_file_path = local_filepath + '.download'
                            with open(temp_file_path, "ab") as f:
                                try:
                                    if is_local_link and isinstance(response, io.BufferedReader):
                                        generator = iter(lambda: response.read(chunk_size), b'')
                                    else:
                                        generator = response.iter_content(chunk_size=chunk_size)
                                    for chunk in generator:
                                        if chunk:  # filter out keep-alive new chunks
                                            f.write(chunk)
                                            if one_file_progress_bar:
                                                one_file_pbar.update(len(chunk))
                                except Exception as err:
                                    pass
                                finally:
                                    if is_local_link and isinstance(response, io.BufferedReader):
                                        try:
                                            response.close()
                                        except Exception as err:
                                            pass

                            file_validation = True
                            if not is_url:
                                file_validation, start_point, chunk_resume = self.__get_next_chunk(
                                    item=item,
                                    download_progress=temp_file_path,
                                    chunk_resume=chunk_resume
                                )
                            if file_validation:
                                shutil.move(temp_file_path, local_filepath)
                                download_done = True
                        except Exception as err:
                            if os.path.isfile(temp_file_path):
                                os.remove(temp_file_path)
                            raise err
                    if one_file_progress_bar:
                        one_file_pbar.close()
                    # save to output variable
                    data = local_filepath
                    # if image - can download annotation mask
                    if item.annotated and annotation_options:
                        self._download_img_annotations(item=item,
                                                       img_filepath=local_filepath,
                                                       annotation_options=annotation_options,
                                                       annotation_filters=annotation_filters,
                                                       local_path=local_path,
                                                       overwrite=overwrite,
                                                       thickness=thickness,
                                                       alpha=alpha,
                                                       with_text=with_text,
                                                       export_version=export_version
                                                       )
                else:
                    if self.items_repository._client_api.sdk_cache.use_cache and \
                            self.items_repository._client_api.cache is not None:
                        response_output = os.path.normpath(response.content)
                        if isinstance(response_output, bytes):
                            response_output = response_output.decode('utf-8')[1:-1]

                        if os.path.isfile(response_output):
                            source_file = response_output
                            with open(source_file, 'wb') as f:
                                data = f.read()
                        download_done = True
                    else:
                        try:
                            if is_local_link and isinstance(response, io.BufferedReader):
                                generator = iter(lambda: response.read(chunk_size), b'')
                            else:
                                generator = response.iter_content(chunk_size=chunk_size)
                            for chunk in generator:
                                if chunk:  # filter out keep-alive new chunks
                                    data.write(chunk)

                            file_validation = True
                            if not is_url:
                                file_validation, start_point, chunk_resume = self.__get_next_chunk(item=item,
                                                                                                   download_progress=data,
                                                                                                   chunk_resume=chunk_resume)
                            if file_validation:
                                download_done = True
                            else:
                                continue
                        except Exception as err:
                            raise err
                        finally:
                            if is_local_link and isinstance(response, io.BufferedReader):
                                try:
                                    response.close()
                                except Exception as err:
                                    pass
                    # go back to the beginning of the stream
                    data.seek(0)
                    data.name = item.name
                    if not save_locally and to_array:
                        if 'image' not in item.mimetype and not is_url:
                            raise PlatformException(
                                error="400",
                                message='Download element type numpy.ndarray support for image only. '
                                        'Item Id: {} is {} type'.format(item.id, item.mimetype))

                        data = np.array(Image.open(data))
        else:
            data = local_filepath
        return data

    def __get_next_chunk(self, item, download_progress, chunk_resume):
        size_validation, file_size, resume = self.__file_validation(item=item,
                                                                    downloaded_file=download_progress)
        start_point = file_size
        if not size_validation:
            if chunk_resume.get(start_point, None) is None:
                chunk_resume = {start_point: 1}
            else:
                chunk_resume[start_point] += 1
            if chunk_resume[start_point] == 3 or not resume:
                raise PlatformException(
                    error=500,
                    message='The downloaded file is corrupted. Please try again. If the issue repeats please contact support.')
        return size_validation, start_point, chunk_resume

    def __default_local_path(self):

        # create default local path
        if self.items_repository._dataset is None:
            local_path = os.path.join(
                self.items_repository._client_api.sdk_cache.cache_path_bin,
                "items",
            )
        else:
            if self.items_repository.dataset._project is None:
                # by dataset name
                local_path = os.path.join(
                    self.items_repository._client_api.sdk_cache.cache_path_bin,
                    "datasets",
                    "{}_{}".format(self.items_repository.dataset.name, self.items_repository.dataset.id),
                )
            else:
                # by dataset and project name
                local_path = os.path.join(
                    self.items_repository._client_api.sdk_cache.cache_path_bin,
                    "projects",
                    self.items_repository.dataset.project.name,
                    "datasets",
                    self.items_repository.dataset.name,
                )
        logger.info("Downloading to: {}".format(local_path))
        return local_path

    @staticmethod
    def get_url_stream(url):
        """
        :param url:
        """
        response = None

        if url.startswith('file://'):
            parsed = urlparse(url)
            path = unquote(parsed.path)
            if parsed.netloc:
                path = f"/{parsed.netloc}{path}"
            path = Path(path).expanduser().resolve()

            if not path.exists():
                raise PlatformException(
                    error='404',
                    message=f'Local file not found: {url}'
                )
            if not path.is_file():
                raise PlatformException(
                    error='400',
                    message=f'Path is not a file: {url}'
                )

            try:
                response = io.BufferedReader(io.FileIO(path, 'rb'))
            except PermissionError as e:
                raise PlatformException(
                    error='403',
                    message=f'Permission denied accessing file: {url}'
                ) from e
        else:
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

        return response
