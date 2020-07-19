import numpy as np

from . import BaseAnnotationDefinition


class Point(BaseAnnotationDefinition):
    """
    Point annotation object
    """

    def __init__(self, x, y, label, attributes=None):
        self.type = "point"
        self.y = y
        self.x = x
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def geo(self):
        return [self.x, self.y]

    @property
    def left(self):
        return self.y

    @property
    def top(self):
        return self.x

    @property
    def right(self):
        return self.y

    @property
    def bottom(self):
        return self.x

    @property
    def z(self):
        return 0

    def show(self, image, thickness, with_text, height, width, annotation_format, color):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: options: dl.ViewAnnotationOptions.list()
        :param color: color
        :return: ndarray
        """
        try:
            import cv2
        except ImportError:
            self.logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        # point cant have thickness 1
        if thickness is None or thickness == -1:
            thickness = 5

        # draw annotation
        image = cv2.circle(
            img=image,
            center=(int(np.round(self.x)), int(np.round(self.y))),
            radius=thickness,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):
        return {"x": float(self.x), "y": float(self.y), "z": float(self.z)}

    @staticmethod
    def from_coordinates(coordinates):
        return coordinates["x"], coordinates["y"]

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            x, y = cls.from_coordinates(_json["coordinates"])
        elif "data" in _json:
            x, y = cls.from_coordinates(_json["data"])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        attributes = _json.get("attributes", list())

        return cls(
            x=x,
            y=y,
            label=_json["label"],
            attributes=attributes,
        )
