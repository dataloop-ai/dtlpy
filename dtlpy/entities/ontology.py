import traceback
from collections import namedtuple
import logging
import random
import attr

from .. import entities, PlatformException, repositories, services, exceptions

from .label import Label

logger = logging.getLogger(name=__name__)


class LabelHandlerMode:
    ADD = "add"
    UPDATE = "update"
    UPSERT = "upsert"


@attr.s
class Ontology(entities.BaseEntity):
    """
    Ontology object
    """
    # api
    _client_api = attr.ib(type=services.ApiClient, repr=False)

    # params
    id = attr.ib()
    creator = attr.ib()
    url = attr.ib(repr=False)
    title = attr.ib()
    labels = attr.ib(repr=False)
    metadata = attr.ib(repr=False)
    attributes = attr.ib()

    # entities
    _recipe = attr.ib(repr=False, default=None)
    _dataset = attr.ib(repr=False, default=None)
    _project = attr.ib(repr=False, default=None)

    # repositories
    _repositories = attr.ib(repr=False)

    # defaults
    _instance_map = attr.ib(default=None, repr=False)

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
        if self._recipe is not None:
            assert isinstance(self._recipe, entities.Recipe)
        return self._recipe

    @property
    def dataset(self):
        if self._dataset is not None:
            assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def project(self):
        if self._project is not None:
            assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def ontologies(self):
        if self._repositories.ontologies is not None:
            assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def labels_flat_dict(self):
        flatten_dict = dict()

        def add_to_dict(tag, father):
            flatten_dict[tag] = father
            for child in father.children:
                add_to_dict('{}.{}'.format(tag, child.tag), child)

        for label in self.labels:
            add_to_dict(label.tag, label)
        return flatten_dict

    @property
    def instance_map(self):
        if self._instance_map is None:
            labels = [label for label in self.labels_flat_dict]
            labels.sort()
            # each label gets index as instance id
            self._instance_map = {label: (i_label + 1) for i_label, label in enumerate(labels)}
        return self._instance_map

    @staticmethod
    def _protected_from_json(_json, client_api, recipe, dataset, project, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :return:
        """
        try:
            ontology = Ontology.from_json(_json=_json,
                                          client_api=client_api,
                                          project=project,
                                          dataset=dataset,
                                          recipe=recipe,
                                          is_fetched=is_fetched)
            status = True
        except Exception:
            ontology = traceback.format_exc()
            status = False
        return status, ontology

    @classmethod
    def from_json(cls, _json, client_api, recipe, dataset=None, project=None, is_fetched=True):
        """
        Build an Ontology entity object from a json

        :param is_fetched:
        :param project:
        :param dataset:
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

        inst = cls(
            metadata=_json.get("metadata", None),
            creator=_json.get("creator", None),
            url=_json.get("url", None),
            id=_json["id"],
            title=_json.get("title", None),
            attributes=attributes,
            client_api=client_api,
            project=project,
            dataset=dataset,
            recipe=recipe,
            labels=labels,
        )

        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        roots = [label.to_root() for label in self.labels]
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Ontology)._client_api,
                                                              attr.fields(Ontology)._recipe,
                                                              attr.fields(Ontology)._project,
                                                              attr.fields(Ontology)._dataset,
                                                              attr.fields(Ontology)._instance_map,
                                                              attr.fields(Ontology)._repositories))
        _json["roots"] = roots
        return _json

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

    def _add_children(self, label_name, children, labels_node, mode):
        for child in children:
            if not isinstance(child, entities.Label):
                if isinstance(child, dict):
                    if "label_name" in child:
                        child = dict(child)
                        child["label_name"] = "{}.{}".format(label_name, child["label_name"])
                        labels_node += self._base_labels_handler(labels=[child], update_ontology=False, mode=mode)
                    else:
                        raise PlatformException("400",
                                                "Invalid parameters - child list must have label name attribute")
                else:
                    raise PlatformException("400", "Invalid parameters - child must be a dict type")
            else:
                child.tag = "{}.{}".format(label_name, child.tag)
                labels_node += self._base_labels_handler(labels=child, update_ontology=False, mode=mode)

        return labels_node

    def _labels_handler_update_mode(self, json_req, upsert=False, log_error=True):
        json_req['upsert'] = upsert
        success, response = self._client_api.gen_request(req_type="PATCH",
                                                         path="/ontologies/%s/labels" % self.id,
                                                         json_req=json_req,
                                                         log_error=log_error)
        if success:
            logger.debug("Labels {} has been added successfully".format(json_req))
        else:
            raise exceptions.PlatformException(response)
        return response

    def _labels_handler_add_mode(self, json_req):
        success, response = self._client_api.gen_request(req_type="PATCH",
                                                         path="/ontologies/%s/addLabels" % self.id,
                                                         json_req=json_req)
        if success:
            logger.debug("Labels {} has been added successfully".format(json_req))
        else:
            raise exceptions.PlatformException(response)
        return response

    def _base_labels_handler(self, labels, update_ontology=True, mode=LabelHandlerMode.ADD):
        """
        Add a single label to ontology using add label endpoint , nested label is also supported

        :param labels = list of labels
        :param update_ontology - return json_req if False
        :param mode add, update or upsert, relevant on update_ontology=True only
        :return: Ontology updated entire label entity
        """
        labels_node = list()
        if mode not in [LabelHandlerMode.ADD,
                        LabelHandlerMode.UPDATE,
                        LabelHandlerMode.UPSERT]:
            raise ValueError('mode must be on of: "add", "update", "upsert"')

        if not isinstance(labels, list):  # for case that add label get one label
            labels = [labels]

        for label in labels:
            if isinstance(label, str):
                # Generate label from string
                label = entities.Label(tag=label)
            elif not isinstance(label, entities.Label):
                # Generate label from json
                label = Label.from_root(label)

            if isinstance(label, entities.Label):
                # label entity
                label_node = {"tag": label.tag}
                if label.color is not None:
                    label_node["color"] = label.color
                if label.attributes is not None:
                    label_node["attributes"] = label.attributes
                if label.display_label is not None:
                    label_node["displayLabel"] = label.display_label

                labels_node.append(label_node)
                children = label.children
                self._add_children(label.tag, children, labels_node, mode=mode)
            else:
                raise PlatformException("400",
                                        "Invalid parameters - Label can be list of str, Labels or dict")

        if not update_ontology or not len(labels_node):
            return labels_node

        json_req = {
            "labelsNode": labels_node
        }

        if mode == LabelHandlerMode.ADD:
            response = self._labels_handler_add_mode(json_req)
        elif mode == LabelHandlerMode.UPDATE:
            response = self._labels_handler_update_mode(json_req)
        else:
            response = self._labels_handler_update_mode(json_req, upsert=True, log_error=False)

        added_label = list()
        if "roots" not in response.json():
            raise exceptions.PlatformException("error fetching updated labels from server")

        for root in response.json()["roots"]:  # to get all labels
            added_label.append(entities.Label.from_root(root=root))

        self.labels = added_label
        return added_label

    def _label_handler(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                       add=True, update_ontology=False, mode=LabelHandlerMode.ADD):
        """
        Add a single label to ontology

        :param add:
        :param label:
        :param label_name: label name
        :param color: optional - if not given a random color will be selected
        :param children: optional - children
        :param attributes: optional - attributes
        :param display_label: optional - display_label
        :param update_ontology: update the ontology, default = False for backward compatible
        :param mode add, update or upsert, relevant on update_ontology=True only
        :return: Label entity
        """

        if update_ontology:
            if isinstance(label, entities.Label) or isinstance(label, str):
                return self._base_labels_handler(labels=label, update_ontology=update_ontology, mode=mode)
            else:
                return self._base_labels_handler({
                    "tag": label_name,
                    "displayLabel": display_label,
                    "color": color,
                    "attributes": attributes,
                    "children": children
                }, update_ontology=update_ontology, mode=mode)

        if not isinstance(label, entities.Label):
            if "." in label_name:
                raise PlatformException("400",
                                        "Invalid parameters - nested label can work with update_ontology option only")

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

            # add children    
            added_children = list()
            for child in children:
                if not isinstance(child, entities.Label):
                    added_children.append(self._label_handler(**child, add=False))
                else:
                    added_children.append(child)

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
                "children": list(),
            }
            added_label = entities.Label.from_root(root)
            added_label.children = added_children
        else:
            added_label = label

        if add:
            self.labels.append(added_label)
            if update_ontology:
                self.update()
        return added_label

    def _labels_handler(self, label_list, update_ontology=False, mode=LabelHandlerMode.ADD):
        """
        Adds a list of labels to ontology

        :param label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel",
                                            "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :param update_ontology: update the ontology, default = False for backward compatible
        :param mode add, update or upsert, relevant on update_ontology=True only
        :return: List of label entities added
        """
        if update_ontology:
            return self._base_labels_handler(labels=label_list, mode=mode)
        labels = list()
        for label in label_list:

            if isinstance(label, str):
                label = entities.Label(tag=label)

            if isinstance(label, entities.Label):
                # label entity
                labels.append(label)
            else:
                # dictionary
                labels.append(Label.from_root(label))
        added_labels = list()
        for label in labels:
            added_labels.append(self._label_handler(label.tag, label=label, update_ontology=update_ontology))

        return added_labels

    def delete_labels(self, label_names):
        """
        Delete labels from ontology

        :param label_names: label object/ label name / list of label objects / list of label names
        :return:
        """
        if not isinstance(label_names, list):
            label_names = [label_names]

        if isinstance(label_names[0], entities.Label):
            label_names = [label.tag for label in label_names]

        for label in label_names:
            self.__delete_label(label)

        self.update()

    def __delete_label(self, label_name):
        if label_name in self.instance_map.keys():
            labels = self.labels
            label_chain = label_name.split('.')
            while len(label_chain) > 1:
                label_name = label_chain.pop(0)
                for i_label, label in enumerate(labels):
                    if label.tag == label_name:
                        labels = labels[i_label].children
                        break
            label_name = label_chain[0]
            for i_label, label in enumerate(labels):
                if label.tag == label_name:
                    labels.pop(i_label)

    def add_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                  add=True, update_ontology=False):
        """
        Add a single label to ontology

        :param add:
        :param label:
        :param label_name: label name
        :param color: optional - if not given a random color will be selected
        :param children: optional - children
        :param attributes: optional - attributes
        :param display_label: optional - display_label
        :param update_ontology: update the ontology, default = False for backward compatible
        :return: Label entity
        """
        return self._label_handler(label_name=label_name, color=color, children=children, attributes=attributes,
                                   display_label=display_label, label=label, add=add, update_ontology=update_ontology)

    def add_labels(self, label_list, update_ontology=False):
        """
        Adds a list of labels to ontology

        :param label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel",
                                            "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :param update_ontology: update the ontology, default = False for backward compatible
        :return: List of label entities added
        """
        self._labels_handler(label_list=label_list, update_ontology=update_ontology, mode=LabelHandlerMode.ADD)

    def update_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                     add=True, upsert=False, update_ontology=False):
        """
        Update a single label to ontology

        :param add:
        :param label:
        :param label_name: label name
        :param color: optional - if not given a random color will be selected
        :param children: optional - children
        :param attributes: optional - attributes
        :param display_label: optional - display_label
        :param upsert if True will add in case it does not existing
        :param update_ontology: update the ontology, default = False for backward compatible
        :return: Label entity
        """
        if upsert:
            mode = LabelHandlerMode.UPSERT
        else:
            mode = LabelHandlerMode.UPDATE

        return self._label_handler(label_name=label_name, color=color, children=children,
                                   attributes=attributes, display_label=display_label, label=label,
                                   add=add, update_ontology=update_ontology, mode=mode)

    def update_labels(self, label_list, upsert=False, update_ontology=False):
        """
        Update a list of labels to ontology

        :param label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel",
                                            "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :param upsert if True will add in case it does not existing
        :param update_ontology: update the ontology, default = False for backward compatible
        :return: List of label entities added
        """
        if upsert:
            mode = LabelHandlerMode.UPSERT
        else:
            mode = LabelHandlerMode.UPDATE
        self._labels_handler(label_list=label_list, update_ontology=update_ontology, mode=mode)
