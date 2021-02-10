import numpy as np

from . import BaseAnnotationDefinition


class Ellipse(BaseAnnotationDefinition):
    """
        Ellipse annotation object
    """
    type = "ellipse"

    def __init__(self, x, y, rx, ry, angle, label, attributes=None, description=None):
        super().__init__(description=description)
        self.label = label
        self.angle = angle
        self.x = x
        self.y = y
        self.rx = rx
        self.ry = ry
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def geo(self):
        return np.asarray([[self.x, self.y],
                           [self.rx, self.ry],
                           [self.angle, self.rad]])

    @property
    def rad(self):
        return np.deg2rad(self.angle)

    @property
    def left(self):
        return self.x - np.sqrt(np.power(self.rx, 2) * np.power(np.cos(-self.rad), 2)
                                + np.power(self.ry, 2) * np.power(np.sin(-self.rad), 2))

    @property
    def top(self):
        return self.y - np.sqrt(np.power(self.rx, 2) * np.power(np.sin(-self.rad), 2)
                                + np.power(self.ry, 2) * np.power(np.cos(-self.rad), 2))

    @property
    def right(self):
        return self.x + np.sqrt(np.power(self.rx, 2) * np.power(np.cos(-self.rad), 2)
                                + np.power(self.ry, 2) * np.power(np.sin(-self.rad), 2))

    @property
    def bottom(self):
        return self.y + np.sqrt(np.power(self.rx, 2) * np.power(np.sin(-self.rad), 2)
                                + np.power(self.ry, 2) * np.power(np.cos(-self.rad), 2))

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
        except ImportError:
            self.logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        if thickness is None:
            thickness = 2

        # draw annotation
        image = cv2.ellipse(
            image,
            center=(int(np.round(self.x)), int(np.round(self.y))),
            axes=(int(np.round(self.rx)), int(np.round(self.ry))),
            angle=self.angle,
            startAngle=0,
            endAngle=360,
            color=color,
            thickness=thickness,
            lineType=-1,
        )
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):
        return {'angle': float(self.angle),
                'center': {'x': float(self.x),
                           'y': float(self.y),
                           'z': 0},
                'rx': float(self.rx),
                'ry': float(self.ry)}

    @staticmethod
    def from_coordinates(coordinates):
        angle = coordinates["angle"]
        x = coordinates["center"]["x"]
        y = coordinates["center"]["y"]
        rx = coordinates["rx"]
        ry = coordinates["ry"]
        return x, y, rx, ry, angle

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            x, y, rx, ry, angle = cls.from_coordinates(_json["coordinates"])
        elif "data" in _json:
            x, y, rx, ry, angle = cls.from_coordinates(_json["data"])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        attributes = _json.get("attributes", list())
        return cls(
            angle=angle,
            x=x,
            y=y,
            rx=rx,
            ry=ry,
            label=_json["label"],
            attributes=attributes,
        )
