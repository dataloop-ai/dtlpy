import dictdiffer
import subprocess
import traceback
import pathspec
import datetime
import tabulate
import logging
import zipfile
import pandas
import os
from datetime import datetime

from .. import exceptions

logger = logging.getLogger(name=__name__)


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
                                'thumbnail'  # item thumnail too long
                                ]
            if not show_all:
                for key in remove_keys_list:
                    if key in keys_list:
                        keys_list.remove(key)

            is_cli = False
            tr = ''.join(traceback.format_stack())
            if 'dlp.exe' in tr:
                # running from command line
                is_cli = True
            for element in to_print:

                if is_cli:
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
            print('\n{}'.format(tabulate.tabulate(df, headers='keys', tablefmt='psql')))

        except Exception:
            raise exceptions.PlatformException('400', 'Printing error')


class Miscellaneous:
    def __init__(self):
        pass

    @staticmethod
    def zip_directory(zip_filename, directory=None):
        """
        Zip Directory
        Will ignore .gitignore files

        :param directory:
        :param zip_filename:
        :return:
        """
        # default path
        if directory is None:
            directory = os.getcwd()
        # check if directory
        assert os.path.isdir(directory), '[ERROR] Directory does not exists: %s' % directory

        if '.gitignore' in os.listdir(directory):
            with open(os.path.join(directory, '.gitignore')) as f:
                spec_src = f.read()
        else:
            spec_src = ''
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, spec_src.splitlines())

        # init zip file
        zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)

        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                if not spec.match_file(filepath):
                    zip_file.write(filepath, arcname=os.path.join('dist', os.path.relpath(filepath, directory)))

        # finally
        zip_file.close()

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


# noinspection PyPep8Naming
class DictDiffer:

    @staticmethod
    def diff(origin, modified):
        TYPE = 0
        FIELD = 1
        LIST = 2

        diffs = dict()
        dict_diff = list(dictdiffer.diff(origin, modified))
        for diff in dict_diff:
            field_pointer = DictDiffer.get_field_path(diffs=diffs, path=diff[FIELD], diff_type=diff[TYPE])
            if diff[TYPE] == 'add':
                for addition in diff[LIST]:
                    field_pointer[addition[0]] = addition[1]

            elif diff[TYPE] == 'remove':
                for deletion in diff[LIST]:
                    field_pointer[deletion[0]] = None

            elif diff[TYPE] == 'change':
                change = diff[LIST]
                field = diff[FIELD]
                if not isinstance(field, list):
                    field = field.split('.')
                field_pointer[field[-1]] = change[1]
        return diffs

    @staticmethod
    def get_field_path(diffs, path, diff_type):
        field_pointer = diffs
        if not isinstance(path, list):
            path = path.split('.')

        if len(path) > 1 or diff_type != 'change':
            for level in path:
                if diff_type == 'change' and level == path[-2]:
                    if level not in field_pointer:
                        field_pointer[level] = dict()
                    field_pointer = field_pointer[level]
                    break
                if level in field_pointer:
                    field_pointer = field_pointer[level]
                else:
                    field_pointer[level] = dict()
                    field_pointer = field_pointer[level]

        return field_pointer


class GitUtils:
    """
    Performs git related methods
    """

    @staticmethod
    def git_included(path):
        """
        Get only included git repo files based on .gitignore file

        :param path: directory - str
        :return: list()
        """
        included_files = list()

        try:
            p = subprocess.Popen(['git', '--git-dir', os.path.join(path, '.git'), 'ls-files'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            string_output = str(output, 'utf-8')
            included_files = string_output.split('\n')
        except Exception:
            logging.warning('Error getting git info for git repository in: {}'.format(path))
            # include all files
            for r, d, f in os.walk(path):
                for folder in d:
                    included_files.append(os.path.join(r, folder))

        return included_files

    @staticmethod
    def is_git_repo(path):
        """
        Check if directory is a git repo

        :param path: directory - str
        :return: True/False
        """
        try:
            p = subprocess.Popen(['git',  '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'status'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            if p.returncode != 0 and 'not a git repository' in str(err):
                response = False
            elif p.returncode == 0 and 'On branch' in str(output):
                response = True
            else:
                response = False
        except Exception:
            response = False
            logging.warning('Error getting git info for git repository in: {}'.format(path))
        return response

    @staticmethod
    def git_status(path):
        """
        Get git repository git status

        :param path: directory - str
        :return: String
        """
        status = dict()
        try:
            p = subprocess.Popen(['git',  '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'status'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            output_lines = str(output, 'utf-8').splitlines()
            branch = output_lines[0].replace('On branch ', '').strip()

            logs = GitUtils.git_log(path)
            status = {'branch': branch,
                      'commit_id': logs[0]['commit'],
                      'commit_author': logs[0]['Author'],
                      'commit_message': logs[0]['message']}
        except Exception:
            logging.warning('Error getting git info for git repository in: {}'.format(path))
        # try:
        #     repo = Repo(path)
        #     branch = repo.active_branch.__str__()
        #     commit_id = repo.active_branch.commit.__str__()
        #     commit_author = repo.active_branch.commit.author.__str__()
        #     commit_message = repo.active_branch.commit.message.__str__()
        # except Exception:
        #     status = dict()

        return status

    @staticmethod
    def git_log(path):
        """
        Get git repository git log

        :param path: directory - str
        :return: log as list()
        """
        log = list()
        try:
            log_limit = 100
            p = subprocess.Popen(['git',  '--git-dir', os.path.join(path, '.git'), '--work-tree', path, 'log'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, err = p.communicate()
            string_output = str(output, 'utf-8').split('\ncommit')
            for output in string_output:
                output = output.split('\n')
                if output[0].startswith('commit'):
                    output[0] = output[0].replace('commit', '')
                log_line = {
                    'commit': output[0].strip(),
                    'Author': output[1].replace('Author:', '').strip(),
                    'Date': output[2].replace('Date:', '').strip(),
                    'message': output[4].strip(),
                }
                log.append(log_line)
            log = log[0:log_limit]
        except Exception:
            logging.warning('Error getting git log for git repository in: {}'.format(path))

        # try:
        #     log = list()
        #     counter = 20
        #     repo = Repo(path)
        #     logs = repo.active_branch.log()
        #     for log_record in reversed(logs):
        #         if counter <= 0:
        #             break
        #         log_record = {
        #             'author': log_record.actor.__str__(),
        #             'message': log_record.message.__str__(),
        #             'commit_id': log_record.newhexsha.__str__(),
        #             'previous_commit_id': log_record.oldhexsha.__str__(),
        #             'time': datetime.datetime.fromtimestamp(log_record.time[0]).isoformat()
        #         }
        #         log.append(log_record)
        #         counter -= 1
        # except Exception:
        #     log = list()

        return log
