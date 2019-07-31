import io
import os
import json
import logging
import traceback
import numpy as np
import datetime
import queue
import threading
from progressbar import Bar, ETA, ProgressBar, Timer
from multiprocessing.pool import ThreadPool
from .. import PlatformException, entities, repositories, exceptions

logger = logging.getLogger("dataloop.repositories.items.uploader")

NUM_TRIES = 3  # try to upload 3 time before fail on item


class Uploader:
    def __init__(self, items_repository):
        assert isinstance(items_repository, repositories.Items)
        self.items_repository = items_repository

    def upload(
            self,
            # what to upload
            local_path,
            local_annotations_path=None,
            # upload options
            remote_path=None,
            file_types=None,
            num_workers=32,
            overwrite=False,
            relative_path=True
    ):
        """
        Upload local file to dataset.
        Local filesystem will remain.
        If "*" at the end of local_path (e.g. "/images/*") items will be uploaded without head directory

        :param relative_path: optional - upload with relative path, default = True
        :param overwrite: optional - default = False
        :param local_path: local file or folder to upload
        :param local_annotations_path: path to dataloop format annotations json files.
        :param remote_path: remote path to save.
        :param file_types: list of file type to upload. e.g ['.jpg', '.png']. default is all
        :param num_workers:
        :return: Output (list)
        """
        ###################
        # Default options #
        ###################
        if remote_path is None:
            remote_path = '/'
        if file_types is not None and not isinstance(file_types, list):
            msg = (
                '"file_types" should be a list of file extension. e.g [".jpg", ".png"]'
            )
            logger.exception(msg)
            raise PlatformException(error="400", message=msg)

        ##########################
        # Convert inputs to list #
        ##########################
        if not isinstance(local_path, list):
            local_path_list = [local_path]
        else:
            local_path_list = local_path
            local_path = local_path[0]

        #############
        # fix paths #
        #############
        if isinstance(local_path_list[0], str):
            # local paths for items
            new_path_list = list()
            for path in local_path_list:
                if path.endswith('*'):
                    path = os.path.split(path)[0]
                    for item in os.listdir(path):
                        new_path_list.append(os.path.join(path, item))
                else:
                    new_path_list.append(path)
            local_path_list = new_path_list

            # local path for log file
            if local_path.endswith('*'):
                local_path = os.path.split(local_path)[0]

        if local_annotations_path is None:
            local_annotations_path_list = [None for _ in range(len(local_path_list))]
        else:
            if not isinstance(local_annotations_path, list):
                local_annotations_path_list = [local_annotations_path]
            else:
                local_annotations_path_list = local_annotations_path

        ###########################
        # Handle files or folders #
        ###########################
        if isinstance(local_path_list[0], str):
            # get file type to upload.
            if file_types is None:
                logger.info("Uploading ALL files of type!")
            else:
                logger.info("Uploading ONLY files of type: %s", ",".join(file_types))
            return self.__upload_wrapper(
                binaries=False,
                local_path_list=local_path_list,
                local_annotations_path_list=local_annotations_path_list,
                file_types=file_types,
                remote_path=remote_path,
                num_workers=num_workers,
                overwrite=overwrite,
                relative_path=relative_path,
                local_path=local_path
            )

        else:
            # handle binaries
            return self.__upload_wrapper(
                binaries=True,
                binaries_list=local_path_list,
                annotations_list=local_annotations_path_list,
                remote_path=remote_path,
                num_workers=num_workers,
                overwrite=overwrite,
                relative_path=relative_path
            )

    def __create_existence_dict_worker(
            self, remote_existence_dict, item_remote_filepaths
    ):
        """

        :param remote_existence_dict: a dictionary that state for each desired remote path if file already exists
        :param item_remote_filepaths: a list of all desired uploaded filepaths
        :return:
        """
        try:
            # get pages of item according to remote filepath
            filters = entities.Filters()
            filters.add(field="type", values="file")
            pages = self.items_repository.list(filters=filters)

            # join path and filename for all uploads
            item_remote_filepaths = [
                file[0] + file[1] for file in item_remote_filepaths
            ]
            for page in pages:
                for item in page:
                    # check in current remote item filename exists in uploaded list
                    if item.filename in item_remote_filepaths:
                        remote_existence_dict[item.filename] = item

            # after listing all platform file make sure everything in dictionary
            for item_remote_filepath in item_remote_filepaths:
                if item_remote_filepath not in remote_existence_dict:
                    remote_existence_dict[item_remote_filepath] = None

        except Exception:
            logger.error("{}\nerror getting items from platform".format(traceback.format_exc()))

    def __upload_wrapper(
            self,
            binaries,
            remote_path,
            num_workers,
            overwrite,
            relative_path,
            local_path=None,
            file_types=None,
            binaries_list=None,
            annotations_list=None,
            local_path_list=None,
            local_annotations_path_list=None,
    ):
        def callback(monitor):
            progress.queue.put((monitor.encoder.fields["path"], monitor.bytes_read))

        # globals
        filepaths = None
        annotations_filepaths = None

        if not binaries:
            # get file paths
            filepaths, annotations_filepaths, head_directories, total_size = self.__get_local_files(
                local_path_list=local_path_list,
                local_annotations_path_list=local_annotations_path_list,
                file_types=file_types,
                remote_path=remote_path
            )
            num_files = len(filepaths)

            # create remote_filepath list
            item_remote_filepaths = self.__create_remote_filepath_list(
                num_files=num_files,
                filepaths=filepaths,
                head_directories=head_directories,
                remote_path=remote_path,
                relative_path=relative_path,
            )
        else:
            num_files = len(binaries_list)
            item_remote_filepaths = self.__create_remote_filepath_list_binaries(
                num_files=num_files,
                binaries_list=binaries_list,
                remote_path=remote_path,
            )
            # get size from binaries
            total_size = 0
            try:
                total_size = np.sum([buff.__sizeof__() for buff in binaries_list])
            except Exception:
                logger.warning("Cant get binaries size")

        ##############################
        # get remote existing items  #
        ##############################
        # list for overriding options
        # running a thread to get all items from platform but keep uploading until thread finish
        # thread writing to dict - if value not in dict get for each specific item
        remote_existence_dict = dict()
        thread = threading.Thread(
            target=self.__create_existence_dict_worker,
            kwargs={
                "remote_existence_dict": remote_existence_dict,
                "item_remote_filepaths": item_remote_filepaths,
            },
        )
        thread.start()

        # prepare to upload multi threaded
        logger.info("Uploading {} items..".format(num_files))
        output = [0 for _ in range(num_files)]
        status = ["" for _ in range(num_files)]
        success = [False for _ in range(num_files)]
        errors = ["" for _ in range(num_files)]
        progress = Progress(max_val=total_size, progress_type="upload")
        pool = ThreadPool(processes=num_workers)
        progress.start()
        try:
            for i_item in range(num_files):
                filepath = None
                buffer = None
                if not binaries:
                    # get file from list
                    filepath = filepaths[i_item]
                    # get matching annotation. None if annotations path was not in inputs
                    annotations = annotations_filepaths[i_item]
                else:
                    # get buffer from list
                    buffer = binaries_list[i_item]
                    # get matching annotation. None if annotations path was not in inputs
                    if annotations_list is None:
                        annotations = None
                    else:
                        annotations = annotations_list[i_item]

                # get matching remote filepath
                item_remote_path, item_remote_name = item_remote_filepaths[i_item]
                item_remote_filepath = item_remote_path + item_remote_name

                ########################
                # check if file exists #
                ########################
                if item_remote_filepath not in remote_existence_dict:
                    # item did not found in dict ( thread still running)  - get existence specifically
                    try:
                        remote_existence_dict[
                            item_remote_filepath
                        ] = self.items_repository.get(
                            filepath="{}".format(item_remote_filepath)
                        )
                    except exceptions.NotFound:
                        remote_existence_dict[item_remote_filepath] = None

                if remote_existence_dict[item_remote_filepath] is not None:
                    # item exists in platform
                    found_item = remote_existence_dict[item_remote_filepath]
                    if overwrite:
                        # delete and proceed to upload
                        found_item.delete()
                    else:
                        # update, upload annotations and proceed to next item
                        status[i_item] = "exist"
                        output[i_item] = found_item
                        success[i_item] = True

                        # upload annotations if exists
                        if annotations is not None:
                            pool.apply_async(
                                self.__upload_annotations,
                                kwds={
                                    'annotations': annotations,
                                    'item': found_item
                                }
                            )
                        continue
                ##########
                # upload #
                ##########
                if binaries:
                    filepath = buffer
                pool.apply_async(
                    self.__upload_single_item_wrapper,
                    kwds={
                        "i_item": i_item,
                        "filepath": filepath,
                        "annotations": annotations,
                        "item_remote_path": item_remote_path,
                        "item_remote_name": item_remote_name,
                        "callback": callback,
                        "status": status,
                        "success": success,
                        "output": output,
                        "errors": errors,
                    },
                )
        except Exception as e:
            logger.exception(e)
            logger.exception(traceback.format_exc())
        finally:
            pool.close()
            pool.join()
            progress.queue.put((None, None))
            progress.queue.join()
            progress.finish()
        n_upload = status.count("upload")
        n_exist = status.count("exist")
        n_error = status.count("error")
        logger.info("Number of files uploaded: {}".format(n_upload))
        logger.info("Number of files exists: {}".format(n_exist))
        logger.info("Number of errors: {}".format(n_error))
        logger.info("Total number of files: {}".format(n_upload + n_exist))
        # log error
        if n_error > 0:
            log_filepath = "log_%s.txt" % datetime.datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            if not binaries:
                if os.path.isfile(local_path):
                    local_path = os.path.split(local_path)[0]
                log_filepath = os.path.join(local_path, log_filepath)
            errors_list = [
                errors[i_job] for i_job, suc in enumerate(success) if suc is False
            ]
            with open(log_filepath, "w") as f:
                f.write("\n".join(errors_list))
            logger.warning(
                "Errors in {n_error} files. See {log_filepath} for full log".format(
                    n_error=n_error, log_filepath=log_filepath
                )
            )
        # remove empty cells
        output = [output[i_job] for i_job, suc in enumerate(success) if suc is True]
        if len(output) == 1:
            output = output[0]
        return output

    @staticmethod
    def __get_local_files(local_path_list, local_annotations_path_list, file_types, remote_path):
        filepaths = list()
        annotations_filepaths = list()
        head_directories = list()
        total_size = 0
        for local_path, local_annotations_path in zip(
                local_path_list, local_annotations_path_list
        ):
            ##########################
            #  get files from folder #
            ##########################
            if os.path.isdir(local_path):
                # create a list of all the items to upload
                for root, subdirs, files in os.walk(local_path):
                    for filename in files:
                        _, ext = os.path.splitext(filename)
                        if file_types is None or ext in file_types:
                            # get full image filepath
                            filepath = os.path.join(root, filename)
                            # extract item's size
                            total_size += os.path.getsize(filepath)
                            # get annotations file
                            if local_annotations_path is not None:
                                # change path to annotations
                                annotations_filepath = filepath.replace(
                                    local_path, local_annotations_path
                                )
                                # remove image extension
                                annotations_filepath, _ = os.path.splitext(
                                    annotations_filepath
                                )
                                # add json extension
                                annotations_filepath += ".json"
                            else:
                                annotations_filepath = None
                            # append to list
                            filepaths.append(filepath)
                            head_directories.append(local_path)
                            annotations_filepaths.append(annotations_filepath)
            ####################
            #  add single file #
            ####################
            elif os.path.isfile(local_path):
                filepath = local_path
                # extract item's size
                total_size += os.path.getsize(filepath)
                if local_annotations_path is not None:
                    # change path to annotations
                    annotations_filepath = filepath.replace(
                        local_path, local_annotations_path
                    )
                    # remove image extension
                    annotations_filepath, _ = os.path.splitext(annotations_filepath)
                    # add json extension
                    annotations_filepath += ".json"
                else:
                    annotations_filepath = None
                # append to list
                filepaths.append(filepath)
                head_directories.append('*' + remote_path)
                annotations_filepaths.append(annotations_filepath)
            else:
                logger.exception("Directory or file doest exists: %s", local_path)
                raise PlatformException(
                    "404", "Directory or file doest exists: %s" % local_path
                )
        return filepaths, annotations_filepaths, head_directories, total_size

    def __upload_single_item(
            self,
            filepath,
            annotations=None,
            remote_path=None,
            uploaded_filename=None,
            callback=None,
    ):
        """
        Upload an item to dataset

        :param annotations: platform format annotations file to add to the new item
        :param filepath: local filepath of the item
        :param remote_path: remote directory of filepath to upload
        :param uploaded_filename: optional - remote filename
        :param callback:
        :return: Item object
        """
        if remote_path is None:
            remote_path = "/"
        if not remote_path.endswith("/"):
            remote_path += "/"
        if isinstance(filepath, str):
            # upload local file
            if not os.path.isfile(filepath):
                logger.exception("Filepath doesnt exists. file: %s" % filepath)
                message = "Filepath doesnt exists. file: %s" % filepath
                raise PlatformException("404", message)
            if uploaded_filename is None:
                uploaded_filename = os.path.basename(filepath)
            remote_url = "/datasets/%s/items" % self.items_repository.dataset.id
            result, response = self.items_repository.client_api.upload_local_file(
                filepath=filepath,
                remote_url=remote_url,
                uploaded_filename=uploaded_filename,
                remote_path=remote_path,
                callback=callback,
            )
        else:
            # upload from buffer
            if isinstance(filepath, bytes):
                buffer = io.BytesIO(filepath)
            elif isinstance(filepath, io.BytesIO):
                buffer = filepath
            elif isinstance(filepath, io.BufferedReader):
                buffer = filepath
            elif isinstance(filepath, io.TextIOWrapper):
                buffer = filepath
            else:
                raise PlatformException("400", "unknown file type")

            if uploaded_filename is None:
                if hasattr(filepath, "name"):
                    uploaded_filename = filepath.name
                else:
                    logger.exception(
                        "Must have filename when uploading bytes array (uploaded_filename)"
                    )
                    raise PlatformException(
                        "400",
                        "Must have filename when uploading bytes array (uploaded_filename)",
                    )
            files = {"file": (uploaded_filename, buffer)}
            payload = {
                "path": os.path.join(remote_path, uploaded_filename).replace("\\", "/"),
                "type": "file",
            }
            result, response = self.items_repository.client_api.gen_request(
                req_type="post",
                path="/datasets/%s/items" % self.items_repository.dataset.id,
                files=files,
                data=payload,
            )
        if result:
            item = self.items_repository.items_entity.from_json(
                client_api=self.items_repository.client_api,
                _json=response.json(),
                dataset=self.items_repository.dataset,
            )
            if annotations is not None:
                try:
                    self.__upload_annotations(annotations=annotations, item=item)
                except Exception:
                    logger.error(traceback.format_exc())
            logger.debug("Item uploaded successfully. Item id: %s" % item.id)
            return item
        else:
            raise PlatformException(response)

    def __upload_single_item_wrapper(
            self,
            i_item,
            filepath,
            annotations,
            item_remote_path,
            item_remote_name,
            callback,
            status,
            success,
            output,
            errors,
    ):
        result = False
        err = None
        for i_try in range(NUM_TRIES):
            logger.debug("upload item: {}, try {}".format(item_remote_name, i_try))
            try:
                result = self.__upload_single_item(
                    filepath=filepath,
                    annotations=annotations,
                    remote_path=item_remote_path,
                    uploaded_filename=item_remote_name,
                    callback=callback,
                )
                if result:
                    break
            except Exception as e:
                err = e
        if result:
            status[i_item] = "upload"
            output[i_item] = result
            success[i_item] = True
        else:
            status[i_item] = "error"
            output[i_item] = item_remote_path + item_remote_name
            success[i_item] = False
            errors[i_item] = "%s\n%s" % (err, traceback.format_exc())

    @staticmethod
    def __create_remote_filepath_list(
            num_files, filepaths, head_directories, remote_path, relative_path
    ):
        item_remote_filepaths = [list() for _ in range(num_files)]
        for i_item in range(num_files):
            # get file from list
            filepath = filepaths[i_item]
            # get file's folder
            head_directory = head_directories[i_item]
            # get the remote path according the upload options
            if head_directory.startswith('*'):
                item_relative_path = os.path.basename(filepath)
            else:
                if relative_path:
                    item_relative_path = os.path.relpath(
                        filepath, os.path.dirname(head_directory)
                    )
                else:
                    item_relative_path = remote_path
            #################################
            # get remote file path and name #
            #################################
            item_remote_path = os.path.join(
                remote_path, os.path.dirname(item_relative_path)
            ).replace("\\", "/")
            item_remote_name = os.path.basename(filepath)
            if not item_remote_path.endswith("/"):
                item_remote_path += "/"
            item_remote_filepaths[i_item] = [item_remote_path, item_remote_name]
        return item_remote_filepaths

    @staticmethod
    def __create_remote_filepath_list_binaries(num_files, binaries_list, remote_path):
        item_remote_filepaths = [list() for _ in range(num_files)]
        for i_item in range(num_files):
            buffer = binaries_list[i_item]
            # get the remote path according the upload options
            #################################
            # get remote file path and name #
            #################################
            item_remote_path = remote_path
            if not hasattr(buffer, "name"):
                raise PlatformException(
                    error="400",
                    message='Must put attribute "name" on buffer (with file name) when uploading buffers',
                )
            item_remote_name = buffer.name
            if not item_remote_path.endswith("/"):
                item_remote_path += "/"
            item_remote_filepaths[i_item] = [item_remote_path, item_remote_name]
        return item_remote_filepaths

    @staticmethod
    def __upload_annotations(annotations, item):
        """
        Upload annotations from file
        :param annotations: file path
        :param item: item
        :return:
        """
        if isinstance(annotations, str) and os.path.isfile(annotations):
            with open(annotations, "r") as f:
                data = json.load(f)
            if "annotations" in data:
                annotations = data["annotations"]
            elif isinstance(data, list):
                annotations = data
            else:
                raise PlatformException(
                    error="400",
                    message='MISSING "annotations" in annotations file, cant upload. item_id: {}, '
                            "annotations_filepath: {}".format(item.id, annotations),
                )
            item.annotations.upload(annotations=annotations)


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
        self.progressbar = ProgressBar(
            widgets=[" [", Timer(), "] ", Bar(), " (", ETA(), ")"],
            redirect_stdout=True,
            redirect_stderr=True,
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
                if msg == "download":
                    self.download += 1
                elif msg == "exist":
                    self.exist += 1
                elif msg == "error":
                    self.error += 1
                else:
                    logger.exception("Unknown message type: %s", msg)
                    # update bar
                self.progressbar.update(self.download + self.exist)
            except Exception as error:
                logger.exception(error)
            finally:
                self.queue.task_done()

    def run(self):
        if self.progress_type == "upload":
            self.run_upload()
        elif self.progress_type == "download":
            self.run_download()
        else:
            assert False
