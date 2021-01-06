import attr
import logging
import random

from .. import PlatformException

logger = logging.getLogger(name=__name__)


@attr.s
class Label:
    tag = attr.ib()
    color = attr.ib()
    display_label = attr.ib()
    attributes = attr.ib()
    children = attr.ib()

    @attributes.default
    def set_attributes(self):
        attributes = list()
        return attributes

    @children.default
    def set_children(self):
        children = list()
        return children

    @color.default
    def set_color(self):
        color = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))
        return color

    @display_label.default
    def set_display_label(self):
        display_label = self.tag
        return display_label

    @classmethod
    def from_root(cls, root):
        """
        Build a Label entity object from a json

        :param root: _json representation of a label as it is in host
        :return: Label object
        """
        children = list()
        if 'children' in root and root['children'] is not None:
            children = [Label.from_root(child) for child in root['children']]

        root = root.get("value", root)
        if "tag" in root:
            label_name = root["tag"]
        elif "label_name" in root:
            label_name = root["label_name"]
        else:
            raise PlatformException("400", "Invalid input - each label must have a tag")

        display_label = root.get("displayLabel", None)
        if display_label is None:
            display_label = root.get("display_label", None)
        return cls(
            tag=label_name,
            color=root.get("color", None),
            display_label=display_label,
            attributes=root.get("attributes", None),
            children=children
        )

    def to_root(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        value = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Label).children,
                                                              attr.fields(Label).color,
                                                              attr.fields(Label).display_label))
        value['displayLabel'] = self.display_label
        value['color'] = self.hex
        children = [child.to_root() for child in self.children]
        _json = {
            'value': value,
            'children': children
        }
        return _json

    @property
    def rgb(self):
        """
        Return label's color in RBG format

        :return: label's color in RBG format
        """
        if self.color is None:
            color = None
        elif isinstance(self.color, str) and self.color.startswith('rgb'):
            color = tuple(eval(self.color.lstrip('rgb')))
        elif isinstance(self.color, str) and self.color.startswith('#'):
            color = tuple(int(self.color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        elif isinstance(self.color, tuple) or isinstance(self.color, list):
            color = self.color
        else:
            logger.warning('Unknown color scheme: {}'.format(self.color))
            color = (255, 0, 0)
        return color

    @property
    def hex(self):
        """
        Return label's color in HEX format

        :return: label's color in HEX format
        """
        if isinstance(self.color, tuple) or isinstance(self.color, list):
            return '#%02x%02x%02x' % self.color
        elif self.color.startswith('rgb'):
            return tuple(eval(self.color.lstrip('rgb')))
        elif self.color.startswith('#'):
            return self.color
