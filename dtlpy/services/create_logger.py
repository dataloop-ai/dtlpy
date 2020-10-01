import datetime
import threading

import os
from logging import handlers, getLogger

from .service_defaults import DATALOOP_PATH


class DataloopLogger(handlers.BaseRotatingHandler):
    """
        Based on logging.handlers.RotatingFileHandler
        Create a new log file after reached maxBytes
        Delete logs older than a threshold default is week)
    """

    def __init__(self, filename, mode='a', maxBytes=0, encoding=None, delay=False):
        if maxBytes > 0:
            mode = 'a'
        super().__init__(filename=filename, mode=mode, encoding=encoding, delay=delay)
        self.maxBytes = maxBytes
        DataloopLogger.clean_dataloop_cache()

    @staticmethod
    def clean_dataloop_cache():
        async_clean = True
        dir_list = [os.path.join(DATALOOP_PATH, d) for d in os.listdir(DATALOOP_PATH)
                    if os.path.isdir(os.path.join(DATALOOP_PATH, d))]
        for path in dir_list:
            if async_clean:
                worker = threading.Thread(target=DataloopLogger.clean_dataloop_cache_thread, kwargs={'path': path})
                worker.daemon = True
                worker.start()
            else:
                DataloopLogger.clean_dataloop_cache_thread(path)

    @staticmethod
    def get_clean_parameter_per(path):
        # (60 * 60 * 24 * 7):  # sec * min * hour * days - delete if older than a week
        # 1e6 100MB
        path_param = [{'type': 'datasets', 'max_time': 60 * 60 * 24 * 30},
                      {'type': 'items', 'max_time': 60 * 60 * 24 * 30},
                      {'type': 'logs', 'max_time': 60 * 60 * 24 * 7, 'max_size': 200 * 1e6},
                      {'type': 'projects', 'max_time': 60 * 60 * 24 * 30}]
        for param in path_param:
            if param['type'] in path:
                return param
        return {'type': 'default', 'max_time': 60 * 60 * 24 * 30}

    @staticmethod
    def clean_dataloop_cache_thread(path, total_cache_size=0, max_param=None):
        logger = getLogger(__name__)
        is_root = False
        if max_param is None:
            max_param = DataloopLogger.get_clean_parameter_per(path)
            is_root = True

        now = datetime.datetime.timestamp(datetime.datetime.now())
        files = [os.path.join(path, f) for f in os.listdir(path)]
        files.sort(key=lambda x: -os.path.getmtime(x))  # newer first
        for filepath in files:
            if os.path.isdir(filepath):
                total_cache_size = DataloopLogger.\
                    clean_dataloop_cache_thread(filepath, total_cache_size=total_cache_size, max_param=max_param)
                # Remove the dir if empty
                if len(os.listdir(filepath)) == 0:
                    os.rmdir(filepath)
                continue
            if 'max_time' in max_param:
                file_time = os.path.getmtime(filepath)
                if (now - file_time) > max_param['max_time']:
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(e)
                    continue
            if 'max_size' in max_param:
                file_size = os.path.getsize(filepath)
                if (total_cache_size + file_size) > max_param['max_time']:
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(e)
                    continue
                total_cache_size += file_size
        if is_root:
            logger.debug("clean_dataloop_cache_thread for {} directory has been ended".format(path))
        return total_cache_size

    @staticmethod
    def get_log_path():
        log_path = os.path.join(DATALOOP_PATH, 'logs')
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        return log_path

    @staticmethod
    def get_log_filepath():
        log_path = DataloopLogger.get_log_path()
        log_filepath = os.path.join(log_path, '{}.log'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')))
        return log_filepath

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # clean older logs (week old)
        DataloopLogger.clean_dataloop_cache()
        # create new log
        self.baseFilename = DataloopLogger.get_log_filepath()
        if not self.delay:
            self.stream = self._open()

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.
        """
        if self.stream is None:  # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:  # are we rolling over?
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)  # due to non-posix-compliant Windows feature
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return 0
