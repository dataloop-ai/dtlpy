import logging
from .. import utilities
import attr

logger = logging.getLogger("dataloop.annotation")


@attr.s
class Annotation:
    """
    Annotations object
    """

    id = attr.ib()
    metadata = attr.ib()
    creator = attr.ib()
    createdAt = attr.ib()
    updatedBy = attr.ib()
    updatedAt = attr.ib()
    itemId = attr.ib()
    url = attr.ib()
    item_url = attr.ib()

    # params
    type = attr.ib()
    label = attr.ib()
    attributes = attr.ib()
    coordinates = attr.ib()

    # entities
    dataset = attr.ib()
    item = attr.ib()

    @classmethod
    def from_json(cls, _json, dataset, item):
        """
        Build an annotation entity object from a json

        :param _json: _json respons form host
        :param dataset: dataset in which the annotation's item is located
        :param item: annotation's item
        :return: Annotation object
        """
        if "metadata" in _json:
            metadata = _json["metadata"]
        else:
            metadata = None
        return cls(
            id=_json["id"],
            type=_json["type"],
            label=_json["label"],
            attributes=_json.get("attributes", list()),
            coordinates=_json.get("coordinates", list()),
            creator=_json["creator"],
            createdAt=_json["createdAt"],
            updatedBy=_json["updatedBy"],
            updatedAt=_json["updatedAt"],
            itemId=_json["itemId"],
            url=_json["url"],
            item_url=_json["item"],
            item=item,
            dataset=dataset,
            metadata=metadata,
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        json = attr.asdict(
            self,
            filter=attr.filters.exclude(
                attr.fields(Annotation).item,
                attr.fields(Annotation).dataset,
                attr.fields(Annotation).item_url,
            ),
        )
        json.update({"item": self.item_url})
        return json

    def print(self):
        utilities.List([self]).print()

    def to_mask(self, img_shape, thickness=1, with_text=False):
        """
        Convert annotation to a colored mask
        :param img_shape
        :param thickness: line thickness
        :param with_text: add label to annotation
        :return: ndarray of the annotation
        """
        return self.item.annotations.to_mask(
            img_shape=img_shape,
            thickness=thickness,
            with_text=with_text,
            annotation=self,
        )

    def to_instance(self, img_shape, thickness=1):
        """
        Convert items annotations to an instance mask (2d array with label index)
        :param thickness: line thickness
        :param img_shape:
        :return: ndarray
        """
        return self.item.annotations.to_instance(
            img_shape=img_shape, thickness=thickness, annotation=self
        )

    def delete(self):
        """
        Remove an annotation from item
        :return: True
        """
        return self.item.annotations.delete(annotation=self, annotation_id=self.id)

    def download(
        self, filepath, get_mask=False, get_instance=False, img_shape=None, thickness=1
    ):
        """
        Save annotation to file
        :param filepath:
        :param get_mask: save mask
        :param get_instance: save instance
        :param img_shape:
        :param thickness:
        :return:
        """
        return self.item.annotations.download(
            filepath=filepath,
            get_mask=get_mask,
            get_instance=get_instance,
            img_shape=img_shape,
            thickness=thickness,
            annotation=self,
        )

    def update(self, system_metadata=False):
        """
        Update an existing annotation in host.
        :param system_metadata:
        :return: Annotation object
        """
        return self.item.annotations.update(
            annotations=self, annotations_ids=self.id, system_metadata=system_metadata
        )
