import datetime
import tabulate
import logging
import zipfile
import pandas
import os

from .. import exceptions

logger = logging.getLogger('dataloop.List')


class List(list):
    def print(self, show_all=False):
        try:
            to_print = list()
            keys_list = list()
            for element in self.__iter__():
                item_dict = element.to_json()
                to_print.append(item_dict)
                [keys_list.append(key) for key in list(item_dict.keys()) if key not in keys_list]
            try:
                # try sorting bt creation date
                to_print = sorted(to_print, key=lambda k: k['createdAt'])
            except KeyError:
                pass
            except Exception as err:
                logger.exception(err)

            remove_keys_list = ['contributors', 'url', 'annotations', 'items', 'export', 'directoryTree',
                                'attributes', 'partitions', 'metadata', 'stream', 'updatedAt', 'arch',
                                'input', 'revisions', 'pipeline',  # task fields
                                'feedbackQueue',  # session fields
                                '_ontology_ids', '_labels',  # dataset
                                'esInstance', 'esIndex',  # time series fields
                                'thumbnail' # item thumnail too long
                                ]
            if not show_all:
                for key in remove_keys_list:
                    if key in keys_list:
                        keys_list.remove(key)

            for element in to_print:
                if 'name' in element:
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
            print('\n{}'.format(tabulate.tabulate(df, headers='keys', tablefmt='psql')))

        except Exception as err:
            raise exceptions.PlatformException('400', 'Printing error')


class Miscellaneous:
    def __init__(self):
        pass

    @staticmethod
    def zip_directory(path=None):
        if not path:
            path = os.getcwd()
        assert os.path.isdir(path), '[ERROR] Directory does not exists: %s' % path
        # save zip in the parent directory
        zip_filename = os.path.join(os.path.dirname(path), os.path.basename(path) + '.zip')
        # init zip file
        zipf = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                filename, file_extension = os.path.splitext(file)
                # write relative file to zip
                zipf.write(os.path.join(root, file),
                           arcname=os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
        zipf.close()

    @staticmethod
    def unzip_directory(zip_filename, to_directory=None):
        zip_ref = zipfile.ZipFile(zip_filename, 'r')
        # the zip contains the full directory so
        # unzipping straight to path (without another directory)
        if not to_directory:
            to_directory = '.'
        zip_ref.extractall(to_directory)
        zip_ref.close()
        return to_directory
