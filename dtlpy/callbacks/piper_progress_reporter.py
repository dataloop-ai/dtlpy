def main():

    from keras.callbacks import Callback
    import numpy as np
    import logging
    import time

    class PiperProgressReporter(Callback):
        def __init__(self, session_id, thread_queue):
            super(PiperProgressReporter, self).__init__()
            self.logger = logging.getLogger('dataloop.callback')
            self.session_id = session_id
            self.thread_queue = thread_queue
            self.results = dict()
            self.epoch_time_start = None

        def on_train_begin(self, logs=None):
            self.results = dict()

        def on_epoch_begin(self, batch, logs=None):
            self.epoch_time_start = time.time()

        def on_epoch_end(self, epoch, logs=None):
            self.results[epoch] = dict(zip(list(logs.keys()), np.array(list(logs.values())).tolist()))
            self.results[epoch]['runtime'] = time.time() - self.epoch_time_start
            self.thread_queue.put({'type': 'train_progress',
                                   'body': {'train_progress': self.results}
                                   })

    return PiperProgressReporter
