def main():

    from keras.callbacks import Callback
    import dtlpy as dl
    import numpy as np
    import logging
    import time
    import json
    import os

    class ProgressViewer(Callback):
        def __init__(self, session_id, directory=None):
            super(ProgressViewer, self).__init__()
            self.logger = logging.getLogger('dataloop.callback')
            # init Dataloop instance
            # get sessions artifact
            self.session = dl.sessions.get(session_id=session_id)
            artifacts = self.session.artifacts.list()
            self.artifact = None
            for artifact in artifacts:
                if artifact.type == 'progress':
                    self.artifact = artifact
                    self.logger.info('Progress artifact found. overwriting. artifact_id: %s' % self.artifact.id)
                    break
            if self.artifact is None:
                self.artifact = self.session.artifacts.create(artifact_name='progress.yml',
                                                              artifact_type='progress',
                                                              description='update progress on each epoch')

                self.logger.info('[INFO] Creating progress artifact. artifact_id: %s' % self.artifact.id)
            if directory is None:
                directory = './results'
            if not os.path.isdir(directory):
                os.makedirs(directory)
            self.filename = os.path.join(directory, 'progress.yml')
            self.results = dict()
            self.epoch_time_start = None

        def on_train_begin(self, logs=None):
            self.results = dict()

        def on_epoch_begin(self, batch, logs=None):
            self.epoch_time_start = time.time()

        def on_epoch_end(self, epoch, logs=None):
            self.results[epoch] = dict(zip(list(logs.keys()), np.array(list(logs.values())).tolist()))
            self.results[epoch]['runtime'] = time.time() - self.epoch_time_start
            with open(self.filename, 'w') as f:
                json.dump(self.results, f)
            self.session.artifacts.upload(filepath=self.filename,
                                          artifact_name='progress.yml',
                                          artifact_type='progress')

    return ProgressViewer