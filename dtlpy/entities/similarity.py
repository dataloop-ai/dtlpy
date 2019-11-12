import json
from io import BytesIO

import attr


@attr.s
class SimilarityItem:
    type = attr.ib(type=str)
    ref = attr.ib(type=str)
    target = attr.ib(type=bool, default=False)

    @classmethod
    def from_json(cls, _json):
        return cls(
            type=_json['type'],
            ref=_json['ref']
        )

    def to_json(self):
        _json = {
            'type': self.type,
            'ref': self.ref
        }

        if self.target:
            _json['target'] = self.target

        return _json


@attr.s
class Similarity:
    """
    Similarity Entity
    """
    ref = attr.ib(type=str)
    type = attr.ib(type=str)
    name = attr.ib(type=str, default=None)
    _items = attr.ib(default=list())

    @property
    def target(self):
        return SimilarityItem(ref=self.ref, type=self.type, target=True)

    @property
    def items(self):
        items = list()
        for item in self._items:
            items.append(SimilarityItem.from_json(_json=item))
        return items

    @classmethod
    def from_json(cls, _json):

        return cls(
            ref=_json['metadata']['target']['ref'],
            type=_json['metadata']['target']['type'],
            items=_json.get('items', list())
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        items = list()
        items.append(self.target.to_json())
        for item in self.items:
            items.append(item.to_json())

        target = {
            "type": self.type,
            "ref": self.ref
        }

        _json = {
            "type": "collection",
            "shebang": "dataloop",
            "metadata": {
                "dltype": "collection",
                "target": target
            },
            "items": items
        }

        return _json

    def to_bytes_io(self):
        byte_io = BytesIO()
        byte_io.name = self.name
        byte_io.write(json.dumps(self.to_json()).encode())
        byte_io.seek(0)

        return byte_io

    def add(self, ref, type='id'):
        item = {
            'ref': ref,
            'type': type
        }

        self._items.append(item)

    def pop(self, ref):
        for item in self._items:
            if item['ref'] == ref:
                self._items.remove(item)
