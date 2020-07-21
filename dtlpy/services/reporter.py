import os
import datetime
import json
import numpy as np


class Reporter:
    """
     ThreadPool Report summary
    """
    ITEMS_DOWNLOAD = 'downloader'
    ITEMS_UPLOAD = 'uploader'
    CONVERTER = 'converter'

    def __init__(self, num_workers, resource):
        self._num_workers = num_workers
        self._refs = [None for _ in range(num_workers)]
        self._success = [False for _ in range(num_workers)]
        self._status = ["" for _ in range(num_workers)]
        self._errors = [None for _ in range(num_workers)]
        self._output = [None for _ in range(num_workers)]
        self._resource = resource

    @property
    def has_errors(self):
        return self.failure_count > 0

    @property
    def output(self):
        output = [output for output in self._output if output is not None]
        return output[0] if len(output) == 1 else output

    @property
    def status_list(self):
        return np.unique(self._status)

    @property
    def num_workers(self):
        return self._num_workers

    @property
    def failure_count(self):
        return len([suc for suc in self._success if suc is False])

    @property
    def success_count(self):
        return len([suc for suc in self._success if suc is True])

    def status_count(self, status):
        return self._status.count(status)

    def set_index(self, i_item, error=None, status=None, ref=None, success=None, output=None):
        if error is not None:
            self._errors[i_item] = error
        if status is not None:
            self._status[i_item] = status
        if ref is not None:
            self._refs[i_item] = ref
        if success is not None:
            self._success[i_item] = success
        if success and output is not None:
            self._output[i_item] = output

    def generate_log_files(self):
        log_filepath = os.path.join(os.getcwd(),
                                    "log_{}_{}.json".format(self._resource,
                                                            datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")))
        errors_list = [self._errors[i_job] for i_job, suc in enumerate(self._success) if suc is False]
        ref_list = [self._refs[i_job] for i_job, suc in enumerate(self._success) if suc is False]
        errors_json = {item_ref: error for item_ref, error in zip(ref_list, errors_list)}
        with open(log_filepath, "w") as f:
            json.dump(errors_json, f, indent=2)

        return log_filepath
