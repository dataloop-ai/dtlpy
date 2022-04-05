from pydantic import BaseModel, Field, root_validator, Extra
from typing import Optional, Union
import pandas as pd
import numpy as np

NUMBER_TYPES = (int, float, complex)


class FigOptions(BaseModel):
    rows_per_page: Optional[int]
    comments: Optional[dict]
    x_title: Optional[str]
    y_title: Optional[str]
    colors: Optional[list]
    direction: Optional[str]

    def to_dict(self):
        return {
            "comments": self.comments,
            "rowsPerPage": self.rows_per_page,
            "xTitle": self.x_title,
            "yTitle": self.y_title,
            "colors": self.colors,
            "direction": self.direction,
        }


class Base(BaseModel):
    title: str
    title_href: Optional[str]
    plot_id: Optional[str]
    type: str
    labels: list
    data: Union[list, np.ndarray]
    options: FigOptions = Field(default=FigOptions())

    class Config:
        arbitrary_types_allowed = True
        extra = Extra.forbid

    def to_dict(self):
        options = self.options.to_dict()
        if isinstance(self, ConfusionMatrix):
            options["confusion"] = True

        data = self.data
        if isinstance(data, np.ndarray):
            data = data.tolist()

        return {
            "type": self.type,
            "title": self.title,
            "href": self.title_href,
            "labels": self.labels,
            "id": self.plot_id,
            "data": data,
            "options": options
        }


class Table(Base):
    type = 'table'

    @root_validator
    def check_data(cls, values):
        data, labels = values.get('data'), values.get('labels')
        n_cols = len(labels)

        if not isinstance(data, list):
            raise ValueError('arg "data" must be a list of lists. got a {!r}'.format(type(data)))

        for i_d, d in enumerate(data):
            if not isinstance(d, list):
                raise ValueError('"data" must be a list of lists. got type {!r} at index {}'.format(type(d), i_d))
            if len(d) != n_cols:
                raise ValueError(
                    '"data" rows must be the same size as "labels": {}. got size {} at index {}'.format(n_cols, len(d),
                                                                                                        i_d))
        return values

    @classmethod
    def from_df(cls, df: pd.DataFrame, **kwargs):
        labels = df.columns
        data = df.values.tolist()
        return cls(labels=labels, data=data, **kwargs)


class Line(Base):
    type = 'line'


class Scatter(Base):
    type = 'scatter'
    labels = list()


class Bar(Base):
    type = 'bar'


class Doughnut(Base):
    type = 'doughnut'


class Pie(Base):
    type = 'pie'

    @root_validator
    def check_data(cls, values):
        data, labels = values.get('data'), values.get('labels')
        if not isinstance(data, list):
            raise ValueError('arg "data" must be a list. got a {!r}'.format(type(data)))

        if len(data) != len(labels):
            raise ValueError('"data" must be the same size as "labels". got size {} and {}'.format(len(data),
                                                                                                   len(labels)))
        for i_d, d in enumerate(data):
            if not isinstance(d, NUMBER_TYPES):
                raise ValueError('all "data" fields must be number. got type {!r} at index {}'.format(type(d), i_d))
        return values


class Hbar(Base):
    type = 'hbar'


class ConfusionMatrix(Base):
    type = 'table'
    href_map: Optional[list]
    color_map: Optional[np.ndarray]

    @staticmethod
    def _rbgtohex(r, g, b):
        return "#{0:02x}{1:02x}{2:02x}".format(int(255 * r), int(255 * g), int(255 * b))

    def to_dict(self):
        options = self.options.to_dict()
        options["confusion"] = True
        data = self.data.copy()
        if isinstance(data, np.ndarray):
            data = data.tolist()
        labels = self.labels.copy()
        for i_row, row in enumerate(data):
            for i_col, val in enumerate(row):
                color = self._rbgtohex(*self.color_map[i_row, i_col, :3]) if self.color_map is not None else None
                href = self.href_map[i_row][i_col] if self.href_map is not None else None
                data[i_row][i_col] = {
                    'text': '{:.2f}'.format(val),
                    'href': href,
                    'color': color}
            row.insert(0, labels[i_row])
        labels.insert(0, 'DET//GT')
        return {
            "type": self.type,
            "title": self.title,
            "href": self.title_href,
            "labels": labels,
            "data": data,
            "options": options
        }
    # def from_df(self, df: pd.DataFrame, **kwargs):
    #     data = []
    #     for i_label, g_label in enumerate(labels):
    #         line = list()
    #         line.append(g_label)
    #         for r_label in labels:
    #             if g_label == r_label:
    #                 p = high_prob()
    #             else:
    #                 p = low_prob()
    #             line.append({'text': str(p),
    #                          'href': "https://rc-con.dataloop.ai/projects/2cb9ae90-b6e8-4d15-9016-17bacc9b7bdf/datasets/607ed8107370454e4dd3b4c7/items?view=icons&dqlFilter=%7B%22filter%22%3A+%7B%22%24and%22%3A+%5B%7B%22hidden%22%3A+false%7D%2C+%7B%22type%22%3A+%22file%22%7D%2C+%7B%22dir%22%3A+%22booking%22%7D%5D%7D%2C+%22page%22%3A+0%2C+%22pageSize%22%3A+1000%2C+%22resource%22%3A+%22items%22%2C+%22join%22%3A+%7B%22on%22%3A+%7B%22resource%22%3A+%22annotations%22%2C+%22local%22%3A+%22itemId%22%2C+%22forigen%22%3A+%22id%22%7D%2C+%22filter%22%3A+%7B%22%24and%22%3A+%5B%7B%22label%22%3A+%22immigration%22%7D%5D%7D%7D%7D",
    #                          'color': rbgtohex(*colors(p)[:3])})
    #         data.append(line)
