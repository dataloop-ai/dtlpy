import numpy as np
import time

from . import Box
from ...services.api_client import client as api_client


class Note(Box):
    """
        Note annotation object
    """

    def __init__(
            self,
            left,
            top,
            right,
            bottom,
            label,
            attributes=None,
            messages=None,
            status='issue',
            assignee=None,
            create_time=None,
            creator=None,
            description=None
    ):
        super(Note, self).__init__(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            label=label,
            attributes=attributes,
            description=description
        )
        self.type = "note"
        if messages is None:
            messages = []
        if not isinstance(messages, list):
            messages = [messages]
        for msg_index in range(len(messages)):
            if not isinstance(messages[msg_index], Message):
                messages[msg_index] = Message(body=messages[msg_index])
        self.messages = messages
        self.status = status
        self.create_time = create_time
        self.creator = creator
        if self.creator is None:
            self.creator = api_client.info()['user_email']
        self.assignee = assignee
        if self.assignee is None:
            self.assignee = self.creator

    def to_coordinates(self, color):
        box = super(Note, self).to_coordinates(color=color)
        note = {
            'messages': [msg.to_json() for msg in self.messages],
            'status': self.status,
            'createTime': self.create_time,
            'creator': self.creator,
            'assignee': self.assignee
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
        messages = [Message.from_json(msg) for msg in note_data.get('messages', list())]

        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            label=_json["label"],
            attributes=_json.get("attributes", None),
            messages=messages,
            status=note_data.get('status', 'open'),
            creator=note_data.get('creator', 'me'),
            assignee=note_data.get('assignee', 'me'),
            create_time=note_data.get('createTime', 0),
        )

    def add_message(self, body: str = None):
        self.messages.append(Message(body=body))


class Message:
    """
    Note message object
    """

    def __init__(self, msg_id: str = None, creator: str = None, msg_time=None, body: str = None):
        self.id = msg_id
        self.time = msg_time if msg_time is not None else int(time.time() * 1000)
        self.body = body
        self.creator = creator
        if self.creator is None:
            self.creator = api_client.info()['user_email']

    def to_json(self):
        _json = {
            "id": self.id,
            "creator": self.creator,
            "time": self.time,
            "body": self.body
        }
        return _json

    @staticmethod
    def from_json(_json):
        return Message(
            msg_id=_json.get('id', None),
            msg_time=_json.get('time', None),
            body=_json.get('body', None),
            creator=_json.get('creator', None)
        )
