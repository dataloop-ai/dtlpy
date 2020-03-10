import numpy as np

from . import BaseAnnotationDefinition


class Polygon(BaseAnnotationDefinition):
    """
    Polygon annotation object
    """

    def __init__(self, geo, label, is_open=True, attributes=None):
        self.type = "segment"
        self.geo = geo
        self.label = label
        self.is_open = is_open
        if attributes is None:
            attributes = list()
        self.attributes = attributes

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
        try:
            import cv2
        except ImportError:
            self.logger.error(
                'Import Error! Cant import cv2. Annotations operations will be limited. import manually and fix errors')
            raise

        if thickness is None:
            thickness = 2
        elif thickness == -1 and self.is_open:
            thickness = 2
            self.logger.warning('Cannot fill out open polygon, setting default thickness to 2')
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
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    @classmethod
    def from_segmentation(cls, mask, label, attributes=None, epsilon=None):
        try:
            import cv2
        except ImportError:
            raise ModuleNotFoundError('opencv not found. Must install to perform this function')

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
