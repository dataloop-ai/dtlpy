import numpy as np

from . import BaseAnnotationDefinition
from .polygon import Polygon


class Box(BaseAnnotationDefinition):
    """
        Box annotation object
    """

    def __init__(self, left, top, right, bottom, label, attributes=None, description=None):
        super().__init__(description=description)
        self.type = "box"
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def x(self):
        return [self.left, self.right]

    @property
    def y(self):
        return [self.top, self.bottom]

    @property
    def geo(self):
        return [
            [self.left, self.top],
            [self.right, self.bottom]
        ]

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
        image = cv2.rectangle(
            img=image,
            pt1=(int(np.round(self.left)), int(np.round(self.top))),
            pt2=(int(np.round(self.right)), int(np.round(self.bottom))),
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
        )
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):
        return [{"x": float(x), "y": float(y), "z": 0} for x, y in self.geo]

    @staticmethod
    def from_coordinates(coordinates):
        return np.asarray([[pt["x"], pt["y"]] for pt in coordinates])

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(_json["coordinates"])
        elif "data" in _json:
            geo = cls.from_coordinates(_json["data"])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))
        left = np.min(geo[:, 0])
        top = np.min(geo[:, 1])
        right = np.max(geo[:, 0])
        bottom = np.max(geo[:, 1])

        attributes = _json.get("attributes", list())

        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            label=_json["label"],
            attributes=attributes,
        )

    @classmethod
    def from_segmentation(cls, mask, label, attributes=None):
        """
        Convert binary mask to Polygon
        :param mask: binary mask (0,1)
        :param label: annotation label
        :param attributes: annotations list of attributes
        :return: Box annotations list  to each separated  segmentation
        """
        polygons = Polygon.from_segmentation(mask=mask, label=label, attributes=attributes,
                                             max_instances=None, is_open=False)

        if not isinstance(polygons, list):
            polygons = [polygons]

        boxes = [cls(left=polygon.left,
                     top=polygon.top,
                     right=polygon.right,
                     bottom=polygon.bottom,
                     label=label,
                     attributes=attributes) for polygon in polygons]

        return boxes
