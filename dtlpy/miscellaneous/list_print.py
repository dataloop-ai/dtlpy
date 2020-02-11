import datetime
import tabulate
import logging
import pandas
from datetime import datetime

from .. import exceptions

logger = logging.getLogger(name=__name__)


class List(list):

    def print(self, show_all=False, level='print', to_return=False):
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
                to_print = sorted(to_print, key=lambda k: k['createdAt'])
            except KeyError:
                pass
            except Exception:
                logger.exception('Error sorting printing:')

            remove_keys_list = ['contributors', 'url', 'annotations', 'items', 'export', 'directoryTree',
                                'attributes', 'partitions', 'metadata', 'stream', 'updatedAt', 'arch',
                                'input', 'revisions', 'pipeline',  # task fields
                                'feedbackQueue',  # session fields
                                '_ontology_ids', '_labels',  # dataset
                                'esInstance', 'esIndex',  # time series fields
                                'thumbnail'  # item thumnail too long
                                ]
            if not show_all:
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
                        element['createdAt'] = datetime.datetime.utcfromtimestamp(int(str_timestamp)).strftime(
                            '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
            df = pandas.DataFrame(to_print, columns=keys_list)
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
            raise exceptions.PlatformException('400', 'Printing error')
