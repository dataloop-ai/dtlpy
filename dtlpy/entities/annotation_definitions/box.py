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
                 label=None, attributes=None, description=None, angle=None):
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
        :param label: annotation label
        :param attributes: a list of attributes for the annotation
        :param description:

        :return:
        """
        super().__init__(description=description, attributes=attributes)

        self.angle = angle
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.top_left = [left, top]
        self.top_right = [right, top]
        self.bottom_left = [left, bottom]
        self.bottom_right = [right, bottom]
        self.label = label

    @property
    def is_rotated(self):
        return self.angle is not None and self.angle != 0

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

    @property
    def four_points(self):
        return [self.top_left, self.bottom_left, self.bottom_right, self.top_right]

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
        image = cv2.drawContours(
            image=image,
            contours=[np.round(self.four_points).astype(int)],
            contourIdx=-1,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA
        )
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):

        pts = [{"x": float(x), "y": float(y), "z": 0} for x, y in self.geo]

        if self.angle is not None and self.angle != 0:
            pts.append(self.angle)

        return pts

    @staticmethod
    def from_coordinates(coordinates):
        return np.asarray([[pt["x"], pt["y"]] for pt in coordinates[:2]])

    @classmethod
    def from_json(cls, _json):
        coordinates = _json.get("coordinates", None) if "coordinates" in _json else _json.get("data", None)
        if coordinates is None:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        geo = cls.from_coordinates(coordinates=coordinates)

        left = np.min(geo[:, 0])
        top = np.min(geo[:, 1])
        right = np.max(geo[:, 0])
        bottom = np.max(geo[:, 1])

        angel = coordinates[2] if len(coordinates) > 2 and (
                    isinstance(coordinates[2], float) or isinstance(coordinates[2], int)) else None

        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            label=_json["label"],
            attributes=_json.get("attributes", None),
            angle=angel
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
        polygons = Polygon.from_segmentation(
            mask=mask,
            label=label,
            attributes=attributes,
            max_instances=None
        )

        if not isinstance(polygons, list):
            polygons = [polygons]

        boxes = [
            cls(
                left=polygon.left,
                top=polygon.top,
                right=polygon.right,
                bottom=polygon.bottom,
                label=label,
                attributes=attributes
            ) for polygon in polygons
        ]

        return boxes
