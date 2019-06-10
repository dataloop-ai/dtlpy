import logging


class Query:
    """
    Query entity to filter items from pages in platform
    """

    def __init__(self):
        self.logger = logging.getLogger('dataloop.items.query')
        self._known_queries = list(['directories', 'filenames', 'itemType', 'mimetypes', 'itemMetadata'])
        self.query = dict()

    def __call__(self, filename=None, directory=None, itemType=None, mimetypes=None, itemMetadata=None):
        """
        Add filter to Query
        :param filename:
        :param directory:
        :return: self
        """
        # filenames
        if filename is not None:
            if isinstance(filename, str):
                filename = [filename]
            if 'filenames' not in self.query:
                self.query['filenames'] = list()
            self.query['filenames'] += filename

        # directories
        if directory is not None:
            if isinstance(directory, str):
                directory = [directory]
            if 'directories' not in self.query:
                self.query['directories'] = list()
            self.query['directories'] += directory

        # itemtype
        if itemType is not None:
            if isinstance(itemType, str):
                itemType = [itemType]
            if 'itemType' not in self.query:
                self.query['itemType'] = list()
            self.query['itemType'] += itemType

        # mimetypes
        if mimetypes is not None:
            if isinstance(mimetypes, str):
                mimetypes = [mimetypes]
            if 'mimetypes' not in self.query:
                self.query['mimetypes'] = list()
            self.query['mimetypes'] = mimetypes

        if itemMetadata is not None:
            self.query['itemMetadata'] = itemMetadata

        return self

    def known_queries(self):
        """
        Print known query parameters
        :return:
        """
        print(self._known_queries)

    def to_dict(self):
        """
        To dictionary for platform call
        :return: Query
        """
        return self.query

    def from_dict(self, query):
        """
        Load Query from dictionary
        :param query:
        :return: self
        """
        if not isinstance(query, dict):
            self.logger.exception('Input must be a dictionary')
            raise ValueError('Input must be a dictionary')

        bad_query = False
        for key, val in query.items():
            if key not in self._known_queries:
                self.logger.exception('Unknown query key: %s. Known keys: %s' % (key, ','.join(self._known_queries)))
                bad_query = True
            else:
                self.query[key] = val
        if bad_query:
            raise ValueError('Unknown query keys. See above for more information')
        return self
