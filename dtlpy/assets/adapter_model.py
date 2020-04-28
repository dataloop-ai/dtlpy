try:
    import dtlpy as dl
except ImportError:
    print('Dataloop SDK not found, you can only work locally. "pip install dtlpy" to install')


class AdapterModel:
    def __init__(self, device, model_specs, hp_values, final):
        self.model_name = ''
        self.model = None

    def reformat(self):
        pass

    def data_loader(self):
        pass

    def preprocess(self, batch):
        return batch

    def load(self, local_path):
        raise NotImplementedError

    def load_from_checkpoint(self, local_path, checkpoint_id):
        checkpoint = dl.checkpoints.get(checkpoint_id=checkpoint_id)
        checkpoint.download(local_path=local_path)
        self.load(local_path)

    def save(self, local_path):
        self.model.save(local_path)

    def save_to_checkpoint(self, local_path):
        self.save(local_path=local_path)
        dl.checkpoints.upload()

    def train(self):
        pass

    def get_checkpoint(self):
        pass

    def get_metrics(self):
        pass

    def predict_items(self, items, with_upload=True):
        for item in items:
            filepath = item.download()
            results = self.predict(filepath)
            if with_upload:
                builder = item.annotation.builder()
                for res in results:
                    builder.add(dl.Segmaeations())
                item.annotations.upload(results)

    def predict(self, batch):
        raise NotImplementedError
