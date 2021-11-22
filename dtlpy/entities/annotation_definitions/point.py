import numpy as np

from . import BaseAnnotationDefinition


class Point(BaseAnnotationDefinition):
    """
    Point annotation object
    """
    type = "point"

    def __init__(self, x, y, label, attributes=None, description=None):
        super().__init__(description=description, attributes=attributes)
        self.y = y
        self.x = x
        self.label = label

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

        # point cant have thickness 1
        if thickness is None or thickness == -1:
            thickness = 5

        # create image to draw on
        if alpha != 1:
            overlay = image.copy()
        else:
            overlay = image

        # draw annotation
        overlay = cv2.circle(
            img=overlay,
            center=(int(np.round(self.x)), int(np.round(self.y))),
            radius=thickness,
            color=color,
            thickness=thickness,
            lineType=cv2.LINE_AA,
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

        return cls(
            x=x,
            y=y,
            label=_json["label"],
            attributes=_json.get("attributes", None),
        )
