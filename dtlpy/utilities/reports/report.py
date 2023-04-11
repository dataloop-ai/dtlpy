import os
import json
import numpy as np
import dtlpy as dl
import tempfile
import io
import requests
from figures import *


class Report:
    def __init__(self, nrows: int = 1, ncols: int = 1):
        """
        Create a report layout with defined size
        :param int nrows: number of rows in the report json
        :param int ncols: number of columns in the report json
        """
        self.figs = np.empty(shape=(nrows, ncols), dtype=object)
        self._ncols = ncols
        self._nrows = nrows
        self._irow = 0
        self._icol = 0

    def add(self, fig, irow: int, icol: int):
        """
        Add fig to to an index location in the layout

        :param fig: input figure.
        :param int irow: row location of the added fig. should be within the layout boundaries defined in the Report init
        :param int icol: column location of the added fig. should be within the layout boundaries defined in the Report init
        :return:
        """
        if 0 > irow or irow >= self._nrows:
            raise ValueError(
                'Trying to set irow with value outside layout definition. layout rows: {}'.format(self._nrows))
        if 0 > icol or icol >= self._ncols:
            raise ValueError(
                'Trying to set icol with value outside layout definition. layout cols: {}'.format(self._ncols))
        self.figs[irow, icol] = fig.to_dict()

    def prepare(self):
        """
        Covert the layout into the json item for uploading

        :return:
        """
        return {
            "shebang": "dataloop",
            "metadata": {"dltype": "report"},
            "layout": {
                "rows": [{"cols": [fig for fig in row if fig is not None]} for row in self.figs]
                # "rows": [{"cols": [report_json]}]
            }
        }

    def upload(self, dataset: dl.Dataset, remote_name: str, remote_path: str):
        """
        Upload the report item to the platform

        :param dataset: dl.Dataset to upload the item to
        :param remote_name: name of the report. should be with .json extension
        :param remote_path: remote directory to upload the item to
        :return:
        """
        if '.' not in remote_name:
            remote_name += '.json'
        else:
            extension = remote_name.split('.')[-1]
            if extension.lower() != 'json':
                raise Exception('remote file should be a JSON file. Please provide ".json" in remote name suffix')

        if remote_path[0] == '/':
            remote_path = remote_path[1:]

        if remote_path[-1] == '/':
            remote_path = remote_path[:-1]

        filepath = f'/{remote_path}/{remote_name}'
        report_dataset = dl.datasets.get(dataset_id=dataset.id)

        try:
            report_item = report_dataset.items.get(filepath=filepath)
        except dl.exceptions.NotFound:
            with tempfile.TemporaryDirectory() as tmpdir:
                filepath = os.path.join(tmpdir, remote_name)
                with open(filepath, 'w') as f:
                    json.dump(self.prepare(), f)
                item = dataset.items.upload(local_path=filepath,
                                            remote_path=remote_path,
                                            remote_name=remote_name,
                                            overwrite=True)
            return item

        binary = io.BytesIO()
        binary.write(json.dumps(self.prepare()).encode())
        binary.name = report_item.name
        headers_req = dl.client_api.auth
        binary.seek(0)
        resp = requests.post(url=dl.environment() + '/items/{}/revisions'.format(report_item.id),
                             headers=headers_req,
                             files={'file': (binary.name, binary)},
                             )
        if not resp.ok:
            raise ValueError(resp.text)
        return report_item
