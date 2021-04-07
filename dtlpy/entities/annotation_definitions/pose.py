import numpy as np
import uuid

from . import BaseAnnotationDefinition


class Pose(BaseAnnotationDefinition):
    """
        Classification annotation object
    """

    def __init__(self, label, template_id, instance_id=None, attributes=None, points=None, description=None):
        super().__init__(description=description)
        self.type = "pose"
        self.label = label
        self.template_id = template_id
        if instance_id is None:
            instance_id = str(uuid.uuid1())
        self.instance_id = instance_id
        if attributes is None:
            attributes = list()
        self.attributes = attributes
        if points is None:
            points = list()
        self.points = points

    @property
    def x(self):
        return [point.x for point in self.points]

    @property
    def y(self):
        return [point.y for point in self.points]

    @property
    def geo(self):
        return list()

    @property
    def left(self):
        if not len(self.points):
            return 0
        return np.min(self.x)

    @property
    def top(self):
        if not len(self.points):
            return 0
        return np.min(self.y)

    @property
    def right(self):
        if not len(self.points):
            return 0
        return np.max(self.x)

    @property
    def bottom(self):
        if not len(self.points):
            return 0
        return np.max(self.y)

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
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):
        return {'templateId': self.template_id,
                'instanceId': self.instance_id}

    @staticmethod
    def from_coordinates(coordinates):
        return coordinates

    @classmethod
    def from_json(cls, _json):
        attributes = _json.get("attributes", list())
        return cls(
            label=_json["label"],
            attributes=attributes,
            template_id=cls.from_coordinates(_json["coordinates"])['templateId'],
            instance_id=cls.from_coordinates(_json["coordinates"])['instanceId']
        )
