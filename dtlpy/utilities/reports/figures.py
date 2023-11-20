from typing import Optional, Union
import pandas as pd
import numpy as np

NUMBER_TYPES = (int, float, complex)


class FigOptions:
    def __init__(self, rows_per_page: int = None, comments: dict = None, x_title: str = None, y_title: str = None,
                 colors: list = None, direction: str = None):
        self.rows_per_page = rows_per_page
        self.comments = comments
        self.x_title = x_title
        self.y_title = y_title
        self.colors = colors
        self.direction = direction

        self._validate()

    def _validate(self):
        # Mapping attribute names to their expected types
        expected_types = {
            'rows_per_page': int,
            'comments': dict,
            'x_title': str,
            'y_title': str,
            'colors': list,
            'direction': str
        }

        for attr, expected_type in expected_types.items():
            value = getattr(self, attr)
            if value is not None and not isinstance(value, expected_type):
                raise ValueError(
                    f"{attr} must be of type {expected_type.__name__}")

    def to_dict(self):
        return {
            "comments": self.comments,
            "rowsPerPage": self.rows_per_page,
            "xTitle": self.x_title,
            "yTitle": self.y_title,
            "colors": self.colors,
            "direction": self.direction,
        }


class Base:
    def __init__(self,
                 title: str,
                 type: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        self.title = title
        self.type = type
        self.title_href = title_href
        self.plot_id = plot_id
        self.labels = labels
        self.data = data
        self.options = options if options is not None and options != {} else FigOptions()

        self._validate()

    def _validate(self):
        if not isinstance(self.title, str):
            raise ValueError("title must be a string")

        if self.title_href is not None and not isinstance(self.title_href, str):
            raise ValueError("title_href must be a string or None")

        if self.plot_id is not None and not isinstance(self.plot_id, str):
            raise ValueError("plot_id must be a string or None")

        if not isinstance(self.labels, list):
            raise ValueError("labels must be a list")

        if not isinstance(self.data, (list, np.ndarray)):
            raise ValueError("data must be a list or a numpy ndarray")

        if not isinstance(self.options, FigOptions):
            raise ValueError("options must be an instance of FigOptions")

        if not isinstance(self.type, str):
            raise ValueError("type must be a string")

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
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type="table",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)
        self._validate_table_data()

    def _validate_table_data(self):
        data, labels = self.data, self.labels
        n_cols = len(labels)

        if not isinstance(data, list):
            raise ValueError(
                'arg "data" must be a list of lists. got a {!r}'.format(type(data)))

        for i_d, d in enumerate(data):
            if not isinstance(d, list):
                raise ValueError(
                    '"data" must be a list of lists. got type {!r} at index {}'.format(type(d), i_d))
            if len(d) != n_cols:
                raise ValueError(
                    '"data" rows must be the same size as "labels": {}. got size {} at index {}'.format(n_cols, len(d),
                                                                                                        i_d))

    @classmethod
    def from_df(cls, df: pd.DataFrame, **kwargs):
        labels = df.columns.to_list()
        data = df.values.tolist()
        return cls(labels=labels, data=data, **kwargs)


class Line(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type="line",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)


class Scatter(Base):
    def __init__(self,
                 title: str,
                 data: Union[list, np.ndarray],
                 labels: list = None,
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        if labels is None:
            labels = list()
        super().__init__(title=title,
                         type='scatter',
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)


class Bar(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type="bar",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)


class Doughnut(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type="doughnut",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)


class Pie(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type='pie',
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)
        self._validate_pie_data()

    def _validate_pie_data(self):
        data, labels = self.data, self.labels
        if not isinstance(data, list):
            raise ValueError(
                'arg "data" must be a list. got a {!r}'.format(type(data)))

        if len(data) != len(labels):
            raise ValueError('"data" must be the same size as "labels". got size {} and {}'.format(len(data),
                                                                                                   len(labels)))
        for i_d, d in enumerate(data):
            if not isinstance(d, NUMBER_TYPES):
                raise ValueError(
                    'all "data" fields must be number. got type {!r} at index {}'.format(type(d), i_d))


class Hbar(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None):
        super().__init__(title=title,
                         type="hbar",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)


class ConfusionMatrix(Base):
    def __init__(self,
                 title: str,
                 labels: list,
                 data: Union[list, np.ndarray],
                 title_href: Optional[str] = None,
                 plot_id: Optional[str] = None,
                 options: Optional[FigOptions] = None,
                 href_map: Optional[list] = None,
                 color_map: Optional[np.ndarray] = None):
        self.xlabel = 'Predicted'
        self.ylabel = 'Actual'
        self.color_map = color_map
        self.href_map = href_map
        super().__init__(title=title,
                         type="table",
                         labels=labels,
                         data=data,
                         title_href=title_href,
                         plot_id=plot_id,
                         options=options)
        self._validate_confusion_matrix_data()

    def _validate_confusion_matrix_data(self):
        if self.color_map is not None and not isinstance(self.color_map, np.ndarray):
            raise ValueError('arg "color_map" must be a numpy ndarray. got a {!r}'.format(
                type(self.color_map)))
        if self.href_map is not None and not isinstance(self.href_map, list):
            raise ValueError(
                'arg "href_map" must be a list. got a {!r}'.format(type(self.href_map)))

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
                color = self._rbgtohex(
                    *self.color_map[i_row, i_col, :3]) if self.color_map is not None else None
                href = self.href_map[i_row][i_col] if self.href_map is not None else None
                data[i_row][i_col] = {
                    'text': '{:.2f}'.format(val),
                    'href': href,
                    'color': color}
            row.insert(0, labels[i_row])
        labels.insert(0, f'{self.ylabel}//{self.xlabel}')
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
