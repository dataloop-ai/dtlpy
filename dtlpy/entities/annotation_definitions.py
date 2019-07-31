import cv2
import base64
import logging
import io
from PIL import Image
import attr
import numpy as np

logger = logging.getLogger("dataloop.annotations.objects")


@attr.s
class Classification:
    """
        Classification annotation object
    """

    type = "class"
    label = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def geo(self):
        return list()

    @property
    def left(self):
        return 0

    @property
    def top(self):
        return 0

    @property
    def right(self):
        return 0

    @property
    def bottom(self):
        return 0

    def show(self, image, thickness, with_text, height, width, annotation_format, color):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
        if with_text:
            image = add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self):
        return list()

    @classmethod
    def from_json(cls, _json):
        attributes = _json.get("attributes", list())
        return cls(
            label=_json["label"],
            attributes=attributes,
        )


@attr.s
class Point:
    """
    Point annotation object
    """

    type = "point"
    y = attr.ib()
    x = attr.ib()
    label = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

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
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
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
            image = add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self):
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
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )

        attributes = _json.get("attributes", list())

        return cls(
            x=x,
            y=y,
            label=_json["label"],
            attributes=attributes,
        )


@attr.s
class Ellipse:
    """
        Ellipse annotation object
    """

    type = "ellipse"
    label = attr.ib()
    angle = attr.ib()
    x = attr.ib()
    y = attr.ib()
    rx = attr.ib()
    ry = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

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
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
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
            image = add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self):
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
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )

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


@attr.s
class Box:
    """
        Box annotation object
    """

    type = "box"
    left = attr.ib()
    top = attr.ib()
    right = attr.ib()
    bottom = attr.ib()
    label = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

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
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
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
            image = add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self):
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
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )
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


@attr.s
class Polyline:
    """
    Polyline annotation object
    """

    type = "polyline"
    is_open = True
    geo = attr.ib()
    label = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

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

    def to_coordinates(self):
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
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
        # poloyline cant have thickness -1
        if thickness is None or thickness == -1:
            thickness = 1

        # draw annotation
        image = cv2.polylines(
            img=image,
            pts=[np.round(self.geo).astype(int)],
            color=color,
            isClosed=False,
            thickness=thickness,
        )
        if with_text:
            image = add_text_to_image(image=image, annotation=self)
        return image

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(coordinates=_json["coordinates"])
        elif "data" in _json:
            geo = cls.from_coordinates(coordinates=_json["data"])
        else:
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )
        attributes = _json.get("attributes", list())
        return cls(
            geo=geo,
            label=_json["label"],
            attributes=attributes,
        )


@attr.s
class Polygon:
    """
    Polygon annotation object
    """

    type = "segment"
    geo = attr.ib()
    label = attr.ib()
    attributes = attr.ib()
    is_open = attr.ib(default=False)

    @attributes.default
    def set_attributes(self):
        return list()

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

    def to_coordinates(self):
        return [[{"x": float(x), "y": float(y)} for x, y in self.geo]]

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
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
        if thickness is None:
            thickness = 2
        elif thickness == -1 and self.is_open:
            thickness = 2
            logger.warning('Cannot fill out open polygon, setting default thickness to 2')
        # draw annotation
        if self.is_open:
            image = cv2.polylines(
                img=image,
                pts=[np.round(self.geo).astype(int)],
                color=color,
                isClosed=False,
                thickness=thickness,
            )
        else:
            image = cv2.drawContours(
                image=image,
                contours=[np.round(self.geo).astype(int)],
                contourIdx=-1,
                color=color,
                thickness=thickness,
            )
        if with_text:
            image = add_text_to_image(image=image, annotation=self)
        return image

    @classmethod
    def from_segmentation(cls, mask, label, attributes=None, epsilon=None):
        # mask float
        mask = 1. * mask
        # normalize to 1
        mask /= np.max(mask)
        # threshold the mask
        ret, thresh = cv2.threshold(mask, 0.5, 255, 0)
        # find contours
        im2, contours, hierarchy = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_TREE,
                                                    cv2.CHAIN_APPROX_NONE)
        if len(contours) == 0:
            # no contours were found
            new_pts = []
        else:
            # calculate contours area
            areas = [cv2.contourArea(cnt) for cnt in contours]
            # take onr contour with maximum area
            filtered_indices = np.asarray(areas).argsort()[::-1][:1]
            filtered_contours = [contours[filtered_indices[i_cnt]] for i_cnt, b_cnt in
                                 enumerate(filtered_indices)]
            # estimate contour to reduce number of points
            if epsilon is None:
                epsilon = 0.0005 * cv2.arcLength(filtered_contours[0], True)
            new_pts = np.squeeze(cv2.approxPolyDP(filtered_contours[0], epsilon, True))

        return cls(
            geo=new_pts,
            label=label,
            attributes=attributes,
            is_open=False
        )

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(coordinates=_json["coordinates"][0])
        elif "data" in _json:
            geo = cls.from_coordinates(coordinates=_json["data"])
        else:
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )
        is_open = _json.get('is_open', False)
        attributes = _json.get("attributes", list())
        return cls(
            geo=geo,
            label=_json["label"],
            attributes=attributes,
            is_open=is_open
        )


@attr.s
class Segmentation:
    """
        Segmentation annotation object
    """

    type = "binary"
    geo = attr.ib()
    label = attr.ib()
    attributes = attr.ib()

    @attributes.default
    def set_attributes(self):
        return list()

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
        if len(self.pts[0]) > 0:
            left = np.min(self.pts[0])
        return left

    @property
    def top(self):
        top = 0
        if len(self.pts[1]) > 0:
            top = np.min(self.pts[1])
        return top

    @property
    def right(self):
        right = 0
        if len(self.pts[0]) > 0:
            right = np.max(self.pts[0])
        return right

    @property
    def bottom(self):
        bottom = 0
        if len(self.pts[1]) > 0:
            bottom = np.max(self.pts[1])
        return bottom

    def show(self, image, thickness, with_text, height, width, annotation_format, color):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: ['mask', 'instance']
        :param color: color
        :return: ndarray
        """
        image[np.where(self.geo)] = color
        if with_text:
            image = add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color=None):
        if color is None:
            color = (255, 255, 255)
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

    @classmethod
    def from_polygon(cls, geo, label, shape, attributes=None):
        """

        :param geo: list of x,y coordinates of the polygon ([[x,y],[x,y]...]
        :param label: annotation's label
        :param shape: image shape (h,w)
        :param attributes:
        :return:
        """
        # plot polygon on a blank mask with thickness -1 to fill the polyline
        mask = np.zeros(shape=shape)
        mask = cv2.drawContours(image=mask,
                                contours=geo,
                                contourIdx=-1,
                                color=1,
                                thickness=-1)

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
            raise ValueError(
                'can not find "coordinates" or "data" in annotation. id: %s'
                % _json["id"]
            )
        attributes = _json.get("attributes", list())
        return cls(
            geo=(mask[:, :, 3] > 127).astype(float),
            label=_json["label"],
            attributes=attributes,
        )


def add_text_to_image(image, annotation):
    text = '{label}-{attributes}'.format(label=annotation.label, attributes=','.join(annotation.attributes))
    top = annotation.top
    left = annotation.left
    if top == 0:
        top = image.shape[0] / 10
    if left == 0:
        left = image.shape[1] / 10
    return cv2.putText(img=image,
                       text=text,
                       org=tuple([int(np.round(top)), int(np.round(left))]),
                       color=(255, 0, 0),
                       fontFace=cv2.FONT_HERSHEY_DUPLEX,
                       fontScale=1,
                       thickness=2)
