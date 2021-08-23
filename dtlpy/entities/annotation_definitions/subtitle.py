from . import BaseAnnotationDefinition


class Subtitle(BaseAnnotationDefinition):
    """
        Subtitle annotation object
    """
    type = "subtitle"

    def __init__(self, text, label, attributes=None, description=None):
        super().__init__(description=description, attributes=attributes)
        self.text = text
        self.label = label

    def to_coordinates(self, color):
        return {"text": self.text}

    @staticmethod
    def from_coordinates(coordinates):
        return coordinates["text"]

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            text = cls.from_coordinates(coordinates=_json["coordinates"])
        elif "data" in _json:
            text = cls.from_coordinates(coordinates=_json["data"])
        else:
            raise ValueError('Bad json, "coordinates" or "data" not found')
        return cls(
            text=text,
            label=_json["label"],
            attributes=_json.get("attributes", None)
        )
