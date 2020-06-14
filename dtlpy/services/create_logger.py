import datetime
import os
from logging import handlers


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
        DataloopLogger.clean_logs()

    @staticmethod
    def clean_logs():
        log_path = DataloopLogger.get_log_path()
        now = datetime.datetime.utcnow().timestamp()
        files = [os.path.join(log_path, f) for f in os.listdir(log_path)]
        files.sort(key=lambda x: -os.path.getmtime(x))  # newer first
        total_logs_size = 0
        for filepath in files:
            # print(filepath)
            file_time = os.path.getmtime(filepath)
            # delete if older than a week
            if (now - file_time) > (60 * 60 * 24 * 7):  # sec * min * hour * days
                os.remove(filepath)
                continue
            file_size = os.path.getsize(filepath)
            if (total_logs_size + file_size) > 200 * 1e6:  # 100MB
                os.remove(filepath)
                continue
            total_logs_size += file_size

    @staticmethod
    def get_log_path():
        log_path = os.path.join(os.path.expanduser('~'), '.dataloop', 'logs')
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
        DataloopLogger.clean_logs()
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
