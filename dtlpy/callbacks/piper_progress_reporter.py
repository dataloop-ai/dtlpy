def main():

    from keras.callbacks import Callback
    import numpy as np
    import logging
    import time

    class PiperProgressReporter(Callback):
        def __init__(self, context_reporter):
            super(PiperProgressReporter, self).__init__()
            self.logger = logging.getLogger('dataloop.callback')
            self.context_reporter = context_reporter
            self.results = dict()
            self.epoch_time_start = None

        def on_train_begin(self, logs=None):
            self.results = dict()

        def on_epoch_begin(self, batch, logs=None):
            self.epoch_time_start = time.time()

        def on_epoch_end(self, epoch, logs=None):
            logs_dict = dict(zip(list(logs.keys()), [float(num) for num in np.array(list(logs.values())).tolist()]))
            self.results[epoch] = logs_dict
            self.results[epoch]['runtime'] = time.time() - self.epoch_time_start
            self.context_reporter.report_output(output={'epoch': epoch,
                                                        'logs': logs_dict})

    return PiperProgressReporter
