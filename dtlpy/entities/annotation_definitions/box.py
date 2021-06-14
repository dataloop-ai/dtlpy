import numpy as np

from . import BaseAnnotationDefinition
from .polygon import Polygon


class Box(BaseAnnotationDefinition):
    """
        Box annotation object
                Can create a box using 2 point using:
         "top", "left", "bottom", "right" (to form a box [(left, top), (right, bottom)])
        To create a rotated box need to input all 4 points using:
         "top_left", "bottom_left", "bottom_right", "top_right" (each variable is in the form of [x,y])
    """
    type = "box"

    def __init__(self,
                 left=None, top=None, right=None, bottom=None,
                 top_left=None, bottom_left=None, bottom_right=None, top_right=None,
                 label=None, attributes=None, description=None):
        """
        Can create a box using 2 point using:
         "top", "left", "bottom", "right" (to form a box [(left, top), (right, bottom)])
        To create a rotated box need to input all 4 points using:
         "top_left", "bottom_left", "bottom_right", "top_right" (each variable is in the form of [x,y])
         Must input all 4 variable of each option

        :param left: left x coordinate of the box
        :param top: top Y coordinate of the box
        :param right: right x coordinate of the box
        :param bottom: bottom Y coordinate of the box
        :param top_left: top_left point of a box [x,y]
        :param bottom_left: bottom_left point of a box [x,y]
        :param bottom_right: bottom_right point of a box [x,y]
        :param top_right: top_right point of a box [x,y]
        :param label: annotation label
        :param attributes: a list of attributes for the annotation
        :param description:

        :return:
        """
        super().__init__(description=description)

        if all(pt is not None for pt in [left, top, right, bottom]):
            self.is_rotated = False
        elif all(pt is not None for pt in [top_left, bottom_left, bottom_right, top_right]):
            self.is_rotated = True
        else:
            raise ValueError('Must input all 4 variables of each option, box or a rotated box')

        if self.is_rotated:
            self.left = np.minimum(top_left[0], bottom_left[0])
            self.top = np.minimum(top_left[1], top_right[1])
            self.right = np.maximum(top_right[0], bottom_right[0])
            self.bottom = np.maximum(bottom_right[1], bottom_left[1])
            self.top_left = top_left
            self.top_right = top_right
            self.bottom_left = bottom_left
            self.bottom_right = bottom_right
        else:
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.top_left = [left, top]
            self.top_right = [right, top]
            self.bottom_left = [left, bottom]
            self.bottom_right = [right, bottom]
        self.angle = np.arctan2(self.top_right[1] - self.top_left[1], self.top_right[0] - self.top_left[0])
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def x(self):
        if self.is_rotated:
            x = [self.top_left[0], self.top_right[0], self.bottom_left[0], self.bottom_right[0]]
        else:
            x = [self.left, self.right]
        return x

    @property
    def y(self):
        if self.is_rotated:
            y = [self.top_left[1], self.top_right[1], self.bottom_left[1], self.bottom_right[1]]
        else:
            y = [self.top, self.bottom]
        return y

    @property
    def geo(self):
        if self.is_rotated:
            pts = [self.top_left, self.bottom_left, self.bottom_right, self.top_right]
        else:
            pts = [
                [self.left, self.top],
                [self.right, self.bottom]
            ]
        return pts

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

        if thickness is None:
            thickness = 2

        # draw annotation
        pts = [self.top_left, self.bottom_left, self.bottom_right, self.top_right]
        image = cv2.drawContours(
            image=image,
            contours=[np.round(pts).astype(int)],
            contourIdx=-1,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA
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

        top_left = None
        bottom_left = None
        bottom_right = None
        top_right = None
        left = None
        top = None
        right = None
        bottom = None
        if len(geo) == 4:
            top_left = geo[0]
            bottom_left = geo[1]
            bottom_right = geo[2]
            top_right = geo[3]
        else:
            left = np.min(geo[:, 0])
            top = np.min(geo[:, 1])
            right = np.max(geo[:, 0])
            bottom = np.max(geo[:, 1])
        attributes = _json.get("attributes", list())

        return cls(
            top_left=top_left,
            bottom_left=bottom_left,
            bottom_right=bottom_right,
            top_right=top_right,
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
