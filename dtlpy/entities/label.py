import attr
import logging

logger = logging.getLogger(name=__name__)


@attr.s
class Label:
    tag = attr.ib()
    color = attr.ib()
    display_label = attr.ib()
    attributes = attr.ib()
    children = attr.ib()

    @classmethod
    def from_root(cls, root):
        """
        Build a Label entity object from a json

        :param root: _json representation of a label as it is in host
        :return: Label object
        """
        return cls(
            tag=root['value']['tag'],
            color=root['value']['color'],
            display_label=root['value']['displayLabel'],
            attributes=root['value']['attributes'],
            children=root['children']
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
        _json = {
            'value': value,
            'children': self.children
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
            logger.warning('Unknown color scheme: %s' % self.color)
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
