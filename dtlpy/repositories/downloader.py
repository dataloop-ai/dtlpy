import io
import os
import json
import tqdm
import traceback
import datetime
from PIL import Image
import threading
import logging

from multiprocessing.pool import ThreadPool
import dtlpy as dl

from .. import entities, PlatformException, utilities

logger = logging.getLogger("dataloop.repositories.items.downloader")

NUM_TRIES = 3  # try to download 3 time before fail on item


class Downloader:
    def __init__(self, items_repository):
        self.items_repository = items_repository

    def download(self,
                 # filter options
                 filters=None,
                 items=None,
                 # download options
                 local_path=None,
                 file_types=None,
                 save_locally=True,
                 num_workers=32,
                 overwrite=False,
                 annotation_options=None,
                 to_items_folder=True,
                 thickness=1,
                 with_text=False
                 ):
        """
        Download dataset by filters.
        Filtering the dataset for items and save them local
        Optional - also download annotation, mask, instance and image mask of the item

        :param filters: Filters entity or a dictionary containing filters parameters
        :param items: download Item entity or item_id (or a list of item)
        :param overwrite: optional - default = False
        :param local_path: local folder or filename to save to.
        :param file_types: a list of file type to download. e.g ['video/webm', 'video/mp4', 'image/jpeg', 'image/png']
        :param num_workers: default - 32
        :param save_locally: bool. save to disk or return a buffer
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :param to_items_folder: Create 'items' folder and download items to it
        :param with_text: optional - add text to annotations, default = False
        :param thickness: optional - line thickness, if -1 annotation will be filled, default =1
        :return: Output (list)
        """

        ###################
        # Default options #
        ###################
        # filters
        if filters is None:
            filters = dl.Filters()

        # file types
        if file_types is not None:
            filters.add(field='metadata.system.mimetype', values=file_types, operator='in')

        # annotation options
        if annotation_options is None:
            annotation_options = list()
        elif not isinstance(annotation_options, list):
            annotation_options = [annotation_options]

        ##############
        # local path #
        ##############

        if local_path is None:
            # create default local path
            local_path = self.__default_local_path()

        if os.path.isdir(local_path):
            logger.info('Local folder already exists:{}. merge/overwrite according to "overwrite option"'.format(
                local_path))
        else:
            # check if filename
            _, ext = os.path.splitext(local_path)
            if not ext:
                logger.info("Creating new directory for download: {}".format(local_path))
                os.makedirs(local_path, exist_ok=True)

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
                    message='Unknown items type to download. expecting str or Item entities. Got "{}" instead'.format(
                        type(items[0])
                    ),
                )

            # convert to list of list (like pages and page)
            items_to_download = [items]
            num_items = len(items)
        else:
            items_to_download = self.items_repository.list(filters=filters)
            num_items = items_to_download.items_count

        ####################
        # annotations json #
        ####################
        # download annotations' json files in a new thread
        # items will start downloading and if json not exists yet - will download for each file
        if annotation_options:
            # a new folder named 'json' will be created under the "local_path"
            logger.info("Downloading annotations formats: {}".format(annotation_options))
            thread = threading.Thread(target=self.download_annotations,
                                      kwargs={"dataset": self.items_repository.dataset,
                                              "local_path": local_path,
                                              'overwrite': overwrite},
                                      )
            thread.start()
        ###############
        # downloading #
        ###############
        # create result lists
        output = [None for _ in range(num_items)]
        success = [False for _ in range(num_items)]
        status = ["" for _ in range(num_items)]
        errors = [None for _ in range(num_items)]

        # pool
        pool = ThreadPool(processes=num_workers)
        # download
        with tqdm.tqdm(total=num_items) as pbar:
            try:
                i_item = 0
                for page in items_to_download:
                    for item in page:
                        if item.type == "dir":
                            continue
                        if save_locally:
                            # get local file path
                            item_local_path, item_local_filepath = self.__get_local_filepath(local_path=local_path,
                                                                                             item=item,
                                                                                             to_items_folder=to_items_folder)

                            if os.path.isfile(item_local_filepath) and not overwrite:
                                logger.debug("File Exists: {}".format(item_local_filepath))
                                status[i_item] = "exist"
                                output[i_item] = item_local_filepath
                                success[i_item] = True
                                i_item += 1
                                if annotation_options and item.annotated:
                                    # download annotations only
                                    pool.apply_async(
                                        self.__download_img_annotations,
                                        kwds={
                                            "item": item,
                                            "img_filepath": item_local_filepath,
                                            "overwrite": overwrite,
                                            "annotation_options": annotation_options,
                                            "local_path": local_path,
                                            "thickness": thickness,
                                            "with_text": with_text
                                        },
                                    )
                                continue

                        else:
                            item_local_path = None
                            item_local_filepath = None

                        # download single item
                        logger.debug("File Download: {}".format(item.filename))
                        pool.apply_async(
                            self.__thread_download_wrapper,
                            kwds={
                                "i_item": i_item,
                                "item": item,
                                "item_local_path": item_local_path,
                                "item_local_filepath": item_local_filepath,
                                "save_locally": save_locally,
                                "annotation_options": annotation_options,
                                "status": status,
                                "output": output,
                                "success": success,
                                "errors": errors,
                                "pbar": pbar,
                                "overwrite": overwrite,
                                "thickness": thickness,
                                "with_text": with_text
                            },
                        )
                        i_item += 1
            except Exception as e:
                logger.exception(e)
            finally:
                pool.close()
                pool.join()
        # reporting
        n_download = status.count("download")
        n_exist = status.count("exist")
        n_error = status.count("error")
        logger.info("Number of files downloaded:{}".format(n_download))
        logger.info("Number of files exists: {}".format(n_exist))
        logger.info("Total number of files: {}".format(n_download + n_exist))

        # log error
        if n_error > 0:
            log_filepath = "log_%s.txt" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            errors_list = [errors[i_job] for i_job, suc in enumerate(success) if suc is False]
            ids_list = [output[i_job] for i_job, suc in enumerate(success) if suc is False]
            errors_json = {item_id: error for item_id, error in zip(ids_list, errors_list)}
            with open(log_filepath, "w") as f:
                json.dump(errors_json, f, indent=4)
            logger.warning("Errors in {} files. See {} for full log".format(n_error, log_filepath))
        if len(output) == 1:
            return output[0]
        else:
            return output

    def __thread_download_wrapper(self,
                                  i_item,
                                  item,
                                  item_local_path,
                                  item_local_filepath,
                                  save_locally,
                                  annotation_options,
                                  status,
                                  output,
                                  success,
                                  errors,
                                  pbar,
                                  overwrite,
                                  thickness,
                                  with_text
                                  ):

        download = False
        err = None
        for i_try in range(NUM_TRIES):
            logger.debug("download item: {}, try {}".format(item.id, i_try))
            try:
                download = self.__thread_download(
                    item=item,
                    save_locally=save_locally,
                    local_path=item_local_path,
                    local_filepath=item_local_filepath,
                    annotation_options=annotation_options,
                    overwrite=overwrite,
                    thickness=thickness,
                    with_text=with_text
                )
                if download:
                    break
            except Exception as e:
                err = e
        pbar.update()
        if not download:
            if err is None:
                err = self.items_repository.client_api.platform_exception
            status[i_item] = "error"
            output[i_item] = item.id
            success[i_item] = False
            errors[i_item] = "%s\n%s" % (err, traceback.format_exc())
        else:
            status[i_item] = "download"
            output[i_item] = download
            success[i_item] = True

    @staticmethod
    def download_annotations(dataset, local_path, overwrite=False):
        """
        Download annotations json for entire dataset

        :param dataset: Dataset entity
        :param overwrite: optional - overwrite annotations if exist, default = false
        :param local_path:
        :return:
        """

        def download_single_chunk(w_filepath, w_url):
            try:
                # remove heading of the url
                w_url = w_url[w_url.find('/dataset'):]
                # get zip from platform
                success, response = dataset.client_api.gen_request(req_type="get",
                                                                   path=w_url,
                                                                   stream=True)

                if not success:
                    raise PlatformException(response)

                # downloading zip from platform
                with open(w_filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                # unzipping annotations to directory
                utilities.Miscellaneous.unzip_directory(zip_filename=w_filepath,
                                                        to_directory=local_path)
            except Exception:
                raise PlatformException(error='400',
                                        message="Getting annotations from zip failed: {}".format(w_url))
            finally:
                # cleanup
                if os.path.isfile(w_filepath):
                    os.remove(w_filepath)

        local_path = os.path.join(local_path, "json")
        # only if json folder does not exist or exist and overwrite
        if not os.path.isdir(os.path.join(local_path, 'json')) or overwrite:
            # create local path to download and save to
            if not os.path.isdir(local_path):
                os.makedirs(local_path)
        urls = list()
        if isinstance(dataset.export['zip'], str):
            urls.append(dataset.export['zip'])
        elif isinstance(dataset.export['zip'], dict):
            for url in dataset.export['zip']['chunks']:
                urls.append(url)
        pool = ThreadPool(processes=32)
        for i_url, url in enumerate(urls):
            # zip filepath
            zip_filepath = os.path.join(local_path, "annotations_{}.zip".format(i_url))
            # send url to pool
            pool.apply_async(download_single_chunk, kwds={'w_url': url,
                                                          'w_filepath': zip_filepath})
        pool.close()
        pool.join()
        pool.terminate()

    @staticmethod
    def __download_img_annotations(item, img_filepath, local_path, overwrite, annotation_options,
                                   thickness=1, with_text=False):

        # fix local path
        if local_path.endswith("/items") or local_path.endswith("\\items"):
            local_path = os.path.dirname(local_path)

        annotation_rel_path = item.filename[1:]

        # find annotations json
        annotations_json_filepath = os.path.join(local_path, "json", item.filename[1:])
        name, _ = os.path.splitext(annotations_json_filepath)
        annotations_json_filepath = name + ".json"

        if os.path.isfile(annotations_json_filepath):

            # if exists take from json file
            with open(annotations_json_filepath, "r") as f:
                data = json.load(f)
            if "annotations" in data:
                data = data["annotations"]
            annotations = entities.AnnotationCollection.from_json(_json=data, item=item)
        else:

            # if doesnt exist get from platform
            annotations = item.annotations.list()

        # get image shape
        if item.width is not None and item.height is not None:
            img_shape = (item.height, item.width)
        elif 'image' in item.mimetype:
            img_shape = Image.open(img_filepath).size[::-1]
        else:
            img_shape = (0, 0)

        # download all annotation options
        for option in annotation_options:
            # get path and create dirs
            annotation_filepath = os.path.join(local_path, option, annotation_rel_path)
            if not os.path.isdir(os.path.dirname(annotation_filepath)):
                os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
            temp_path, ext = os.path.splitext(annotation_filepath)

            if option == "json":
                if not os.path.isfile(annotations_json_filepath):
                    annotations.download(
                        filepath=annotations_json_filepath,
                        annotation_format=option,
                        height=img_shape[0],
                        width=img_shape[1],
                    )
            elif option in ["mask", "instance"]:
                annotation_filepath = temp_path + ".png"
                if not os.path.isfile(annotation_filepath) or overwrite:
                    # if not exists OR (exists AND overwrite)
                    if not os.path.exists(os.path.dirname(annotation_filepath)):
                        # create folder if not exists
                        os.makedirs(os.path.dirname(annotation_filepath), exist_ok=True)
                    annotations.download(
                        filepath=annotation_filepath,
                        annotation_format=option,
                        height=img_shape[0],
                        width=img_shape[1],
                        thickness=thickness,
                        with_text=with_text
                    )
            else:
                raise PlatformException(
                    "400", "Unknown annotation option: {}".format(option)
                )

    @staticmethod
    def __get_local_filepath(local_path, item, to_items_folder):
        # create paths
        _, ext = os.path.splitext(local_path)
        if ext:
            # local_path is a filename
            local_filepath = local_path
            local_path = os.path.dirname(local_filepath)
        else:
            # if directory - get item's filename
            if to_items_folder:
                local_path = os.path.join(local_path, "items")
            local_filepath = os.path.join(local_path, item.filename[1:])
        return local_path, local_filepath

    def __thread_download(self,
                          item,
                          save_locally,
                          local_path,
                          local_filepath,
                          overwrite,
                          annotation_options,
                          chunk_size=8192,
                          thickness=1,
                          with_text=False
                          ):
        """
        Get a single item's binary data
        Calling this method will returns the item body itself , an image for example with the proper mimetype.

        :param item: Item entity to download
        :param save_locally: bool. save to file or return buffer
        :param local_path: optional - local folder or filename to save to.
        :param chunk_size: size of chunks to download - optional. default = 8192
        :param annotation_options: download annotations options: ['mask', 'img_mask', 'instance', 'json']
        :return:
        """
        # check if need to download image binary from platform
        need_to_download = True
        if save_locally and os.path.isfile(local_filepath):
            need_to_download = overwrite

        response = None
        if need_to_download:
            result, response = self.items_repository.client_api.gen_request(
                req_type="get",
                path="/datasets/%s/items/%s/stream" % (item.dataset.id, item.id),
                stream=True,
            )
            if not result:
                raise PlatformException(response)
        if save_locally:
            # save to file
            if not os.path.exists(os.path.dirname(local_filepath)):
                # create folder if not exists
                os.makedirs(os.path.dirname(local_filepath), exist_ok=True)
            # download and save locally
            total_length = response.headers.get("content-length")
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            # save to output variable
            data = local_filepath
            # if image - can download annotation mask
            if item.annotated and annotation_options:
                self.__download_img_annotations(
                    item=item,
                    img_filepath=local_filepath,
                    annotation_options=annotation_options,
                    local_path=local_path,
                    overwrite=overwrite,
                    thickness=thickness,
                    with_text=with_text
                )
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

    def __default_local_path(self):

        # create default local path
        if self.items_repository.dataset.project is None:
            # by dataset name
            local_path = os.path.join(
                os.path.expanduser("~"),
                ".dataloop",
                "datasets",
                "%s_%s"
                % (
                    self.items_repository.dataset.name,
                    self.items_repository.dataset.id,
                ),
            )
        else:
            # by dataset and project name
            local_path = os.path.join(
                os.path.expanduser("~"),
                ".dataloop",
                "projects",
                self.items_repository.dataset.project.name,
                "datasets",
                self.items_repository.dataset.name,
            )
        logger.info("Downloading to: {}".format(local_path))
        return local_path
