import numpy as np
import logging

from . import BaseAnnotationDefinition

logger = logging.getLogger(name=__name__)


class Polygon(BaseAnnotationDefinition):
    """
    Polygon annotation object
    """
    type = "segment"

    def __init__(self, geo, label, attributes=None, description=None):
        super().__init__(description=description)
        self.geo = geo
        self.label = label
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
    def from_segmentation(cls, mask, label, attributes=None, epsilon=None, max_instances=1, min_area=0):
        """
        Convert binary mask to Polygon
        :param mask: binary mask (0,1)
        :param label: annotation label
        :param attributes: annotations list of attributes
        :param epsilon: from opencv: specifying the approximation accuracy. This is the maximum distance
    .   between the original curve and its approximation. if 0 all points are returns
        :param max_instances: number of max instances to return. if None all wil be returned
        :param min_area: remove polygons with area lower thn this threshold (pixels)
        :return: Polygon annotation
        """
        try:
            import cv2
        except (ImportError, ModuleNotFoundError):
            raise ImportError('opencv not found. Must install to perform this function')

        # mask float
        mask = 1. * mask
        # normalize to 1
        mask /= np.max(mask)
        # threshold the mask
        ret, thresh = cv2.threshold(mask, 0.5, 255, 0)
        # find contours
        major, minor, _ = cv2.__version__.split(".")
        if int(major) > 3:
            contours, hierarchy = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        else:
            _, contours, hierarchy = cv2.findContours(thresh.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        if len(contours) == 0:
            # no contours were found
            new_pts_list = []
        else:
            # calculate contours area
            areas = np.asarray([cv2.contourArea(cnt) for cnt in contours])
            # take onr contour with maximum area
            sorted_areas_inds = areas.argsort()[::-1]
            filtered_contours = [contours[s_ind] for s_ind in
                                 sorted_areas_inds if areas[s_ind] > min_area]  # filter by area size
            filtered_contours = filtered_contours[:max_instances]  # take only the first max_instance of the results
            # estimate contour to reduce number of points
            new_pts_list = list()
            for curve in filtered_contours:
                if epsilon is None:
                    epsilon = 0.0005 * cv2.arcLength(curve=curve,
                                                     closed=True)
                new_pts_list.append(np.squeeze(cv2.approxPolyDP(curve=curve,
                                                                epsilon=epsilon,
                                                                closed=True)))
        polygons = [cls(geo=new_pts,
                        label=label,
                        attributes=attributes,
                        ) for new_pts in new_pts_list]

        if len(polygons) == 1:
            polygons = polygons[0]
        return polygons

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(coordinates=_json["coordinates"][0])
        elif "data" in _json:
            geo = cls.from_coordinates(coordinates=_json["data"][0])
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
