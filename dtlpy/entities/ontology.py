from collections import namedtuple
import logging
import random
import attr

from .. import utilities, entities, PlatformException, repositories, services

logger = logging.getLogger(name=__name__)


@attr.s
class Ontology:
    """
    Ontology object
    """
    # api
    _client_api = attr.ib(type=services.ApiClient)

    # params
    id = attr.ib()
    creator = attr.ib()
    url = attr.ib()
    labels = attr.ib()
    metadata = attr.ib()
    attributes = attr.ib()

    # entities
    _recipe = attr.ib()

    # repositories
    _repositories = attr.ib()

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['ontologies'])

        if self._recipe is None:
            ontologies = repositories.Ontologies(client_api=self._client_api, recipe=self._recipe)
        else:
            ontologies = self.recipe.ontologies

        r = reps(ontologies=ontologies)
        return r

    @property
    def recipe(self):
        assert isinstance(self._recipe, entities.Recipe)
        return self._recipe

    @property
    def ontologies(self):
        assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @classmethod
    def from_json(cls, _json, client_api, recipe):
        """
        Build an Ontology entity object from a json

        :param _json: _json response from host
        :param recipe: ontology's recipe
        :param client_api: client_api
        :return: Ontology object
        """
        if "attributes" in _json:
            attributes = _json["attributes"]
        else:
            attributes = list()

        labels = list()
        for root in _json["roots"]:
            labels.append(entities.Label.from_root(root=root))

        return cls(
            metadata=_json["metadata"],
            creator=_json["creator"],
            url=_json["url"],
            id=_json["id"],
            attributes=attributes,
            client_api=client_api,
            recipe=recipe,
            labels=labels,
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        roots = [label.to_root() for label in self.labels]
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Ontology)._client_api,
                                                              attr.fields(Ontology)._recipe,
                                                              attr.fields(Ontology)._repositories))
        _json["roots"] = roots
        return _json

    def print(self):
        utilities.List([self]).print()

    def delete(self):
        """
        Delete recipe from platform

        :return: True
        """
        return self.ontologies.delete(self.id)

    def update(self, system_metadata=False):
        """
        Update items metadata

        :param system_metadata: bool
        :return: Ontology object
        """
        return self.ontologies.update(self, system_metadata=system_metadata)

    def add_label(self, label_name, color=None, children=None, attributes=None, display_label=None):
        """
        Add a single label to ontology

        :param label_name: label name
        :param color: optional - if not given a random color will be selected
        :param children: optional - children
        :param attributes: optional - attributes
        :param display_label: optional - display_label
        :return: True if label was added
        """
        if attributes is None:
            attributes = list()
        if not isinstance(attributes, list):
            attributes = [attributes]

        # get random color if none given
        if color is None:
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        if children is None:
            children = list()
        if not isinstance(children, list):
            children = [children]
        if display_label is None:
            display_label = ""
            if len(label_name.split("_")) == 1:
                display_label = label_name[0].upper() + label_name[1:]
            else:
                for word in label_name.split("_"):
                    display_label += word[0].upper() + word[1:] + " "
                display_label = display_label[0:-1]
        root = {
            "value": {
                "tag": label_name,
                "displayLabel": display_label,
                "color": color,
                "attributes": attributes,
            },
            "children": children,
        }
        self.labels.append(entities.Label.from_root(root))
        return True

    def add_labels(self, label_list):
        """
        Adds a list of labels to ontology

        :param label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel",
                                            "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :return: True if labels were added
        """
        labels = list()
        for label in label_list:
            if isinstance(label, entities.Label):
                labels.append(
                    {
                        "label_name": label.tag,
                        "color": label.color,
                        "children": label.children,
                        "attributes": label.attributes,
                        "display_label": label.display_label,
                    }
                )
                continue
            children = label.get("children", None)
            label = label.get("value", label)
            if "tag" in label:
                label_name = label["tag"]
            else:
                raise PlatformException("400", "Invalid input - each label must have a tag")
            if "color" in label:
                color = label["color"]
            else:
                logger.warning("No color given to label. Random color will be given")
                color = None
            attributes = label.get("attributes", None)
            display_label = label.get("displayLabel", None)
            labels.append(
                {
                    "label_name": label_name,
                    "color": color,
                    "children": children,
                    "attributes": attributes,
                    "display_label": display_label,
                }
            )

        for label in labels:
            self.add_label(
                label_name=label["label_name"],
                color=label["color"],
                children=label["children"],
                attributes=label["attributes"],
                display_label=label["display_label"],
            )
        return True
