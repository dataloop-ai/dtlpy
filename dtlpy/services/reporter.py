import os
import datetime
import json
import threading

import numpy as np
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
        self.writing = False
        self.mutex = threading.Lock()
        self.no_output = no_output
        self._client_api = client_api
        self.key = datetime.datetime.now().strftime('%S-%M-%H-%d-%m-%Y')
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

        self._resource = resource
        self._print_error_logs = print_error_logs
        self._output_entity = output_entity

    @property
    def has_errors(self):
        return self.failure_count > 0

    def construct_output(self, entity):
        if self._output_entity and entity:
            return self._output_entity.from_json(client_api=self._client_api, _json=entity)
        return entity

    @property
    def output(self):
        if self.no_output:
            return

        cache = self._reports.get('output')
        for k in cache.keys():
            for item in list(cache.get(key=k).values()):
                yield self.construct_output(item)

        current = [self.construct_output(output) for output in list(self._output.values()) if output is not None]
        for item in current:
            yield item

    @property
    def status_list(self):
        output = dict()
        status_cache = self._reports.get('status')
        for key in status_cache.keys():
            if key not in ['failure', 'success']:
                output.update(status_cache.get(key=key))
        output.update(self._status)
        return list(output.values())

    @property
    def num_workers(self):
        return self._num_workers

    def upcount_num_workers(self):
        self._num_workers += 1

    @property
    def failure_count(self):
        curr = len([suc for suc in (self._success.values()) if suc is False])
        return self._reports.get('status').get(key='failure') + curr

    @property
    def success_count(self):
        curr = len([suc for suc in (self._success.values()) if suc is True])
        return self._reports.get('status').get(key='success') + curr

    def status_count(self, status):
        status_list = self.status_list
        return list(status_list).count(status)

    def _write_to_disk(self):
        self.mutex.acquire()
        self.writing = True
        list_items_values = [self._errors,
                             self._status,
                             self._output,
                             ]

        list_items_names = ['errors',
                            'status',
                            'output',
                            ]

        if len(self._success) > CHUNK:
            status_cache = self._reports.get('status')
            status_cache.incr(key='failure',
                              value=len([suc for suc in list(self._success.values()) if suc is False]))
            status_cache.incr(key='success',
                              value=len([suc for suc in list(self._success.values()) if suc is True]))
            self._success.clear()
        for i in range(len(list_items_values)):
            if len(list_items_values[i]) > CHUNK:
                self._reports[list_items_names[i]].push(list_items_values[i])
                list_items_values[i].clear()

        self.writing = False
        self.mutex.release()

    def set_index(self, ref, error=None, status=None, success=None, output=None):
        if self.writing:
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

        if len(self._errors) > CHUNK or len(self._status) > CHUNK or len(
                self._output) > CHUNK or len(self._success) > CHUNK:
            self._write_to_disk()

    def generate_log_files(self):
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
        date_now = datetime.datetime(year=int(self.key.split('-')[5]), month=int(self.key.split('-')[4]),
                                     day=int(self.key.split('-')[3]))
        cache_dir = os.path.dirname(self._reports['output'].cache_dir)
        cache_files_list = os.listdir(cache_dir)
        # remove all the cache files from the last day
        for filename in cache_files_list:
            try:
                date_file = datetime.datetime(year=int(filename.split('-')[6]), month=int(filename.split('-')[5]),
                                              day=int(filename.split('-')[4]))
            except:
                continue
            if date_file < date_now:
                try:
                    shutil.rmtree(cache_dir + '\\' + filename)
                except OSError:  # Windows wonkiness
                    pass
