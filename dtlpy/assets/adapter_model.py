import json
import os
import sys

sys.path.append(os.path.dirname(__file__))

try:
    import dtlpy as dl
except ImportError:
    print('Dataloop SDK not found, you can only work locally. "pip install dtlpy" to install')


class AdapterModel:
    def __init__(self, model_entity=None, model_name=None):
        self._model_name = model_name
        self._model_entity = model_entity

    ##############
    # attributes #
    ##############
    @property
    def model_entity(self):
        return self._model_entity

    @model_entity.setter
    def model_entity(self, model_entity):
        self._model_entity = model_entity
    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_entity(self, model_entity):
        self._model_entity = model_entity

    ####################
    # Dataloop methods #
    ####################
    def load_from_snapshot(self, local_path, snapshot_id):
        checkpoint = self.model_entity.snapshots.get(snapshot_id=snapshot_id)
        checkpoint.download(local_path=local_path)
        self.load(local_path)

    def save_to_snapshot(self, local_path, snapshot_name, description=''):
        self.save(local_path=local_path)
        snapshot = self.model_entity.snapshots.create(snapshot_name=snapshot_name,
                                                      description=description)
        snapshot.upload(local_path=local_path)

    def get_snapshot(self):
        pass

    def get_metrics(self):
        pass

    #################
    # model methods #
    #################
    def preprocess(self, batch):
        return batch

    def load(self, local_path):
        raise NotImplementedError

    def save(self, local_path):
        raise NotImplementedError

    def predict_items(self):
        raise NotImplementedError

    def train(self, images_path, jsons_path, dump_path):
        raise NotImplementedError

    def predict_batch(self, batch):
        raise NotImplementedError


class DumpHistoryCallback(keras.callbacks.Callback):
    def __init__(self, dump_file):
        super().__init__()
        self.dump_file = dump_file
        self.data = dict()

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        for name, val in logs.items():
            if name not in self.data:
                self.data[name] = {'x': list(),
                                   'y': list()}
            self.data[name]['x'].append(float(epoch))
            self.data[name]['y'].append(float(val))
        self.dump_history()

    def dump_history(self):
        _json = {
            "query": {},
            "datasetId": "",
            "xlabel": "epoch",
            "title": "training loss",
            "ylabel": "val",
            "type": "metric",
            "data": [{"name": name,
                      "x": values['x'],
                      "y": values['y']} for name, values in self.data.items()]
        }

        with open(self.dump_file, 'w') as f:
            json.dump(_json, f, indent=2)
