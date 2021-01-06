from . import BaseAnnotationDefinition


class Comparison(BaseAnnotationDefinition):
    """
    Comparison annotation object
    """

    def __init__(self, coordinates, label, attributes=None, description=None):
        super().__init__(description=description)
        self.type = "comparison"
        self.label = label
        self.coordinates = coordinates
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def geo(self):
        return 0

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
        :param annotation_format: options: list(dl.ViewAnnotationOptions)
        :param color: color
        :return: ndarray
        """
        if with_text:
            image = self.add_text_to_image(image=image, annotation=self)
        return image

    def to_coordinates(self, color):
        return self.coordinates

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            coordinates = _json["coordinates"]
        elif "data" in _json:
            coordinates = _json["data"]
        else:
            coordinates = dict()

        attributes = _json.get("attributes", list())

        return cls(
            coordinates=coordinates,
            label=_json.get("label", None),
            attributes=attributes
        )
