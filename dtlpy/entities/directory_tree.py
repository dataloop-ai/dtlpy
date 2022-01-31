import logging

logger = logging.getLogger(name='dtlpy')


class DirectoryTree:
    """
    Dataset DirectoryTree

    """

    def __init__(self, _json):
        self.dirs = list()
        self.root = SingleDirectory(directory_tree=self, children=_json.get('children', None),
                                    value=_json.get('value', None))
        self.tree = _json

    @property
    def dir_names(self):
        return [directory.path for directory in self.dirs]


class SingleDirectory:
    """
    DirectoryTree single directory

    """

    def __init__(self, value, directory_tree, children=None):
        self.id = value.get('id', None)
        self.name = value.get('name', None)
        self.parent = value.get('dir', None)
        self.path = value.get('filename', None)
        self.metadata = value.get('metadata', dict())

        self.children = list()

        if children is not None:
            for child in children:
                self.children.append(
                    SingleDirectory(directory_tree=directory_tree, children=child.get('children', None),
                                    value=child['value']))

        directory_tree.dirs.append(self)
