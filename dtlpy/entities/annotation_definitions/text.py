from . import BaseAnnotationDefinition


class Text(BaseAnnotationDefinition):
    """
        can create a text annotation having two types (paragraph, block)
    """
    type = "text_mark"

    def __init__(self, text_type, start, end, label,
                 top=None, left=None, attributes=None, description=None):
        """
        can create a text annotation having two types (paragraph, block)

        :param text_type: text type (paragraph, block)
        :param start: start position in characters
        :param end: end position in characters
        :param label: annotation label
        :param top: top box pixel
        :param left: left box pixel
        :param attributes: a list of attributes for the annotation
        :param description:

        :return:
        """
        super().__init__(description=description)
        self.text_type = text_type
        self.start = start
        self.end = end
        self.top = top
        self.left = left
        self.label = label
        if attributes is None:
            attributes = list()
        self.attributes = attributes

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def geo(self):
        return list()

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
        return self.add_text_to_image(image=image, annotation=self)

    def to_coordinates(self, color):
        coordinates = {
            "type": self.text_type,
            "label": self.label,
            "start": self.start,
            "end": self.end
        }
        if self.top is not None and self.left is not None:
            coordinates['top'] = self.top
            coordinates['left'] = self.left
        return coordinates

    @classmethod
    def from_json(cls, _json):
        attributes = _json.get("attributes", list())
        coordinates = _json["coordinates"]

        return cls(
            text_type=coordinates.get("type"),
            start=coordinates.get("start"),
            end=coordinates.get("end"),
            top=coordinates.get("top", None),
            left=coordinates.get("left", None),
            label=_json["label"],
            attributes=attributes,
        )
