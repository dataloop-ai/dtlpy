import numpy as np

from . import BaseAnnotationDefinition


class Polyline(BaseAnnotationDefinition):
    """
    Polyline annotation object
    """

    def __init__(self, geo, label, attributes=None, description=None):
        super().__init__(description=description, attributes=attributes)
        self.type = "polyline"
        self.geo = geo
        self.label = label

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
        return [[{"x": float(x), "y": float(y)} for x, y in self.geo]]

    @staticmethod
    def from_coordinates(coordinates):
        return np.asarray([[pt["x"], pt["y"]] for pt in coordinates])

    def show(self, image, thickness, with_text, height, width, annotation_format, color, alpha=1):
        """
        Show annotation as ndarray
        :param image: empty or image to draw on
        :param thickness:
        :param with_text: not required
        :param height: item height
        :param width: item width
        :param annotation_format: options: list(dl.ViewAnnotationOptions)
        :param color: color
        :param alpha: opacity value [0 1], default 1
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

        if alpha != 1:
            overlay = image.copy()
        else:
            overlay = image

        overlay = cv2.polylines(
            img=overlay,
            pts=[np.round(self.geo).astype(int)],
            color=color,
            isClosed=False,
            thickness=thickness,
        )

        if not isinstance(color, int) and len(color) == 4 and color[3] != 255:
            # add with opacity
            image = cv2.addWeighted(src1=overlay,
                                    alpha=alpha,
                                    src2=image,
                                    beta=1 - alpha,
                                    gamma=0)
        else:
            image = overlay

        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(coordinates=_json["coordinates"][0])
        elif "data" in _json:
            geo = cls.from_coordinates(coordinates=_json["data"][0])
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))
        return cls(
            geo=geo,
            label=_json["label"],
            attributes=_json.get("attributes", None),
        )
