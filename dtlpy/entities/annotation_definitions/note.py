import numpy as np

from . import Box


class Note(Box):
    """
        Note annotation object
    """

    def __init__(self, left, top, right, bottom, label, attributes=None, messages=None, status=None,
                 create_time=None, creator=None):
        super(Note, self).__init__(left=left, top=top, right=right, bottom=bottom, label=label, attributes=attributes)
        self.type = "note"
        self.messages = messages
        self.status = status
        self.create_time = create_time
        self.creator = creator

    def to_coordinates(self, color):
        box = super(Note, self).to_coordinates(color=color)
        note = {
            'messages': self.messages,
            'status': self.status,
            'createTime': self.create_time,
            'creator': self.creator
        }
        coordinates = {
            'box': box,
            'note': note
        }

        return coordinates

    @staticmethod
    def from_coordinates(coordinates):
        return Box.from_coordinates(coordinates['box'])

    @classmethod
    def from_json(cls, _json):
        if "coordinates" in _json:
            geo = cls.from_coordinates(_json["coordinates"])
            note_data = _json["coordinates"].get('note', dict())
        elif "data" in _json:
            geo = cls.from_coordinates(_json["data"])
            note_data = _json["data"].get('note', dict())
        else:
            raise ValueError('can not find "coordinates" or "data" in annotation. id: {}'.format(_json["id"]))

        left = np.min(geo[:, 0])
        top = np.min(geo[:, 1])
        right = np.max(geo[:, 0])
        bottom = np.max(geo[:, 1])

        attributes = _json.get("attributes", list())
        messages = note_data.get('messages', list())

        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            label=_json["label"],
            attributes=attributes,
            messages=messages,
            status=note_data.get('status', 'open'),
            creator=note_data.get('creator', 'me'),
            create_time=note_data.get('createTime', 0),
        )
