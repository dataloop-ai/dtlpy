import math
import numpy as np

from . import BaseAnnotationDefinition


class Cube(BaseAnnotationDefinition):
    """
        Cube annotation object
    """
    type = "cube"

    def __init__(self, label, front_tl, front_tr, front_br, front_bl,
                 back_tl, back_tr, back_br, back_bl, angle=None,
                 attributes=None, description=None):
        super().__init__(description=description, attributes=attributes)
        self.front_bl = front_bl
        self.front_br = front_br
        self.front_tr = front_tr
        self.front_tl = front_tl
        self.back_bl = back_bl
        self.back_br = back_br
        self.back_tr = back_tr
        self.back_tl = back_tl

        self._angle = angle
        self.label = label

        self.keys = ["front_tl", "front_tr", "front_br", "front_bl",
                     "back_tl", "back_tr", "back_br", "back_bl"]

    @staticmethod
    def calculate_angle(b, c):
        a = [b[0] + 200, b[1]]
        if b in (a, c):
            return 0

        ang = math.degrees(
            math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
        return ang + 360 if ang < 0 else ang

    @property
    def angle(self):
        if self._angle is None:
            self._angle = Cube.calculate_angle(self.front_tl, self.front_tr)
        return self._angle

    @property
    def x(self):
        return self.geo[:, 0]

    @property
    def y(self):
        return self.geo[:, 1]

    @property
    def geo(self):
        return np.asarray([self.front_tl,
                           self.front_tr,
                           self.front_br,
                           self.front_bl,
                           self.back_tl,
                           self.back_tr,
                           self.back_br,
                           self.back_bl
                           ])

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

        image = cv2.polylines(image,
                              pts=[np.asarray(
                                  [self.front_bl, self.front_br, self.front_tr, self.front_tl]).round().astype(int)],
                              isClosed=True,
                              color=color,
                              thickness=thickness)
        image = cv2.polylines(image,
                              pts=[np.asarray([self.back_bl, self.back_br, self.back_tr, self.back_tl]).round().astype(
                                  int)],
                              isClosed=True,
                              color=color,
                              thickness=thickness)
        image = cv2.line(image,
                         pt1=tuple(np.asarray(self.front_bl).round().astype(int)),
                         pt2=tuple(np.asarray(self.back_bl).round().astype(int)),
                         color=color,
                         thickness=thickness)
        image = cv2.line(image,
                         pt1=tuple(np.asarray(self.front_br).round().astype(int)),
                         pt2=tuple(np.asarray(self.back_br).round().astype(int)),
                         color=color,
                         thickness=thickness)
        image = cv2.line(image,
                         pt1=tuple(np.asarray(self.front_tl).round().astype(int)),
                         pt2=tuple(np.asarray(self.back_tl).round().astype(int)),
                         color=color,
                         thickness=thickness)
        image = cv2.line(image,
                         pt1=tuple(np.asarray(self.front_tr).round().astype(int)),
                         pt2=tuple(np.asarray(self.back_tr).round().astype(int)),
                         color=color,
                         thickness=thickness)
        return image

    def to_coordinates(self, color):
        coordinates = {self.keys[idx]: {"x": float(x), "y": float(y), "z": 0}
                       for idx, [x, y] in enumerate(self.geo)}
        coordinates['angle'] = self.angle
        return coordinates

    @staticmethod
    def from_coordinates(coordinates):
        geo = list()
        for key, pt in enumerate(coordinates):
            geo.append([pt["x"], pt["y"]])
        return np.asarray(geo)

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            key = "coordinates"
        elif "data" in _json:
            key = "data"
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        return cls(
            front_bl=np.asarray([_json[key]["front_bl"]['x'], _json[key]["front_bl"]['y']]),
            front_br=np.asarray([_json[key]["front_br"]['x'], _json[key]["front_br"]['y']]),
            front_tl=np.asarray([_json[key]["front_tl"]['x'], _json[key]["front_tl"]['y']]),
            front_tr=np.asarray([_json[key]["front_tr"]['x'], _json[key]["front_tr"]['y']]),
            back_bl=np.asarray([_json[key]["back_bl"]['x'], _json[key]["back_bl"]['y']]),
            back_br=np.asarray([_json[key]["back_br"]['x'], _json[key]["back_br"]['y']]),
            back_tl=np.asarray([_json[key]["back_tl"]['x'], _json[key]["back_tl"]['y']]),
            back_tr=np.asarray([_json[key]["back_tr"]['x'], _json[key]["back_tr"]['y']]),
            label=_json["label"],
            angle=_json[key]["angle"],
            attributes=_json.get("attributes", None)
        )

    @staticmethod
    def rotate(center, point, angle):
        angle = math.radians(angle)
        cx, cy = center
        px, py = point

        qx = cx + math.cos(angle) * (px - cx) - math.sin(angle) * (py - cy)
        qy = cy + math.sin(angle) * (px - cx) + math.cos(angle) * (py - cy)
        return [qx, qy]

    @classmethod
    def from_boxes_and_angle(cls,
                             front_left, front_top, front_right, front_bottom,
                             back_left, back_top, back_right, back_bottom,
                             label, angle=0, attributes=None):
        """
        Create cuboid by given front and back boxes with angle
        the angle calculate fom the center of each box
        """
        if angle != 0:
            front_center = [front_left + (front_right - front_left) / 2, front_top + (front_bottom - front_top) / 2]
            back_center = [back_left + (back_right - back_left) / 2, back_top + (back_bottom - back_top) / 2]
            front_tl = Cube.rotate(center=front_center, point=[front_left, front_top], angle=angle)
            front_tr = Cube.rotate(center=front_center, point=[front_right, front_top], angle=angle)
            front_br = Cube.rotate(center=front_center, point=[front_right, front_bottom], angle=angle)
            front_bl = Cube.rotate(center=front_center, point=[front_left, front_bottom], angle=angle)
            back_tl = Cube.rotate(center=back_center, point=[back_left, back_top], angle=angle)
            back_tr = Cube.rotate(center=back_center, point=[back_right, back_top], angle=angle)
            back_br = Cube.rotate(center=back_center, point=[back_right, back_bottom], angle=angle)
            back_bl = Cube.rotate(center=back_center, point=[back_left, back_bottom], angle=angle)
        else:
            front_tl = [front_left, front_top]
            front_tr = [front_right, front_top]
            front_br = [front_right, front_bottom]
            front_bl = [front_left, front_bottom]
            back_tl = [back_left, back_top]
            back_tr = [back_right, back_top]
            back_br = [back_right, back_bottom]
            back_bl = [back_left, back_bottom]

        return cls(
            front_tl=front_tl, front_tr=front_tr, front_br=front_br, front_bl=front_bl,
            back_tl=back_tl, back_tr=back_tr, back_br=back_br, back_bl=back_bl,
            label=label,
            angle=angle,
            attributes=attributes
        )
