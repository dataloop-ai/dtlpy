import numpy as np

from . import BaseAnnotationDefinition


class Polyline(BaseAnnotationDefinition):
    """
    Polyline annotation object
    """

    def __init__(self, geo, label, attributes=None, description=None):
        super().__init__(description=description)
        self.type = "polyline"
        self.geo = geo
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def x(self):
        return self.geo[:, 0]

    @property
    def y(self):
        return self.geo[:, 1]

    @property
    def left(self):
        return np.min(self.x)

    @property
    def top(self):
        return np.min(self.y)

    @property
    def right(self):
        return np.max(self.x)

    @property
    def bottom(self):
        return np.max(self.y)

    def to_coordinates(self, color):
        return [{"x": float(x), "y": float(y)} for x, y in self.geo]

    @staticmethod
    def from_coordinates(coordinates):
        return np.asarray([[pt["x"], pt["y"]] for pt in coordinates])

    def show(self, image, thickness, with_text, height, width, annotation_format, color):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: options: list(dl.ViewAnnotationOptions)
        :param color: color
        :return: ndarray
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            self.logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        # polyline cant have thickness -1
        if thickness is None or thickness == -1:
            thickness = 2

        # draw annotation
        image = cv2.polylines(
            img=image,
            pts=[np.round(self.geo).astype(int)],
            color=color,
            isClosed=False,
            thickness=thickness,
        )
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(coordinates=_json["coordinates"])
        elif "data" in _json:
            geo = cls.from_coordinates(coordinates=_json["data"])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))
        attributes = _json.get("attributes", list())
        return cls(
            geo=geo,
            label=_json["label"],
            attributes=attributes,
        )
