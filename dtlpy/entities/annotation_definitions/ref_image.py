from . import BaseAnnotationDefinition


class RefImage(BaseAnnotationDefinition):
    """
    Create an image annotation. Reference the url or item id in this annotation type
    """
    type = "ref_image"

    def __init__(self, ref, ref_type=None, mimetype=None, label='ref-image', attributes=None, description=None):

        """
        Create an image annotation. Used for generative model and any other algorithm where and image is the output

        For type 'id', need to upload the image as item in the platform and reference the item id in the annotation.
        For type 'url', mimetype must be provided to load the ref correctly in the platform

        :param str ref: the reference to the image annotation, represented by an ‘itemId’ or ‘url’
        :param str ref_type: one of ‘id’ | ‘url’
        :param str mimetype: optional. in case the refType is URL, e.g. image/jpeg, video/mpeg
        :param label: annotation label
        :param attributes: annotation attributes
        :param description:

        :return:
        """
        super().__init__(description=description, attributes=attributes)
        if ref_type is None:
            if ref.startswith('http'):
                ref_type = 'url'
            else:
                ref_type = 'id'
        self.ref = ref
        self.ref_type = ref_type
        self.mimetype = mimetype
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
        # TODO over or show the image annotations
        return self.add_text_to_image(image=image, annotation=self)

    def to_coordinates(self, color):
        coordinates = {
            "ref": self.ref,
            "refType": self.ref_type,
            "mimetype": self.mimetype,
        }
        return coordinates

    @classmethod
    def from_json(cls, _json):
        coordinates = _json["coordinates"]
        ref = coordinates.get('ref')
        ref_type = coordinates.get('refType')
        mimetype = coordinates.get('mimetype')
        return cls(
            ref=ref,
            ref_type=ref_type,
            mimetype=mimetype,
            label=_json["label"],
            attributes=_json.get("attributes", None),
        )
