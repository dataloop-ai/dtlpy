import os
import datetime
import json
import numpy as np
import logging

logger = logging.getLogger(name=__name__)


class Reporter:
    """
     ThreadPool Report summary
    """
    ITEMS_DOWNLOAD = 'downloader'
    ITEMS_UPLOAD = 'uploader'
    CONVERTER = 'converter'

    def __init__(self, num_workers, resource, print_error_logs=False):
        self._num_workers = num_workers
        self._refs = dict(list(enumerate([None] * num_workers)))
        self._success = dict(list(enumerate([False] * num_workers)))
        self._status = dict(list(enumerate([""] * num_workers)))
        self._errors = dict(list(enumerate([None] * num_workers)))
        self._output = dict(list(enumerate([None] * num_workers)))

        self._resource = resource
        self._print_error_logs = print_error_logs


    @property
    def has_errors(self):
        return self.failure_count > 0

    @property
    def output(self):
        output = [output for output in list(self._output.values()) if output is not None]
        # TODO 2.0 always return a list
        return output[0] if len(output) == 1 else output

    @property
    def status_list(self):
        return np.unique(list(self._status.values()))

    @property
    def num_workers(self):
        return self._num_workers

    def upcount_num_workers(self):
        self._num_workers += 1

    @property
    def failure_count(self):
        return len([suc for suc in list(self._success.values()) if suc is False])

    @property
    def success_count(self):
        return len([suc for suc in list(self._success.values()) if suc is True])

    def status_count(self, status):
        return list(self._status.values()).count(status)
        # return self._status.count(status)

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
        errors_list = [self._errors[i_job] for i_job, suc in self._success.items() if suc is False]
        ref_list = [self._refs[i_job] for i_job, suc in self._success.items() if suc is False]
        errors_json = {item_ref: error for item_ref, error in zip(ref_list, errors_list)}
        if self._print_error_logs:
            for key in errors_json:
                logger.warning("{}\n{}".format(key, errors_json[key]))
            return None
        else:
            with open(log_filepath, "w") as f:
                json.dump(errors_json, f, indent=2)
            return log_filepath
