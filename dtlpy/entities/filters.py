import logging
import attr
from ..exceptions import PlatformException

logger = logging.getLogger('dataloop.items.filters')


@attr.s
class Filters:
    """
    Filters entity to filter items from pages in platform
    """
    filenames = attr.ib(default=None)
    directories = attr.ib(default=None)
    itemType = attr.ib(default=None)
    mimetypes = attr.ib(default=None)
    itemMetadata = attr.ib(default=None)
    labels = attr.ib(default=None)

    @staticmethod
    def known_queries():
        """
        Print known filters parameters
        :return:
        """
        print([at.name for at in attr.fields(Filters)])

    def prepare(self):
        """
        To dictionary for platform call
        :return: dict
        """
        _json = attr.asdict(self)
        # remove all Nones
        _json = {key: val for key, val in _json.items() if val is not None}
        # convert to list when needed
        if 'filenames' in _json and not isinstance(_json['filenames'], list):
            _json['filenames'] = [_json['filenames']]

        if 'directories' in _json and not isinstance(_json['directories'], list):
            _json['directories'] = [_json['directories']]

        if 'mimetypes' in _json and not isinstance(_json['mimetypes'], list):
            _json['mimetypes'] = [_json['mimetypes']]

        if 'labels' in _json and not isinstance(_json['labels'], list):
            _json['labels'] = [_json['labels']]
        return _json

    @classmethod
    def from_dict(cls, filters_dict):
        """
        Load Filters object from dictionary
        :param filters_dict: dictionary of filters
        :return: self
        """
        if not isinstance(filters_dict, dict):
            logger.exception('Input must be a dictionary')
            raise ValueError('Input must be a dictionary')

        bad_query = False
        kwargs = dict()
        unknown = list()
        for key, val in filters_dict.items():
            if key not in cls.known_queries:
                unknown.append(key)
                bad_query = True
            else:
                kwargs[key] = val
        if bad_query:
            raise PlatformException(
                error='400',
                message='Unknown filters keys used. Known: {known}. user inputs: {unknown}'.format(
                    known=cls.known_queries(),
                    unknown=unknown))
        return cls(**kwargs)
