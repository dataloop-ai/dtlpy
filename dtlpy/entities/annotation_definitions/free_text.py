from . import BaseAnnotationDefinition


class FreeText(BaseAnnotationDefinition):
    """
    Free text annotation type (e.g. response for a prompt)
    """
    type = "text"

    def __init__(self, text, label='free-text', attributes=None, description=None):
        """
        Create a free text annotation
        :param label: annotation label
        :param text: string of the annotation
        :param attributes: annotation attributes
        :param description:

        :return:
        """
        super().__init__(description=description, attributes=attributes)
        self.text = text
        self.label = label

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    @property
    def geo(self):
        return list()

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
        return self.text

    def to_coordinates(self, color):
        return self.text

    @classmethod
    def from_json(cls, _json):
        coordinates = _json["coordinates"]

        return cls(
            text=coordinates,
            label=_json["label"],
            attributes=_json.get("attributes", None),
        )
