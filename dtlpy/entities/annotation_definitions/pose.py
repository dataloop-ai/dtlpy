from . import BaseAnnotationDefinition


class Pose(BaseAnnotationDefinition):
    """
        Classification annotation object
    """

    def __init__(self, label, template_id, instance_id, attributes=None, points=None):

        self.type = "pose"
        self.label = label
        self.template_id = template_id
        self.instance_id = instance_id
        if attributes is None:
            attributes = list()
        self.attributes = attributes
        if points is None:
            points = list()
        self.points = points

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
        :param annotation_format: options: dl.ViewAnnotationOptions.list()
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
