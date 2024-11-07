from . import BaseAnnotationDefinition


class GisType:
    """
    State enum
    """
    BOX = 'box'
    POLYGON = 'polygon'
    POLYLINE = 'polyline'
    POINT = 'point'


class Gis(BaseAnnotationDefinition):
    """
        Box annotation object
        Can create a box using 2 point using: "top", "left", "bottom", "right" (to form a box [(left, top), (right, bottom)])
        For rotated box add the "angel"
    """
    type = "gis"

    def __init__(self,
                 annotation_type: GisType,
                 geo,
                 label=None,
                 attributes=None,
                 description=None,
                 ):
        """
        Can create gis annotation using points:

        :param geo: list of points
        :param label: annotation label
        :param attributes: a list of attributes for the annotation
        :param description:

        :return:
        """
        super().__init__(description=description, attributes=attributes)

        if geo is None:
            raise ValueError('geo must be provided')
        if annotation_type is None:
            raise ValueError('annotation_type must be provided')
        self.label = label
        self.annotation = None
        self.geo = geo
        self.annotation_type = annotation_type

    def to_coordinates(self, color):
        return {
            "geo_type": self.annotation_type,
            "wgs84_geo_coordinates": self.geo
        }

    @classmethod
    def from_json(cls, _json):
        json_coordinates = _json.get("coordinates", {}) if "coordinates" in _json else _json.get("data", {})
        coordinates = json_coordinates.get("wgs84_geo_coordinates", None)
        annotations_type = json_coordinates.get("geo_type", None)
        if coordinates is None:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        return cls(
            annotation_type=annotations_type,
            geo=coordinates,
            label=_json["label"],
            attributes=_json.get("attributes", None)
        )
