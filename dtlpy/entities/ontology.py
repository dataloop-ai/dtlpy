from collections import namedtuple
import traceback
import logging
import random
import uuid
import attr
import os

from .. import entities, PlatformException, repositories, exceptions
from ..services.api_client import ApiClient
from .label import Label

logger = logging.getLogger(name='dtlpy')


class AttributesTypes:
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    SLIDER = "range"
    YES_NO = "boolean"
    FREE_TEXT = "freeText"

class AttributesRange:
    def __init__(self, min_range, max_range, step):
        self.min_range = min_range
        self.max_range = max_range
        self.step = step

    def to_json(self):
        return {'min': self.min_range, 'max': self.max_range, 'step': self.step}


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
    _client_api = attr.ib(type=ApiClient, repr=False)

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
    _color_map = attr.ib(default=None, repr=False)

    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['ontologies', 'datasets', 'projects'])

        if self._recipe is None:
            ontologies = repositories.Ontologies(client_api=self._client_api, recipe=self._recipe)
        else:
            ontologies = self.recipe.ontologies

        r = reps(ontologies=ontologies, datasets=repositories.Datasets(client_api=self._client_api),
                 projects=repositories.Projects(client_api=self._client_api))
        return r

    @property
    def recipe(self):
        if self._recipe is None:
            filters = entities.Filters(resource=entities.FiltersResource.RECIPE)
            filters.add(field="ontologies", values=self.id)
            recipes = self.project.recipes.list(filters=filters)
            if recipes.items_count > 0:
                self._recipe = recipes.items[0]
            else:
                logger.warning(f"Ontology ID: {self.id} Does not belong to a recipe")
        if self._recipe is not None:
            assert isinstance(self._recipe, entities.Recipe)
        return self._recipe

    @property
    def dataset(self):
        if self._dataset is None:
            if self.recipe is not None:
                self._dataset = self.recipe.dataset
        if self._dataset is not None:
            assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @property
    def project(self):
        if self._project is None:
            if 'system' in self.metadata:
                project_id = self.metadata['system'].get('projectIds', None)
                if project_id is not None:
                    self._project = self.projects.get(project_id=project_id[0])
            elif self.dataset is not None:
                self._project = self.dataset.project
        if self._project is not None:
            assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def ontologies(self):
        if self._repositories.ontologies is not None:
            assert isinstance(self._repositories.ontologies, repositories.Ontologies)
        return self._repositories.ontologies

    @property
    def projects(self):
        if self._repositories.projects is not None:
            assert isinstance(self._repositories.projects, repositories.Projects)
        return self._repositories.projects

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
        """
         instance mapping for creating instance mask

        :return dictionary {label: map_id}
        :rtype: dict
        """
        if self._instance_map is None:
            labels = [label for label in self.labels_flat_dict]
            labels.sort()
            # each label gets index as instance id
            self._instance_map = {label: (i_label + 1) for i_label, label in enumerate(labels)}
        return self._instance_map

    @instance_map.setter
    def instance_map(self, value: dict):
        """
        instance mapping for creating instance mask

        :param value: dictionary {label: map_id}
        :rtype: dict
        """
        if not isinstance(value, dict):
            raise ValueError('input must be a dictionary of {label_name: instance_id}')
        self._instance_map = value

    @property
    def color_map(self):
        """
        Color mapping of labels, {label: rgb}

        :return: dict
        :rtype: dict
        """
        if self._color_map is None:
            self._color_map = {k: v.rgb for k, v in self.labels_flat_dict.items()}
        return self._color_map

    @color_map.setter
    def color_map(self, values):
        """
        Color mapping of labels, {label: rgb}

        :param values: dict {label: rgb}
        :return:
        """
        if not isinstance(values, dict):
            raise ValueError('input must be a dict. got: {}'.format(type(values)))
        self._color_map = values

    @staticmethod
    def _protected_from_json(_json, client_api, recipe=None, dataset=None, project=None, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: platform json
        :param client_api: ApiClient entity
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

    @property
    def _use_attributes_2(self):
        if isinstance(self.metadata, dict):
            attributes = self.metadata.get("attributes", None)
            if attributes is not None:
                return True
            else:
                if isinstance(self.attributes, list) and len(self.attributes) > 0:
                    return False
        return True

    @classmethod
    def from_json(cls, _json, client_api, recipe=None, dataset=None, project=None, is_fetched=True):
        """
        Build an Ontology entity object from a json

        :param bool is_fetched: is Entity fetched from Platform
        :param dtlpy.entities.project.Project project: project entity
        :param dtlpy.entities.dataset.Dataset dataset: dataset
        :param dict _json: _json response from host
        :param dtlpy.entities.recipe.Recipe recipe: ontology's recipe
        :param dl.ApiClient client_api: ApiClient entity
        :return: Ontology object
        :rtype: dtlpy.entities.ontology.Ontology
        """
        attributes_v2 = _json.get('metadata', {}).get("attributes", [])
        attributes_v1 = _json.get("attributes", [])
        attributes = attributes_v2 if attributes_v2 else attributes_v1

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
        :rtype: dict
        """
        roots = [label.to_root() for label in self.labels]
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Ontology)._client_api,
                                                              attr.fields(Ontology)._recipe,
                                                              attr.fields(Ontology)._project,
                                                              attr.fields(Ontology)._dataset,
                                                              attr.fields(Ontology)._instance_map,
                                                              attr.fields(Ontology)._color_map,
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

        :param bool system_metadata: bool - True, if you want to change metadata system
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

    def _base_labels_handler(self, labels, update_ontology=True, mode=LabelHandlerMode.UPSERT):
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
            elif isinstance(label, dict):
                # Generate label from dict
                label = Label.from_root(label)
            elif isinstance(label, entities.Label):
                ...
            else:
                raise ValueError(
                    'Unsupported type for `labels`. Expected a list of (str, dict, dl.Label). Got: {}'.format(
                        type(label)))

            # label entity
            label_node = {"tag": label.tag}
            if label.color is not None:
                label_node["color"] = label.hex
            if label.attributes is not None:
                label_node["attributes"] = label.attributes
            if label.display_label is not None:
                label_node["displayLabel"] = label.display_label
            if label.display_data is not None:
                label_node["displayData"] = label.display_data
            labels_node.append(label_node)
            children = label.children
            self._add_children(label.tag, children, labels_node, mode=mode)

        if not update_ontology or not len(labels_node):
            return labels_node

        json_req = {
            "labelsNode": labels_node
        }

        if mode == LabelHandlerMode.UPDATE:
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

    def _add_image_label(self, icon_path):
        display_data = dict()
        if self.project is not None:
            dataset = self.project.datasets._get_binaries_dataset()
        elif self.dataset is not None:
            dataset = self.dataset.project.datasets._get_binaries_dataset()
        else:
            raise ValueError('must have project or dataset to create with icon path')
        platform_path = "/.dataloop/ontologies/{}/labelDisplayImages/".format(self.id)
        basename = os.path.basename(icon_path)
        item = dataset.items.upload(local_path=icon_path,
                                    remote_path=platform_path,
                                    remote_name='{}-{}'.format(uuid.uuid4().hex, basename))
        display_data['displayImage'] = dict()
        display_data['displayImage']['itemId'] = item.id
        display_data['displayImage']['datasetId'] = item.dataset_id
        return display_data

    def _label_handler(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                       add=True, icon_path=None, update_ontology=False, mode=LabelHandlerMode.UPSERT):
        """
        Add a single label to ontology

        :param label_name: label name
        :param color: optional - if not given a random color will be selected
        :param children: optional - children
        :param attributes: optional - attributes
        :param display_label: optional - display_label
        :param label: label
        :param add:to add or not
        :param icon_path: path to image to be display on label
        :param update_ontology: update the ontology, default = False for backward compatible
        :param mode add, update or upsert, relevant on update_ontology=True only
        :return: Label entity
        """

        if update_ontology:
            if isinstance(label, entities.Label) or isinstance(label, str):
                return self._base_labels_handler(labels=label,
                                                 update_ontology=update_ontology,
                                                 mode=mode)
            else:
                display_data = dict()
                if icon_path is not None:
                    display_data = self._add_image_label(icon_path=icon_path)
                return self._base_labels_handler(labels={"tag": label_name,
                                                         "displayLabel": display_label,
                                                         "color": color,
                                                         "attributes": attributes,
                                                         "children": children,
                                                         "displayData": display_data
                                                         },
                                                 update_ontology=update_ontology,
                                                 mode=mode)

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

            display_data = dict()
            if icon_path is not None:
                display_data = self._add_image_label(icon_path=icon_path)

            root = {
                "value": {
                    "tag": label_name,
                    "displayLabel": display_label,
                    "color": color,
                    "attributes": attributes,
                    "displayData": display_data
                },
                "children": list(),
            }
            added_label = entities.Label.from_root(root)
            added_label.children = added_children
        else:
            added_label = label
        if add and self._validate_label(added_label=added_label, mode=mode, color=color,
                                        children=children, attributes=attributes,
                                        display_label=display_label, display_data=icon_path):
            self.labels.append(added_label)
        self._base_labels_handler(labels=added_label, update_ontology=True, mode=mode)
        return added_label

    def _validate_label(self, added_label, mode=LabelHandlerMode.UPSERT, color=None, children=None, attributes=None,
                        display_label=None, display_data=None):
        """
        check if the label is exist
        """
        for i in range(len(self.labels)):
            if self.labels[i].tag == added_label.tag:
                if mode == LabelHandlerMode.UPDATE:
                    if color:
                        self.labels[i].color = added_label.color
                    if children:
                        self.labels[i].children = added_label.children
                    if attributes:
                        self.labels[i].attributes = added_label.attributes
                    if display_label:
                        self.labels[i].display_label = added_label.display_label
                    if display_data:
                        self.labels[i].display_data = added_label.display_data
                return False
        return True

    def _labels_handler(self, label_list, update_ontology=False, mode=LabelHandlerMode.UPSERT):
        """
        Adds a list of labels to ontology

        :param list label_list: a list of labels to add to the dataset's ontology. each value should be a dict, dl.Label or a string
                        if dictionary, should look like this: {"value": {"tag": "name of the label", "displayLabel": "display name on the platform",
                                            "color": "#hex value", "attributes": [attributes]}, "children": [children]}
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
                  add=True, icon_path=None, update_ontology=False):
        """
        Add a single label to ontology

        :param str label_name: str - label name
        :param tuple color: color
        :param children: children (sub labels)
        :param list attributes: attributes
        :param str display_label: display_label
        :param dtlpy.entities.label.Label label: label
        :param bool add: to add or not
        :param str icon_path: path to image to be display on label
        :param bool update_ontology: update the ontology, default = False for backward compatible
        :return: Label entity
        :rtype: dtlpy.entities.label.Label

        **Example**:

        .. code-block:: python

            label = ontology.add_label(label_name='person', color=(34, 6, 231), attributes=['big', 'small'])
        """
        return self._label_handler(label_name=label_name, color=color, children=children, attributes=attributes,
                                   display_label=display_label, label=label, add=add, icon_path=icon_path,
                                   update_ontology=update_ontology)

    def add_labels(self, label_list, update_ontology=False):
        """
        Adds a list of labels to ontology

        :param list label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel",
                                            "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :param bool update_ontology: update the ontology, default = False for backward compatible
        :return: List of label entities added

        **Example**:

        .. code-block:: python

            labels = ontology.add_labels(label_list=label_list)
        """
        self._labels_handler(label_list=label_list, update_ontology=update_ontology, mode=LabelHandlerMode.UPSERT)

    def update_label(self, label_name, color=None, children=None, attributes=None, display_label=None, label=None,
                     add=True, icon_path=None, upsert=False, update_ontology=False):
        """
        Update a single label to ontology

        :param str label_name: str - label name
        :param tuple color: color
        :param children: children (sub labels)
        :param list attributes: attributes
        :param str display_label: display_label
        :param dtlpy.entities.label.Label label: label
        :param bool add: to add or not
        :param str icon_path: path to image to be display on label
        :param bool update_ontology: update the ontology, default = False for backward compatible
        :param bool upsert: if True will add in case it does not existing
        :return: Label entity
        :rtype: dtlpy.entities.label.Label

        **Example**:

        .. code-block:: python

            label = ontology.update_label(label_name='person', color=(34, 6, 231), attributes=['big', 'small'])
        """
        if upsert:
            mode = LabelHandlerMode.UPSERT
        else:
            mode = LabelHandlerMode.UPDATE

        return self._label_handler(label_name=label_name, color=color, children=children,
                                   attributes=attributes, display_label=display_label, label=label,
                                   add=add, icon_path=icon_path, update_ontology=update_ontology, mode=mode)

    def update_labels(self, label_list, upsert=False, update_ontology=False):
        """
        Update a list of labels to ontology

        :param list label_list: list of labels [{"value": {"tag": "tag", "displayLabel": "displayLabel", "color": "#color", "attributes": [attributes]}, "children": [children]}]
        :param bool upsert: if True will add in case it does not existing
        :param bool update_ontology: update the ontology, default = False for backward compatible

        :return: List of label entities added

        **Example**:

        .. code-block:: python

            labels = ontology.update_labels(label_list=label_list)
        """

        if upsert:
            mode = LabelHandlerMode.UPSERT
        else:
            mode = LabelHandlerMode.UPDATE
        self._labels_handler(label_list=label_list, update_ontology=update_ontology, mode=mode)

    def update_attributes(self,
                          title: str,
                          key: str,
                          attribute_type,
                          scope: list = None,
                          optional: bool = None,
                          values: list = None,
                          attribute_range=None):
        """
        ADD a new attribute or update if exist

        :param str title: attribute title
        :param str key: the key of the attribute must br unique
        :param AttributesTypes attribute_type: dl.AttributesTypes your attribute type
        :param list scope: list of the labels or * for all labels
        :param bool optional: optional attribute
        :param list values: list of the attribute values ( for checkbox and radio button)
        :param dict or AttributesRange attribute_range: dl.AttributesRange object
        :return: true in success
        :rtype: bool
        """
        return self.ontologies.update_attributes(
            ontology_id=self.id,
            title=title,
            key=key,
            attribute_type=attribute_type,
            scope=scope,
            optional=optional,
            values=values,
            attribute_range=attribute_range)

    def delete_attributes(self, keys: list):
        """
        Delete a bulk of attributes

        :param list keys: Keys of attributes to delete
        :return: True if success
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = ontology.delete_attributes(['1'])
        """

        return self.ontologies.delete_attributes(ontology_id=self.id, keys=keys)

    def copy_from(self, ontology_json: dict):
        """
        Import ontology to the platform.\n
        Notice: only the following fields will be updated: `labels`, `attributes`, `instance_map` and `color_map`.

        :param dict ontology_json: The source ontology json to copy from
        :return: Ontology object: The updated ontology entity
        :rtype: dtlpy.entities.ontology.Ontology

        **Example**:

        .. code-block:: python

            ontology = ontology.import_ontology(ontology_json=ontology_json)
        """
        # TODO: Add support for import from ontology entity in the Future
        if not self._use_attributes_2:
            raise ValueError("This method is only supported for attributes 2 mode!")
        new_ontology = self.from_json(_json=ontology_json, client_api=self._client_api)

        # Update 'labels' and 'attributes'
        self.labels = new_ontology.labels
        new_attributes = new_ontology.attributes
        if isinstance(new_attributes, list):
            for new_attribute in new_attributes:
                attribute_range = new_attribute.get("range", None)
                if attribute_range is not None:
                    attribute_range = entities.AttributesRange(
                        min_range=attribute_range.get("min", None),
                        max_range=attribute_range.get("max", None),
                        step=attribute_range.get("step", None)
                    )
                script_data = new_attribute.get("scriptData", None)
                if script_data is None:
                    new_attribute_key = new_attribute.get("key", None)
                    raise Exception(f"Attribute '{new_attribute_key}' scriptData is missing in the ontology json!")
                self.update_attributes(
                    title=script_data.get("title", None),
                    key=new_attribute.get("key", None),
                    attribute_type=new_attribute.get("type", None),
                    scope=new_attribute.get("scope", None),
                    optional=script_data.get("optional", None),
                    values=new_attribute.get("values", None),
                    attribute_range=attribute_range
                )

        # Get remote updated 'attributes'
        self.metadata["attributes"] = self.ontologies.get(ontology_id=self.id).attributes

        # Update 'instance map' and 'color map'
        self._instance_map = new_ontology.instance_map
        self._color_map = new_ontology.color_map
        return self.update(system_metadata=True)
