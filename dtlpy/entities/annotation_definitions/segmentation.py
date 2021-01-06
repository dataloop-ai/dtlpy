import numpy as np
import base64
import io
from PIL import Image

from . import BaseAnnotationDefinition

from .box import Box
from .polygon import Polygon


class Segmentation(BaseAnnotationDefinition):
    """
    Segmentation annotation object
    """

    def __init__(self, geo, label, attributes=None, description=None):
        super().__init__(description=description)
        self.type = "binary"
        self.geo = geo
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def x(self):
        return

    @property
    def y(self):
        return

    @property
    def pts(self):
        return np.where(self.geo > 0)

    @property
    def left(self):
        left = 0
        if len(self.pts[1]) > 0:
            left = np.min(self.pts[1])
        return left

    @property
    def top(self):
        top = 0
        if len(self.pts[0]) > 0:
            top = np.min(self.pts[0])
        return top

    @property
    def right(self):
        right = 0
        if len(self.pts[1]) > 0:
            right = np.max(self.pts[1])
        return right

    @property
    def bottom(self):
        bottom = 0
        if len(self.pts[0]) > 0:
            bottom = np.max(self.pts[0])
        return bottom

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
        image[np.where(self.geo)] = color
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color=None):
        if color is None:
            color = (255, 255, 255)
        max_val = np.max(self.geo)
        if max_val > 1:
            self.geo = self.geo / max_val
        png_ann = np.stack((color[0] * self.geo,
                            color[1] * self.geo,
                            color[2] * self.geo,
                            255 * self.geo),
                           axis=2).astype(np.uint8)
        pil_img = Image.fromarray(png_ann)
        buff = io.BytesIO()
        pil_img.save(buff, format="PNG")
        new_image_string = base64.b64encode(buff.getvalue()).decode("utf-8")
        coordinates = "data:image/png;base64,%s" % new_image_string
        return coordinates

    def to_box(self):
        """

        :return: Box annotations list  to each separated  segmentation
        """
        polygons = Polygon.from_segmentation(mask=self.geo, label=self.label,
                                             attributes=self.attributes, max_instances=None, is_open=False)

        if not isinstance(polygons, list):
            polygons = [polygons]

        boxes = [Box(left=polygon.left,
                     top=polygon.top,
                     right=polygon.right,
                     bottom=polygon.bottom,
                     label=polygon.label,
                     attributes=polygon.attributes) for polygon in polygons]

        return boxes

    @classmethod
    def from_polygon(cls, geo, label, shape, is_open=False, attributes=None):
        """

        :param is_open:
        :param geo: list of x,y coordinates of the polygon ([[x,y],[x,y]...]
        :param label: annotation's label
        :param shape: image shape (h,w)
        :param attributes:
        :return:
        """
        try:
            import cv2
        except ImportError:
            raise ImportError('opencv not found. Must install to perform this function')

        thickness = 1 if is_open else -1

        # plot polygon on a blank mask with thickness -1 to fill the polyline
        mask = np.zeros(shape=shape, dtype=np.uint8)
        mask = cv2.drawContours(image=mask,
                                contours=[np.asarray(geo).astype('int')],
                                contourIdx=-1,
                                color=1,
                                thickness=thickness)

        return cls(
            geo=mask,
            label=label,
            attributes=attributes,
        )

    @staticmethod
    def from_coordinates(coordinates):
        if isinstance(coordinates, dict):
            data = coordinates["data"][22:]
        elif isinstance(coordinates, str):
            data = coordinates[22:]
        else:
            raise TypeError('unknown binary data type')
        decode = base64.b64decode(data)
        return np.array(Image.open(io.BytesIO(decode)))

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            mask = cls.from_coordinates(_json["coordinates"])
        elif "data" in _json:
            mask = cls.from_coordinates(_json["data"])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))
        attributes = _json.get("attributes", list())
        return cls(
            geo=(mask[:, :, 3] > 127).astype(float),
            label=_json["label"],
            attributes=attributes,
        )
