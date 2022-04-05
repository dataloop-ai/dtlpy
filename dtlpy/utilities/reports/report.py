import os
import json
import numpy as np
import dtlpy as dl
import tempfile


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
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, remote_name)
            print(filepath)
            with open(filepath, 'w') as f:
                json.dump(self.prepare(), f)
            item = dataset.items.upload(local_path=filepath,
                                        remote_path=remote_path,
                                        remote_name=remote_name,
                                        overwrite=True)
        return item
