import os
import datetime
import json
import threading

import logging
from . import disk_cache

logger = logging.getLogger(name=__name__)
CHUNK = 200000


class Reporter:
    """
     ThreadPool Report summary
    """
    ITEMS_DOWNLOAD = 'downloader'
    ITEMS_UPLOAD = 'uploader'
    CONVERTER = 'converter'

    def __init__(self, num_workers, resource, client_api, print_error_logs=False, output_entity=None, no_output=False):
        self._num_workers = num_workers
        self.mutex = threading.Lock()
        self.no_output = no_output
        self._client_api = client_api
        self.key = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self._reports = {'errors': disk_cache.DlCache('errors-' + self.key),
                         'output': disk_cache.DlCache('output-' + self.key),
                         'status': disk_cache.DlCache('status-' + self.key),
                         }
        self._reports.get('status').add('success', 0)
        self._reports.get('status').add('failure', 0)
        self.clear_reporter()
        self._success = dict()
        self._status = dict()
        self._errors = dict()
        self._output = dict()
        self.cache_items = {'errors': self._errors,
                            'status': self._status,
                            'output': self._output}
        self._resource = resource
        self._print_error_logs = print_error_logs
        self._output_entity = output_entity

    @property
    def has_errors(self):
        """
        return True if errors has occurred False otherwise
        """
        return self.failure_count > 0

    def construct_output(self, entity):
        """
        convert the json to his entity object
        """
        if self._output_entity and entity:
            return self._output_entity.from_json(client_api=self._client_api, _json=entity)
        return entity

    @property
    def output(self):
        """
        return a generator for all the outputs or the output it self if it is single
        """
        if self.no_output:
            return

        output = self._reports.get('output')
        for k in output.keys():
            for item in list(output.get(key=k).values()):
                yield self.construct_output(item)

        current = [self.construct_output(output) for output in list(self._output.values()) if output is not None]
        for item in current:
            yield item

    @property
    def status_list(self):
        """
        return a list of all the status that get
        """
        output = dict()
        status_cache = self._reports.get('status')
        for key in status_cache.keys():
            if key not in ['failure', 'success']:
                output.update(status_cache.get(key=key))
        output.update(self._status)
        return list(output.values())

    @property
    def num_workers(self):
        """
        number of the threads to work
        """
        return self._num_workers

    def upcount_num_workers(self):
        """
        increase the number of the threads to work
        """
        self._num_workers += 1

    @property
    def failure_count(self):
        """
        return how many actions fail
        """
        curr = len([suc for suc in (self._success.values()) if suc is False])
        return self._reports.get('status').get(key='failure') + curr

    @property
    def success_count(self):
        """
        return how many actions success
        """
        curr = len([suc for suc in (self._success.values()) if suc is True])
        return self._reports.get('status').get(key='success') + curr

    def status_count(self, status):
        """
        :param status: str of status to check it
        :return: how many times this status appear
        """
        status_list = self.status_list
        return list(status_list).count(status)

    def _write_to_disk(self):
        """
        the function write to the dick the outputs that get until the chunk amount
        """
        with self.mutex:
            if len(self._success) > CHUNK:
                status_cache = self._reports.get('status')
                num_true = sum(list(self._success.values()))
                status_cache.incr(key='failure',
                                  value=len(self._success) - num_true)
                status_cache.incr(key='success',
                                  value=num_true)
                self._success.clear()
            for name, cache_list in self.cache_items.items():
                if len(cache_list) > CHUNK:
                    self._reports[name].push(cache_list)
                    cache_list.clear()

    def set_index(self, ref, error=None, status=None, success=None, output=None):
        """
        set the values that we get from the actions in the reporter
        """
        if self.mutex.locked():
            self.mutex.acquire()
            self.mutex.release()
        if error is not None:
            self._errors[ref] = error

        if status is not None:
            self._status[ref] = status

        if success is not None:
            self._success[ref] = success

        if success and output is not None:
            if not self.no_output:
                self._output[ref] = output

        if len(self._errors) > CHUNK or \
                len(self._status) > CHUNK or \
                len(self._output) > CHUNK or \
                len(self._success) > CHUNK:
            self._write_to_disk()

    def generate_log_files(self):
        """
        build a log file that display the errors
        """
        if len(self._errors) > 0:
            self._reports['errors'].push(self._errors)
            self._errors.clear()

        log_filepath = os.path.join(os.getcwd(),
                                    "log_{}_{}.json".format(self._resource,
                                                            datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")))
        errors_json = dict()
        err_cache = self._reports['errors']
        for k in err_cache.keys():
            errors_json.update(err_cache.get(k))
        if self._print_error_logs:
            for key in errors_json:
                logger.warning("{}\n{}".format(key, errors_json[key]))
            return None
        else:
            with open(log_filepath, "w") as f:
                json.dump(errors_json, f, indent=2)
            return log_filepath

    def clear_reporter(self):
        """
        clear the file system from the outputs
        """
        import shutil
        date_now = datetime.datetime(year=int(self.key.split('-')[0]),
                                     month=int(self.key.split('-')[1]),
                                     day=int(self.key.split('-')[2]))
        cache_dir = os.path.dirname(self._reports['output'].cache_dir)
        cache_files_list = os.listdir(cache_dir)
        # remove all the cache files from the last day
        for filename in cache_files_list:
            try:
                date_file = datetime.datetime(year=int(filename.split('-')[1]),
                                              month=int(filename.split('-')[2]),
                                              day=int(filename.split('-')[3]))
            except:
                continue
            if date_file < date_now:
                try:
                    shutil.rmtree(cache_dir + '\\' + filename)
                except OSError:  # Windows wonkiness
                    pass
