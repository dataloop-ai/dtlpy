from . import BaseAnnotationDefinition


class Description(BaseAnnotationDefinition):
    """
        Subtitle annotation object
    """

    def __init__(self, text):
        self.type = "item_description"
        self.text = text
        self.label = "item.description"
        self.attributes = {}

    def to_coordinates(self, color):
        return {"text": self.text}

    @staticmethod
    def from_coordinates(coordinates):
        return coordinates["text"]

    @classmethod
    def from_json(cls, _json):
        attributes = _json.get("attributes", list())
        if "coordinates" in _json:
            text = cls.from_coordinates(coordinates=_json["coordinates"])
        elif "data" in _json:
            text = cls.from_coordinates(coordinates=_json["data"])
        else:
            raise ValueError('Bad json, "coordinates", "data" or "description" not found')
        return cls(
            text=text,
        )
