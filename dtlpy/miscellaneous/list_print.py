import datetime
import tabulate
import typing
import logging
import pandas

from .. import exceptions

logger = logging.getLogger(name='dtlpy')

T = typing.TypeVar('T')


class List(list, typing.MutableSequence[T]):
    def to_df(self, show_all=False, columns=None):
        try:
            to_print = list()
            keys_list = list()
            for element in self.__iter__():
                if hasattr(element, 'to_json'):
                    item_dict = element.to_json()
                else:
                    item_dict = element
                to_print.append(item_dict)
                [keys_list.append(key) for key in list(item_dict.keys()) if key not in keys_list]
            try:
                # try sorting bt creation date
                to_print = sorted(to_print, key=lambda k: k['createdAt'] if k['createdAt'] is not None else "")
            except KeyError:
                pass
            except Exception:
                logger.exception('Error sorting printing:')

            remove_keys_list = ['contributors', 'url', 'annotations', 'items', 'export', 'directoryTree', 'org',
                                '_contributors', 'role', 'account', 'featureConstraints',
                                'attributes', 'partitions', 'metadata', 'stream', 'updatedAt', 'arch',
                                'input', 'revisions', 'pipeline',  # task fields
                                'feedbackQueue',  # session fields
                                '_ontology_ids', '_labels',  # dataset
                                'esInstance', 'esIndex',  # time series fields
                                'thumbnail',  # item thumnail too long
                                # services fields
                                'driverId', 'useUserJwt', 'versions', 'runtime', 'mq', 'global',
                                # triggers
                                'scope',
                                # Package
                                'modules'
                                ]
            if not show_all:
                if columns is not None:
                    # take columns from inputs
                    if not isinstance(columns, list):
                        if not isinstance(columns, str):
                            raise exceptions.PlatformException(
                                error='3002',
                                message='"columns" input must be str or list. found: {}'.format(type(columns)))
                        columns = [columns]
                    keys_list = columns
                else:
                    # take default columns
                    for key in remove_keys_list:
                        if key in keys_list:
                            keys_list.remove(key)

            for element in to_print:
                # handle printing errors for not ascii string when in cli
                if 'name' in element:
                    try:
                        # check if ascii
                        element['name'].encode('ascii')
                    except UnicodeEncodeError:
                        # if not - print bytes instead
                        element['name'] = str(element['name']).encode('utf-8')
                if 'createdAt' in element:
                    try:
                        str_timestamp = str(element['createdAt'])
                        if len(str_timestamp) > 10:
                            str_timestamp = str_timestamp[:10]
                        element['createdAt'] = datetime.datetime.utcfromtimestamp(int(str_timestamp)).isoformat()
                    except Exception:
                        pass
            df = pandas.DataFrame(to_print, columns=keys_list)
            return df
        except Exception:
            raise exceptions.PlatformException(error='3002',
                                               message='Failed converting to DataFrame')

    def print(self, show_all=False, level='print', to_return=False, columns=None):
        try:
            df = self.to_df(show_all=show_all, columns=columns)
            if 'name' in list(df.columns.values):
                df['name'] = df['name'].astype(str)

            if to_return:
                return tabulate.tabulate(df, headers='keys', tablefmt='psql')
            else:
                if level == 'print':
                    print('\n{}'.format(tabulate.tabulate(df, headers='keys', tablefmt='psql')))
                elif level == 'debug':
                    logger.debug('\n{}'.format(tabulate.tabulate(df, headers='keys', tablefmt='psql')))
                else:
                    raise ValueError('unknown log level in printing: {}'.format(level))

        except Exception:
            raise exceptions.PlatformException(error='3002', message='Failed printing entity')
