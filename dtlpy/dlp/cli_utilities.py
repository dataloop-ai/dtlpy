from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import History
from fuzzyfinder.main import fuzzyfinder
import csv
import threading
import os
import datetime
import logging


class StateEnum:
    """
    State enum
    """
    START = 0
    RUNNING = 1
    DONE = 2
    CONTINUE = 3


def get_parser_tree(parser):
    """
    Creates parser tree for autocomplete
    :param parser: parser
    :return: parser tree
    """
    if parser._subparsers is None:
        p_keywords = list()
        for param in parser._option_string_actions:
            if param.startswith('--'):
                p_keywords.append(param)
    else:
        p_keywords = dict()
        subparsers = parser._subparsers._group_actions[0].choices
        for sub_parser in subparsers:
            p_keywords[sub_parser] = get_parser_tree(subparsers[sub_parser])
    if 'shell' in p_keywords:
        # noinspection PyTypeChecker
        p_keywords.pop('shell')
    return p_keywords


class FileHistory(History):
    """
    :class:`.History` class that stores all strings in a file.
    """

    def __init__(self, filename):
        self.filename = filename
        super(FileHistory, self).__init__()
        self.to_hide = ['password', 'secret']

    def load_history_strings(self):
        strings = []
        lines = []

        def add():
            if lines:
                # Join and drop trailing newline.
                string = ''.join(lines)[:-1]
                hide = any(field in string for field in self.to_hide)
                if not hide:
                    strings.append(string)

        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                for line in f:
                    line = line.decode('utf-8')

                    if line.startswith('+'):
                        lines.append(line[1:])
                    else:
                        add()
                        lines = []

                add()

        # Reverse the order, because newest items have to go first.
        return reversed(strings)

    def store_string(self, string):
        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# %s\n' % datetime.datetime.utcnow())
            for line in string.split('\n'):
                hide = any(field in line for field in self.to_hide)
                if not hide:
                    write('+%s\n' % line)


class DlpCompleter(Completer):
    """
    Autocomplete for dlp shell
    """

    def __init__(self, keywords, dlp):
        super(DlpCompleter, self).__init__()
        # globals
        self.keywords = keywords
        self.param_suggestions = list()
        self.thread_state = StateEnum.START
        self.dlp = dlp

    def get_param_suggestions(self, param, word_before_cursor, cmd):
        """
        Return parap suggestions
        :param param:
        :param word_before_cursor:
        :param cmd:
        :return:
        """
        prev_state = logging.root.manager.disable
        try:
            logging.root.manager.disable = logging.ERROR
            if self.thread_state in [StateEnum.RUNNING, StateEnum.DONE]:
                return
            else:
                if param == '--project-name':
                    self.thread_state = StateEnum.RUNNING
                    project_list = self.dlp.projects.list()
                    self.param_suggestions = ['"{}'.format(project.name) for project in project_list]
                    self.thread_state = StateEnum.DONE

                elif param == '--package-name':
                    self.thread_state = StateEnum.RUNNING
                    if '--project-name' in cmd:
                        project = self.dlp.projects.get(
                            project_name=cmd[cmd.index('--project-name') + 1].replace('"', ''))
                        packages = project.packages
                    else:
                        packages = self.dlp.packages
                    package_list = packages.list()
                    self.param_suggestions = ['"{}'.format(package.name) for package in package_list]
                    self.thread_state = StateEnum.DONE

                elif param == '--service-name':
                    self.thread_state = StateEnum.RUNNING
                    if '--package-name' in cmd:
                        package = self.dlp.packages.get(
                            package_name=cmd[cmd.index('--package-name') + 1].replace('"', ''))
                        services = package.services
                    elif '--project-name' in cmd:
                        project = self.dlp.projects.get(
                            project_name=cmd[cmd.index('--project-name') + 1].replace('"', ''))
                        services = project.services
                    else:
                        services = self.dlp.services

                    service_list = services.list()
                    self.param_suggestions = ['"{}'.format(service.name) for service in service_list]
                    self.thread_state = StateEnum.DONE

                elif param == '--trigger-name':
                    self.thread_state = StateEnum.RUNNING
                    if '--service-name' in cmd:
                        service = self.dlp.services.get(
                            service_name=cmd[cmd.index('--service-name') + 1].replace('"', ''))
                        triggers = service.triggers
                    elif '--package-name' in cmd:
                        package = self.dlp.packages.get(
                            package_name=cmd[cmd.index('--package-name') + 1].replace('"', ''))
                        triggers = package.services
                    elif '--project-name' in cmd:
                        project = self.dlp.projects.get(
                            project_name=cmd[cmd.index('--project-name') + 1].replace('"', ''))
                        triggers = project.services
                    else:
                        triggers = self.dlp.services

                    trigger_list = triggers.list()
                    self.param_suggestions = ['"{}'.format(trigger.name) for trigger in trigger_list]
                    self.thread_state = StateEnum.DONE

                elif param == '--dataset-name':
                    self.thread_state = StateEnum.RUNNING
                    if '--project-name' in cmd:
                        project = self.dlp.projects.get(
                            project_name=cmd[cmd.index('--project-name') + 1].replace('"', ''))
                        dataset_list = project.datasets.list()
                    else:
                        project = self.dlp.projects.get()
                        dataset_list = project.datasets.list()
                    self.param_suggestions = ['"{}'.format(dataset.name) for dataset in dataset_list]
                    self.thread_state = StateEnum.DONE

                elif param == '--remote-path':
                    self.thread_state = StateEnum.RUNNING
                    if '--project-name' in cmd:
                        project = self.dlp.projects.get(
                            project_name=cmd[cmd.index('--project-name') + 1].replace('"', ''))
                    else:
                        project = self.dlp.projects.get()
                    if '--dataset-name' in cmd:
                        dataset = project.datasets.get(
                            dataset_name=cmd[cmd.index('--dataset-name') + 1].replace('"', ''))
                    else:
                        dataset = self.dlp.datasets.get()
                    self.param_suggestions = dataset.directory_tree.dir_names
                    with_quotation = ['"{}'.format(directory) for directory in dataset.directory_tree.dir_names]
                    self.param_suggestions += with_quotation
                    self.thread_state = StateEnum.DONE

                elif param in ['--local-path', '--local-annotations-path', '--service-file']:
                    self.thread_state = StateEnum.CONTINUE
                    param = word_before_cursor.replace('"', '')
                    if param == '':
                        param, path = os.path.splitdrive(os.getcwd())
                        param += os.path.sep
                        self.param_suggestions = ['"{}'.format(os.path.join(param, directory))
                                                  for directory in os.listdir(param)
                                                  if not directory.startswith('.')]
                    elif os.path.isdir(os.path.dirname(param)):
                        base_dir = os.path.dirname(param)
                        self.param_suggestions = ['"{}'.format(os.path.join(base_dir, directory))
                                                  for directory in os.listdir(base_dir)
                                                  if (not directory.startswith('.') and
                                                      param in '"{}'.format(os.path.join(base_dir, directory)))]

                elif param in ['--annotation-options']:
                    self.thread_state = StateEnum.CONTINUE
                    self.param_suggestions = ['mask', 'json', 'instance', '"mask, json"',
                                              '"mask, instance"', '"json, instance"', '"mask, json, instance"']

                elif param in ['--actions']:
                    self.thread_state = StateEnum.CONTINUE
                    self.param_suggestions = ['Created', 'Updated', 'Deleted', '"Created, Updated"',
                                              '"Created, Deleted"', '"Updated, Deleted"', '"Created, Updated, Deleted"']

                elif param in ['--resource']:
                    self.thread_state = StateEnum.CONTINUE
                    self.param_suggestions = [value for key, value in self.dlp.TriggerResource.__dict__.items() if
                                              not key.startswith('_')]

                elif param in ['cd']:
                    self.thread_state = StateEnum.CONTINUE
                    if word_before_cursor != '' and os.path.isdir(os.path.join(os.getcwd(), word_before_cursor)):
                        self.param_suggestions = [os.path.join(word_before_cursor, directory)
                                                  for directory in
                                                  os.listdir(os.path.join(os.getcwd(), word_before_cursor))
                                                  if os.path.isdir(
                                os.path.join(os.getcwd(), word_before_cursor, directory))]
                    else:
                        self.param_suggestions = [directory for directory in os.listdir(os.getcwd()) if
                                                  os.path.isdir(directory)]

                else:
                    self.thread_state = StateEnum.START
                    self.param_suggestions = list()
        except Exception:
            self.param_suggestions = list()
            self.thread_state = StateEnum.START
        finally:
            logging.root.manager.disable = prev_state

    def need_param(self, cmd, word_before_cursor):
        need_param = False

        try:
            bool_flags_list = ['--overwrite', '--with-text', '--deploy', '--not-items-folder', '--encode',
                               '--without-binaries']

            if len(cmd) > 2 and cmd[-2].startswith('--') and word_before_cursor != '':
                need_param = self.get_param(cmd=cmd, word_before_cursor=word_before_cursor) not in bool_flags_list
            elif cmd[-1].startswith('-') and word_before_cursor == '':
                need_param = self.get_param(cmd=cmd, word_before_cursor=word_before_cursor) not in bool_flags_list
            elif cmd[0] in ['cd']:
                need_param = True
        except Exception:
            need_param = False

        return need_param

    @staticmethod
    def get_param(cmd, word_before_cursor):
        if word_before_cursor == '' or len(cmd) < 2:
            param = cmd[-1]
        else:
            param = cmd[-2]

        return param

    def get_completions(self, document, complete_event):
        """
        Get command completion
        :param document:
        :param complete_event:
        :return:
        """
        # fix input
        cmd = next(csv.reader([" ".join(document.text.split())], delimiter=' '))

        # get current word
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # suggest keywords
        suggestions = list()
        if self.need_param(cmd=cmd, word_before_cursor=word_before_cursor):
            param = self.get_param(cmd=cmd, word_before_cursor=word_before_cursor)
            if self.thread_state in [StateEnum.START, StateEnum.CONTINUE]:
                if param in ['--project-name', '--dataset-name', '--remote-path']:
                    thread = threading.Thread(target=self.get_param_suggestions,
                                              kwargs={"param": param,
                                                      'word_before_cursor': word_before_cursor,
                                                      'cmd': cmd})
                    thread.daemon = True
                    thread.start()

                else:
                    self.get_param_suggestions(param=param, word_before_cursor=word_before_cursor, cmd=cmd)
            if self.thread_state in [StateEnum.DONE, StateEnum.CONTINUE]:
                suggestions = self.param_suggestions
        elif len(cmd) == 0:
            suggestions = list(self.keywords.keys())
        elif len(cmd) == 1:
            self.thread_state = StateEnum.START
            if cmd[0] not in self.keywords.keys() and cmd[0] != '':
                if not word_before_cursor == '':
                    suggestions = list(self.keywords.keys())
            elif cmd[0] == '':
                suggestions = list(self.keywords.keys())
            elif isinstance(self.keywords[cmd[0]], list):
                suggestions = self.keywords[cmd[0]]
            elif isinstance(self.keywords[cmd[0]], dict):
                suggestions = list(self.keywords[cmd[0]].keys())
        elif len(cmd) >= 2:
            self.thread_state = StateEnum.START
            if cmd[0] not in self.keywords.keys():
                suggestions = list()
            elif isinstance(self.keywords[cmd[0]], list):
                suggestions = self.keywords[cmd[0]]
            elif isinstance(self.keywords[cmd[0]], dict):
                if cmd[1] in self.keywords[cmd[0]].keys():
                    suggestions = self.keywords[cmd[0]][cmd[1]]
                else:
                    suggestions = list(self.keywords[cmd[0]].keys())

        matches = fuzzyfinder(word_before_cursor, suggestions)
        for match in matches:
            yield Completion(match, start_position=-len(word_before_cursor))
