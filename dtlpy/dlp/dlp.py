#! /usr/bin/python3
import argparse
import logging
import jwt
import os
import subprocess
import traceback
import sys
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder.main import fuzzyfinder
import dtlpy as dlp
import shlex
from dtlpy import exceptions
import datetime
import threading

if os.name == "nt":
    # set encoding for windows printing
    os.environ["PYTHONIOENCODING"] = ":replace"

##########
# Logger #
##########
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dataloop.cli")
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)
keywords = dict()
param_suggestions = list()


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
        p_keywords.pop('shell')
    return p_keywords


class StoreDictKeyPair(argparse.Action):
    """
    Stores dict key pairs
    """

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            my_dict = {}
            for kv in values.split(";"):

                k, v = kv.split("=")
                if v.lower() in ["true", "false"]:
                    v = v.lower() == "true"
                logger.info("Input dict option: {}:{}".format(k, v))
                my_dict[k] = v
            setattr(namespace, self.dest, my_dict)
        except Exception:
            raise ValueError("Bad input options. must be KEY=VAL;KEY=VAL...")


class StateEnum:
    """
    State enum
    """
    START = 0
    RUNNING = 1
    DONE = 2
    CONTINUE = 3


thread_state = StateEnum.START


class DlpCompleter(Completer):
    """
    Autocomplete for dlp shell
    """
    # globals
    global keywords
    global param_suggestions
    global thread_state

    @staticmethod
    def get_param_suggestions(param, word_before_cursor, cmd):
        """
        Return parap suggestions
        :param param:
        :param word_before_cursor:
        :param cmd:
        :return:
        """
        # globals
        global keywords
        global param_suggestions
        global thread_state
        try:
            logging.disable(level=logging.ERROR)
            if thread_state in [StateEnum.RUNNING, StateEnum.DONE]:
                return
            else:
                if param == '--project-name':
                    thread_state = StateEnum.RUNNING
                    project_list = dlp.projects.list()
                    param_suggestions = [project.name for project in project_list]
                    thread_state = StateEnum.DONE
                elif param == '--dataset-name':
                    thread_state = StateEnum.RUNNING
                    if '--project-name' in cmd:
                        project = dlp.projects.get(project_name=cmd[cmd.index('--project-name') + 1])
                        dataset_list = project.datasets.list()
                    else:
                        if not isinstance(dlp.datasets.project, dlp.entities.Project):
                            dlp.datasets.project = dlp.projects.get()
                        dataset_list = dlp.datasets.list()
                    param_suggestions = [dataset.name for dataset in dataset_list]
                    thread_state = StateEnum.DONE
                elif param == '--local-path':
                    thread_state = StateEnum.CONTINUE
                    param = word_before_cursor.replace('"', '')
                    if param.endswith('/') or param.endswith('/'):
                        param = param[:-1]
                    if param == '':
                        param_suggestions = ['"{}'.format(os.path.join(os.path.expanduser('/'), directory)) for
                                             directory in
                                             os.listdir(os.path.join(os.path.expanduser('/')))
                                             if not directory.startswith('.')]
                    elif os.path.isdir(param):
                        dirs = os.listdir(param)
                        param_suggestions = ['"{}'.format(os.path.join(param, directory))
                                             for directory in dirs if not directory.startswith('.')]
                    elif os.path.isdir(os.path.join(os.path.join(os.path.expanduser('/')), param)):
                        dirs = os.listdir(os.path.join(os.path.join(os.path.expanduser('~')), param))
                        param_suggestions = ['"{}'.format(os.path.join(param, directory))
                                             for directory in dirs if not directory.startswith('.')]
                elif param in ['--annotation-options']:
                    thread_state = StateEnum.CONTINUE
                    param_suggestions = ['mask', 'json', 'instance', '"mask, json"',
                                         '"mask, instance"', '"json, instance"', '"mask, json, instance"']
                else:
                    thread_state = StateEnum.START
                    param_suggestions = list()
        except Exception:
            param_suggestions = list()
            thread_state = StateEnum.START
        finally:
            logging.disable(logging.NOTSET)

    def need_param(self, cmd, word_before_cursor):
        need_param = False
        bool_flags_list = ['--overwrite', '--no-relative-path',
                           '--with-text', '--deploy', '--not-items-folder', '--encode']

        if len(cmd) > 2 and cmd[-2].startswith('--') and word_before_cursor != '':
            need_param = not self.get_param(cmd=cmd, word_before_cursor=word_before_cursor) in bool_flags_list
        elif cmd[-1].startswith('-') and word_before_cursor == '':
            need_param = not self.get_param(cmd=cmd, word_before_cursor=word_before_cursor) in bool_flags_list

        return need_param

    @staticmethod
    def get_param(cmd, word_before_cursor):
        if word_before_cursor == '':
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
        global keywords
        global param_suggestions
        global thread_state

        # fix input
        cmd = " ".join(document.text.split())
        cmd = cmd.split(" ")

        # get current word
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # suggest keywords
        suggestions = list()
        if self.need_param(cmd=cmd, word_before_cursor=word_before_cursor):
            param = self.get_param(cmd=cmd, word_before_cursor=word_before_cursor)
            if thread_state in [StateEnum.START, StateEnum.CONTINUE]:
                if param in ['--project-name', '--dataset-name']:
                    thread = threading.Thread(
                        target=self.get_param_suggestions,
                        kwargs={
                            "param": param,
                            'word_before_cursor': word_before_cursor,
                            'cmd': cmd})
                    thread.start()
                else:
                    self.get_param_suggestions(param=param, word_before_cursor=word_before_cursor, cmd=cmd)
            if thread_state in [StateEnum.DONE, StateEnum.CONTINUE]:
                suggestions = param_suggestions
        elif len(cmd) == 1:
            thread_state = StateEnum.START
            if cmd[0] not in keywords.keys():
                suggestions = list(keywords.keys())
            elif isinstance(keywords[cmd[0]], list):
                suggestions = keywords[cmd[0]]
            elif isinstance(keywords[cmd[0]], dict):
                suggestions = list(keywords[cmd[0]].keys())
        elif len(cmd) >= 2:
            thread_state = StateEnum.START
            if cmd[0] not in keywords.keys():
                suggestions = list()
            elif isinstance(keywords[cmd[0]], list):
                suggestions = keywords[cmd[0]]
            elif isinstance(keywords[cmd[0]], dict):
                if cmd[1] in keywords[cmd[0]].keys():
                    suggestions = keywords[cmd[0]][cmd[1]]
                else:
                    suggestions = list(keywords[cmd[0]].keys())

        matches = fuzzyfinder(word_before_cursor, suggestions)
        for match in matches:
            yield Completion(match, start_position=-len(word_before_cursor))


def login_input():
    print(datetime.datetime.utcnow())
    print("email:")
    email = input()
    print(datetime.datetime.utcnow())
    print("password:")
    password = input()
    print()
    print()
    client_id = input()
    client_secret = input()
    return email, password, client_id, client_secret


def get_parser():
    """
    Build the parser for CLI
    :return: parser object
    """
    parser = argparse.ArgumentParser(
        description="CLI for Dataloop",
        formatter_class=argparse.RawTextHelpFormatter
    )

    ###############
    # sub parsers #
    ###############
    subparsers = parser.add_subparsers(dest="operation", help="supported operations")

    ########
    # shell #
    ########
    subparsers.add_parser("shell", help="Open interactive Dataloop shell")

    ########
    # Login #
    ########
    subparsers.add_parser("login", help="Login using web Auth0 interface")

    a = subparsers.add_parser("login-token", help="Login by passing a valid token")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-t", "--token", metavar='\b', help="valid token", required=True
    )

    a = subparsers.add_parser("login-secret", help="Login client id and secret")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-e", "--email", metavar='\b', help="user email", required=True)
    required.add_argument(
        "-p", "--password", metavar='\b', help="user password", required=True
    )
    required.add_argument(
        "-i", "--client-id", metavar='\b', help="client id", required=True
    )
    required.add_argument(
        "-s", "--client-secret", metavar='\b', help="client secret", required=True
    )

    ########
    # Init #
    ########
    subparsers.add_parser("init", help="Initialize a .dataloop context")

    ########
    # Help #
    ########
    subparsers.add_parser("help", help="Get help")

    ###########
    # version #
    ###########
    subparsers.add_parser("version", help="DTLPY SDK version")

    #######
    # API #
    #######
    subparser = subparsers.add_parser("api", help="Connection and environment")
    subparser_parser = subparser.add_subparsers(dest="api", help="gate operations")

    # ACTIONS #

    # info
    subparser_parser.add_parser("info", help="Print api information")

    # setenv
    a = subparser_parser.add_parser("setenv", help="Set platform environment")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-e", "--env", metavar='\b', help="working environment", required=True
    )

    # update
    a = subparser_parser.add_parser("update", help="Update dtlpy package")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-u",
        "--url",
        metavar='\b',
        help="package url",
        default="dtlpy",
    )

    ############
    # Projects #
    ############
    subparser = subparsers.add_parser("projects", help="Operations with projects")
    subparser_parser = subparser.add_subparsers(
        dest="projects", help="projects operations"
    )

    # ACTIONS #

    # list
    subparser_parser.add_parser("ls", help="List all projects")

    # create
    a = subparser_parser.add_parser("create", help="Create a new project")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-p", "--project-name", metavar='\b', help="project name")

    # checkout
    a = subparser_parser.add_parser("checkout", help="checkout a project")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-p", "--project-name", metavar='\b', help="project name")

    # open web
    a = subparser_parser.add_parser("web", help="Open in web browser")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', help="project name")

    ############
    # Datasets #
    ############
    subparser = subparsers.add_parser("datasets", help="Operations with datasets")
    subparser_parser = subparser.add_subparsers(dest="datasets", help="datasets operations")

    # ACTIONS #
    # open web
    a = subparser_parser.add_parser("web", help="Open in web browser")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', help="project name")
    optional.add_argument("-d", "--dataset-name", metavar='\b', help="dataset name")

    # list
    a = subparser_parser.add_parser("ls", help="List of datasets in project")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")

    # create
    a = subparser_parser.add_parser("create", help="Create a new dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-d", "--dataset-name", metavar='\b', help="dataset name", required=True)
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")

    # upload
    a = subparser_parser.add_parser("upload", help="Upload directory to dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-l", "--local-path", required=True, metavar='\b',
                          help="local path")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")
    optional.add_argument("-d", "--dataset-name", metavar='\b', default=None,
                          help="dataset name. Default taken from checked out (if checked out)")
    optional.add_argument("-r", "--remote-path", metavar='\b', default=None,
                          help="remote path to upload to. default: /")
    optional.add_argument("-f", "--file-types", metavar='\b', default=None,
                          help='Comma separated list of file types to upload, e.g ".jpg,.png". default: all')
    optional.add_argument("-nw", "--num-workers", metavar='\b', default=None,
                          help="num of threads workers")
    optional.add_argument("-lap", "--local-annotations-path", metavar='\b', default=None,
                          help="Path for local annotations to upload with items")
    optional.add_argument("-ow", "--overwrite", dest="overwrite", action='store_true', default=False,
                          help="Overwrite existing item")
    optional.add_argument("-rp", "--no-relative-path", dest="relative_path", action='store_false', default=True,
                          help="Upload flatten")

    # download
    a = subparser_parser.add_parser("download", help="Download dataset to a local directory")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")
    optional.add_argument("-d", "--dataset-name", metavar='\b', default=None,
                          help="dataset name. Default taken from checked out (if checked out)")
    optional.add_argument("-ao", "--annotation-options", metavar='\b',
                          help="which annotation to download. options: json,instance,mask", default=None)
    optional.add_argument("-r", "--remote-path", metavar='\b',
                          help="which annotation to download. options: json,instance,mask", default=None)
    optional.add_argument("-rp", "--no-relative-path", action='store_false', default=True,
                          help="download flatten")
    optional.add_argument("-ow", "--overwrite", action='store_true', default=False,
                          help="Overwrite existing item")
    optional.add_argument("-nw", "--num-workers", metavar='\b', default=None,
                          help="number of download workers")
    optional.add_argument("-t", "--not-items-folder", action='store_true', default=False,
                          help="Download WITHOUT 'items' folder")
    optional.add_argument("-wt", "--with-text", action='store_true', default=False,
                          help="Annotations will have text in mask")
    optional.add_argument("-th", "--thickness", metavar='\b', default="1",
                          help="Annotation line thickness")
    optional.add_argument("-l", "--local-path", metavar='\b', default=None,
                          help="local path")

    # checkout
    a = subparser_parser.add_parser("checkout", help="checkout a dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-d", "--dataset-name", metavar='\b', help="dataset name")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")

    #########
    # items #
    #########
    subparser = subparsers.add_parser("items", help="Operations with items")
    subparser_parser = subparser.add_subparsers(dest="items", help="items operations"
                                                )

    # ACTIONS #

    a = subparser_parser.add_parser("web", help="Open in web browser")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-r", "--remote-path", metavar='\b', help="remote path")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', help="project name")
    optional.add_argument("-d", "--dataset-name", metavar='\b', help="dataset name")

    # list
    a = subparser_parser.add_parser("ls", help="List of items in dataset")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")
    optional.add_argument("-d", "--dataset-name", metavar='\b', default=None,
                          help="dataset name. Default taken from checked out (if checked out)")
    optional.add_argument("-o", "--page", metavar='\b', help="page number (integer)", default=0)
    optional.add_argument("-r", "--remote-path", metavar='\b', help="remote path", default=None)

    # upload
    a = subparser_parser.add_parser("upload", help="Upload a single file")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-f", "--filename", metavar='\b', help="local filename to upload", required=True)
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")
    optional.add_argument("-d", "--dataset-name", metavar='\b', default=None,
                          help="dataset name. Default taken from checked out (if checked out)")
    optional.add_argument("-r", "--remote-path", metavar='\b', default="/",
                          help="remote path")

    ##########
    # videos #
    ##########
    subparser = subparsers.add_parser("videos", help="Operations with videos")
    subparser_parser = subparser.add_subparsers(dest="videos", help="videos operations")

    # ACTIONS #

    # play
    a = subparser_parser.add_parser("play", help="Play video")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-l",
        "--item-path",
        metavar='\b',
        default=None,
        help="Video remote path in platform. e.g /dogs/dog.mp4",
    )
    optional.add_argument(
        "-p",
        "--project-name",
        metavar='\b',
        default=None,
        help="project name. Default taken from checked out (if checked out)",
    )
    optional.add_argument(
        "-d",
        "--dataset-name",
        metavar='\b',
        default=None,
        help="dataset name. Default taken from checked out (if checked out)",
    )

    # upload
    a = subparser_parser.add_parser("upload", help="Upload a single video")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-f", "--filename", metavar='\b', help="local filename to upload", required=True
    )
    required.add_argument(
        "-p", "--project-name", metavar='\b', help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar='\b', help="dataset name", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-r", "--remote-path", metavar='\b', help="remote path", default="/"
    )

    # split video to chunks
    optional.add_argument(
        "-sc",
        "--split-chunks",
        metavar='\b',
        default=None,
        help="Video splitting parameter: Number of chunks to split",
    )
    optional.add_argument(
        "-ss",
        "--split-seconds",
        metavar='\b',
        default=None,
        help="Video splitting parameter: Seconds of each chuck",
    )
    optional.add_argument(
        "-st",
        "--split-times",
        metavar='\b',
        default=None,
        help="Video splitting parameter: List of seconds to split at. e.g 600,1800,2000",
    )
    # encode
    optional.add_argument(
        "-e",
        "--encode",
        action="store_true",
        default=False,
        help="encode video to mp4, remove bframes and upload",
    )

    ############
    # packages #
    ############
    subparser = subparsers.add_parser("packages", help="Operations with package")
    subparser_parser = subparser.add_subparsers(
        dest="packages", help="package operations"
    )

    # list
    a = subparser_parser.add_parser("ls", help="List all package")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-p",
        "--project-name",
        metavar='\b',
        default=None,
        help="project name. Default taken from checked out (if checked out)",
    )
    optional.add_argument(
        "-g", "--package-id", metavar='\b', help="list package's artifacts", default=None
    )

    # pack
    a = subparser_parser.add_parser("pack", help="Create a new package")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-g", "--package-name", metavar='\b', help="package name", required=True
    )
    required.add_argument(
        "-ds", "--description", metavar='\b', help="package description", required=True
    )
    required.add_argument(
        "-dir",
        "--directory",
        metavar='\b',
        help="Local path of packaeg script",
        required=True,
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-p",
        "--project-name",
        metavar='\b',
        default=None,
        help="project name. Default taken from checked out (if checked out)",
    )
    optional.add_argument(
        "-d",
        "--dataset-name",
        metavar='\b',
        default=None,
        help="dataset name. Default taken from checked out (if checked out)",
    )

    # delete
    a = subparser_parser.add_parser("delete", help="Delete a package forever...")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-d", "--dataset-name", metavar='\b', help="Dataset name", default=None
    )

    # unpack
    a = subparser_parser.add_parser("unpack", help="Download and unzip source code")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-g", "--package-id", metavar='\b', help="package id", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-p",
        "--project-name",
        metavar='\b',
        default=None,
        help="project name. Default taken from checked out (if checked out)",
    )
    optional.add_argument(
        "-d",
        "--directory",
        metavar='\b',
        default=os.getcwd(),
        help="source code directory. default: cwd",
    )

    ############
    # Plugins #
    ############
    subparser = subparsers.add_parser("plugins", help="Operations with plugins")
    subparser_parser = subparser.add_subparsers(
        dest="plugins", help="plugin operations"
    )

    # ACTIONS #

    # generate
    a = subparser_parser.add_parser(
        "generate", help="Create a boilerplate for a new plugin"
    )
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--plugin-name", metavar='\b', help="plugin name", required=True
    )

    # ls
    subparser_parser.add_parser("ls", help="List plugins")

    # push
    a = subparser_parser.add_parser("push", help="Push the plugin to the platform")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-d", "--deploy", dest="deploy", action='store_true', default=False,
                          help="Push and deploy")
    optional.add_argument("-r", "--revision", metavar='\b', default=None,
                          help="Revision to deploy if selected True")

    # invoke
    a = subparser_parser.add_parser(
        "invoke", help="Invoke plugin with arguments on remote"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-f",
        "--file",
        metavar='\b',
        default="./mock.json",
        help="Location of file with invocation inputs",
    )

    a = subparser_parser.add_parser("deploy", help="Deploy plugin on remote")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-r", "--revision", metavar='\b', help="plugin revision")

    _ = subparser_parser.add_parser(
        "status", help="Get the status of the plugins deployment"
    )
    # test
    subparser_parser.add_parser(
        "test", help="Tests that plugin locally using mock.json"
    )

    # checkout
    a = subparser_parser.add_parser("checkout", help="checkout a plugin")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-p", "--plugin-name", metavar='\b', help="plugin name")

    ############
    # Sessions #
    ############
    subparser = subparsers.add_parser("sessions", help="Operations with sessions")
    subparser_parser = subparser.add_subparsers(
        dest="sessions", help="Operations with sessions"
    )

    # ACTIONS #

    # list
    a = subparser_parser.add_parser("ls", help="List artifacts for session")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)", )
    optional.add_argument("-i", "--session-id", metavar='\b', help="List artifacts in session id")

    # tree
    a = subparser_parser.add_parser("tree", help="Print tree representation of sessions")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)", )

    # create
    a = subparser_parser.add_parser("create", help="Create a new Session")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-s", "--session-name", metavar='\b', help="session name", required=True)
    required.add_argument("-g", "--package-id", metavar='\b', help="source code", required=True)
    required.add_argument("-p", "--pipe-id", metavar='\b', help="pip to run", required=True)
    required.add_argument("-d", "--description", metavar='\b', help="session description", required=True)

    # upload
    a = subparser_parser.add_parser("upload", help="Add artifact to session")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-s", "--session-id", metavar='\b', help="session id", required=True)
    required.add_argument("-f", "--filename", metavar='\b', help="local filename to add", required=True)
    required.add_argument("-t", "--type", metavar='\b', help="artifact type", required=True)
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-d", "--description", metavar='\b', help="file description. default: ''", default="")

    # download
    a = subparser_parser.add_parser("download", help="Download artifact from session")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-s", "--session-id", metavar='\b', help="session id", required=True)
    required.add_argument("-a", "--artifact-id", metavar='\b', help="artifact id", required=True)
    required.add_argument("-d", "--local-path", metavar='\b', help="download to location", required=True)

    #########
    # Shell #
    #########
    # ls
    subparsers.add_parser("ls", help="List dirs")
    #
    # pwd
    subparsers.add_parser("pwd", help="Get cwd")

    # cd
    subparser = subparsers.add_parser("cd", help="Change dir")
    subparser.add_argument(dest='dir')

    # clear
    subparsers.add_parser("clear", help="Clear shell")

    ########
    # Exit #
    ########
    subparsers.add_parser("exit", help="Exit bash")

    return parser


def run(args, parser):
    global logger

    #########
    # Login #
    #########
    if args.operation == "login":
        dlp.login()
    elif args.operation == "login-token":
        dlp.login_token(args.token)
    elif args.operation == "login-secret":
        dlp.login_secret(
            email=args.email,
            password=args.password,
            client_id=args.client_id,
            client_secret=args.client_secret,
        )

    #########
    # Init  #
    #########
    elif args.operation == "init":
        dlp.init()

    ###########
    # Version #
    ###########
    elif args.operation == "version":
        print(datetime.datetime.utcnow())
        print("[INFO] Dataloop SDK Version: {}".format(dlp.__version__))

    ########
    # Help #
    ########
    elif args.operation == "help":
        print(datetime.datetime.utcnow())
        parser.print_help()

    #######
    # api #
    #######
    elif args.operation == "api":
        if args.api == "info":
            dlp.info()

        if args.api == "setenv":
            dlp.setenv(args.env)
            print(datetime.datetime.utcnow())
            print("[INFO] Platform environment: {}".format(dlp.environment()))

        if args.api == "update":
            url = args.url
            payload = jwt.decode(dlp.client_api.token, algorithms=['HS256'], verify=False)
            try:
                if 'admin' in payload['https://dataloop.ai/authorization']['roles']:
                    url = "https://storage.googleapis.com/dtlpy/dev/dtlpy-latest-py3-none-any.whl"
            except Exception:
                pass
            print(datetime.datetime.utcnow())
            print("[INFO] Update DTLPy from {}".format(url))
            print("[INFO] Installing using pip...")
            cmd = "pip install {} --upgrade".format(url)
            subprocess.Popen(cmd, shell=True)
            sys.exit(0)

    ############
    # Projects #
    ############
    elif args.operation == "projects":
        if args.projects == "ls":
            dlp.projects.list().print()
        elif args.projects == "web":
            dlp.projects.open_in_web(project_name=args.project_name)
        elif args.projects == "create":
            dlp.projects.create(args.project_name).print()
        elif args.projects == "checkout":
            dlp.projects.checkout(args.project_name)
        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp projects --help" for options')

    ############
    # Datasets #
    ############
    elif args.operation == "datasets":
        if args.datasets == "ls":
            project = dlp.projects.get(project_name=args.project_name)
            print(datetime.datetime.utcnow())
            project.datasets.list().print()

        elif args.datasets == "checkout":
            if args.project_name is not None:
                dlp.projects.checkout(args.project_name)
            dlp.datasets.checkout(args.dataset_name)

        elif args.datasets == "web":
            project = dlp.projects.get(project_name=args.project_name)
            project.datasets.open_in_web(dataset_name=args.dataset_name)

        elif args.datasets == "create":
            project = dlp.projects.get(project_name=args.project_name)
            print(datetime.datetime.utcnow())
            project.datasets.create(dataset_name=args.dataset_name).print()

        elif args.datasets == "upload":
            print(datetime.datetime.utcnow())
            print("[INFO] Uploading directory...")

            if isinstance(args.num_workers, str):
                args.num_workers = int(args.num_workers)
            if isinstance(args.file_types, str):
                args.file_types = args.file_types.split(",")
            project = dlp.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            dataset.items.upload(
                local_path=args.local_path,
                remote_path=args.remote_path,
                file_types=args.file_types,
                num_workers=args.num_workers,
                overwrite=args.overwrite,
                relative_path=not args.no_relative_path,
                local_annotations_path=args.local_annotations_path,
            )

        elif args.datasets == "download":
            print(datetime.datetime.utcnow())
            print("[INFO] Downloading dataset...")
            if isinstance(args.num_workers, str):
                args.num_workers = int(args.num_workers)
            project = dlp.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            annotation_options = None
            if args.annotation_options is not None:
                annotation_options = args.annotation_options.split(",")

            # create remote path filters
            filters = dlp.Filters()
            if args.remote_path is not None:
                remote_path = args.remote_path.split(",")
                if len(remote_path) > 1:
                    filters.add(
                        field="filename", values=args.remote_path, operator="in"
                    )
                else:
                    filters.add(
                        field="filename", values=args.remote_path, operator="glob"
                    )

            dataset.items.download(
                filters=filters,
                local_path=args.local_path,
                annotation_options=annotation_options,
                overwrite=args.overwrite,
                relative_path=not args.no_relative_path,
                num_workers=args.num_workers,
                with_text=args.with_text,
                thickness=int(args.thickness),
                to_items_folder=not args.not_items_folder,
            )
        else:
            print('Type "dlp datasets --help" for options')

    #########
    # items #
    #########
    elif args.operation == "items":
        if dlp.token_expired():
            print(datetime.datetime.utcnow())
            print("[ERROR] token expired, please login.")
            return

        if args.items == "ls":
            project = dlp.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            if isinstance(args.page, str):
                try:
                    args.page = int(args.page)
                except ValueError:
                    raise ValueError("Input --page must be integer")
            filters = dlp.Filters()
            if args.remote_path is None:
                filters = None  # default value
            elif isinstance(args.remote_path, list):
                filters.add(field="filename", values=args.remote_path, operator="in")
            else:
                filters.add(field="filename", values=args.remote_path)
            pages = dataset.items.list(filters=filters, page_offset=args.page)
            print(datetime.datetime.utcnow())
            pages.print()
            print("Displaying page %d/%d" % (args.page + 1, pages.total_pages_count))

        elif args.items == "web":
            project = dlp.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            dataset.items.open_in_web(filepath=args.remote_path)

        elif args.items == "upload":
            project = dlp.projects.get(project_name=args.project_name)
            project.datasets.get(dataset_name=args.dataset_name).items.upload(
                local_path=args.filename, remote_path=args.remote_path
            )

        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp items --help" for options')

    ##########
    # Videos #
    ##########
    elif args.operation == "videos":
        if dlp.token_expired():
            print(datetime.datetime.utcnow())
            print("[ERROR] token expired, please login.")
            return

        if args.videos == "play":
            from dtlpy.utilities.videos.video_player import VideoPlayer

            VideoPlayer(
                item_filepath=args.item_path,
                dataset_name=args.dataset_name,
                project_name=args.project_name,
            )

        elif args.videos == "upload":
            if (
                    (args.split_chunks is not None)
                    or (args.split_seconds is not None)
                    or (args.split_times is not None)
            ):
                # upload with split
                if isinstance(args.split_chunks, str):
                    args.split_chunks = int(args.split_chunks)
                if isinstance(args.split_seconds, str):
                    args.split_seconds = int(args.split_seconds)
                if isinstance(args.split_times, str):
                    args.split_times = [int(sec) for sec in args.split_times.split(",")]
                dlp.utilities.videos.Videos.split_and_upload(
                    project_name=args.project_name,
                    dataset_name=args.dataset_name,
                    filepath=args.filename,
                    remote_path=args.remote_path,
                    split_chunks=args.split_chunks,
                    split_seconds=args.split_seconds,
                    split_pairs=args.split_times,
                )
        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp videos --help" for options')

    ############
    # Packages #
    ############
    elif args.operation == "packages":
        if dlp.token_expired():
            print(datetime.datetime.utcnow())
            print("[ERROR] token expired, please login.")
            return

        if args.packages == "ls":
            if args.project_name is not None:
                # list project's packages
                print(datetime.datetime.utcnow())
                dlp.projects.get(project_name=args.project_name).packages.list().print()
            elif args.package_id is not None:
                # list package artifacts
                if args.project_name is None:
                    logger.error("Please provide package project name")
                    raise dlp.PlatformException(
                        "400", "Please provide package project name"
                    )
                project = dlp.projects.get(project_name=args.project_name)
                print(datetime.datetime.utcnow())
                project.packages.get(package_id=args.package_id).print()
            else:
                # list user's package
                projects = dlp.projects.list()
                for project in projects:
                    print(datetime.datetime.utcnow())
                    project.packages.list().print()

        elif args.packages == "pack":
            if args.project_name is not None:
                if args.dataset_name is not None:
                    project = dlp.projects.get(args.project_name)
                    project.packages._dataset = project.datasets.get(
                        dataset_name=args.dataset_name
                    )
                    project.packages.pack(
                        directory=args.directory,
                        name=args.package_name,
                        description=args.description,
                    )
                else:
                    dlp.projects.get(args.project_name).packages.pack(
                        directory=args.directory,
                        name=args.package_name,
                        description=args.description,
                    )
            else:
                logger.error("Please provide project name")
                raise dlp.PlatformException("400", "Please provide project name")

        elif args.packages == "delete":
            if args.project_name is not None:
                dlp.projects.get(args.project_name).packages.delete(
                    package_id=args.package_id
                )
            else:
                logger.error("Please provide project name")
                raise dlp.PlatformException("400", "Please provide project name")

        elif args.packages == "unpack":
            print(datetime.datetime.utcnow())
            print("Unpacking source code...")
            dlp.projects.get(args.project_name).packages.unpack(
                package_id=args.package_id, local_directory=args.directory
            )

        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp packages --help" for options')

    ############
    # Plugins  #
    ############
    elif args.operation == "plugins":
        if dlp.token_expired():
            print(datetime.datetime.utcnow())
            print("[ERROR] token expired, please login.")
            return

        if args.plugins == "generate":
            dlp.plugins.generate_local_plugin(name=args.plugin_name)

        elif args.plugins == "ls":
            dlp.plugins.list()

        elif args.plugins == "checkout":
            dlp.plugins.checkout(args.plugin_name)
            print(datetime.datetime.utcnow())

        elif args.plugins == "push":
            dlp.plugins.push_local_plugin(deploy=args.deploy, revision=args.revision)
            print(datetime.datetime.utcnow())
            print("Successfully pushed the plugin to remote")
            
        elif args.plugins == "test":
            print(datetime.datetime.utcnow())
            # dlp.plugins.test_local_plugin()
            os.chdir('./src')
            cmd = 'python -m debug'
            os.system(cmd)
            os.chdir('..')

        elif args.plugins == "invoke":
            print(datetime.datetime.utcnow())
            print(dlp.plugins.invoke_plugin(args.file))

        elif args.plugins == "deploy":
            print(datetime.datetime.utcnow())
            deployment_id = dlp.plugins.deploy_plugin_from_folder(args.revision)
            print(
                "Successfully deployed the plugin, deployment id is: %s" % deployment_id
            )

        elif args.plugins == "status":
            dlp.plugins.get_status_from_folder()
        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp plugins --help" for options')

    ############
    # Sessions #
    ############
    elif args.operation == "sessions":

        if args.sessions == "ls":
            if args.session_id is not None:
                print(datetime.datetime.utcnow())
                dlp.sessions.get(session_id=args.session_id).print()
            elif args.project_name is not None:
                print(datetime.datetime.utcnow())
                dlp.projects.get(project_name=args.project_name).sessions.list().print()
            else:
                print(datetime.datetime.utcnow())
                print("[ERROR] need to input session-id or project-name.")

        elif args.sessions == "tree":
            dlp.projects.get(project_name=args.project_name).sessions.tree()

        elif args.sessions == "create":
            dlp.projects.get(project_name=args.project_name).sessions.create(
                session_name=args.session_name,
                dataset_name=args.dataset_name,
                pipe_id=args.pipe_id,
                package_id=args.package_id,
            )

        elif args.sessions == "upload":
            dlp.sessions.get(session_id=args.session_id).artifacts.upload(
                filepath=args.filename,
                artifact_type=args.type,
                description=args.description,
            )

        elif args.sessions == "download":
            dlp.sessions.get(session_id=args.session_id).artifacts.download(
                artifact_type=args.artifact_type, local_directory=args.local_dir
            )
        else:
            print(datetime.datetime.utcnow())
            print('Type "dlp sessions --help" for options')

    #######
    # pwd #
    #######
    elif args.operation == "pwd":
        print(os.getcwd())

    ######
    # cd #
    ######
    elif args.operation == "cd":
        directory = args.dir
        if directory == '..':
            directory = os.path.split(os.getcwd())[0]
        os.chdir(directory)
        print(os.getcwd())

    ######
    # ls #
    ######
    elif args.operation == "ls":
        print(os.getcwd())
        dirs = os.listdir(os.getcwd())
        import pprint

        pp = pprint.PrettyPrinter(indent=3)
        pp.pprint(dirs)

    #########
    # clear #
    #########
    elif args.operation == "clear":
        if os.name == "nt":
            os.system('cls')
        else:
            os.system('clear')

    ###############
    # Catch typos #
    ###############
    elif args.operation == "project":
        print(datetime.datetime.utcnow())
        print('dlp: "project" is not an dlp command. Did you mean "projects"?')
    elif args.operation == "dataset":
        print(datetime.datetime.utcnow())
        print('dlp: "dataset" is not an dlp command. Did you mean "datasets"?')
    elif args.operation == "item":
        print(datetime.datetime.utcnow())
        print('dlp: "item" is not an dlp command. Did you mean "items"?')
    elif args.operation == "session":
        print(datetime.datetime.utcnow())
        print('dlp: "session" is not an dlp command. Did you mean "sessions"?')
    elif args.operation == "package":
        print(datetime.datetime.utcnow())
        print('dlp: "package" is not an dlp command. Did you mean "packages"?')

    #########################
    # Catch rest of options #
    #########################
    else:
        print(datetime.datetime.utcnow())
        if args.operation:
            print('dlp: "%s" is not an dlp command' % args.operation)
        print('See "dlp --help" for options')


def dlp_exit():
    print(datetime.datetime.utcnow())
    print("Goodbye ;)")
    sys.exit(0)


def main():
    try:
        global keywords
        # parse
        parser = get_parser()
        keywords = get_parser_tree(parser=parser)
        args = parser.parse_args()
        history_file = os.path.join(os.getcwd(), ".history.txt")

        if args.operation == "shell":
            #######################
            # Open Dataloop shell #
            #######################
            while True:
                text = prompt(
                    u"dl>",
                    history=FileHistory(history_file),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=DlpCompleter(),
                )
                try:
                    if text in ["-h", "--help"]:
                        text = "help"
                    parser = get_parser()
                    args = parser.parse_args(shlex.split(text))
                    if args.operation == "exit":
                        dlp_exit()
                    else:
                        run(args=args, parser=parser)
                except exceptions.TokenExpired:
                    print(datetime.datetime.utcnow())
                    print("[ERROR] token expired, please login.")
                    continue
                except SystemExit as e:
                    # exit
                    if e.code == 0:
                        if "-h" in text or "--help" in text:
                            continue
                        else:
                            sys.exit(0)
                    # error
                    else:
                        print(datetime.datetime.utcnow())
                        print('"{command}" is not a valid command'.format(command=text))
                        continue
                except Exception as e:
                    print(datetime.datetime.utcnow())
                    print(traceback.format_exc())
                    print(e)
                    continue

        else:
            ######################
            # Run single command #
            ######################
            try:
                run(args=args, parser=parser)
                sys.exit(0)
            except exceptions.TokenExpired:
                print(datetime.datetime.utcnow())
                print("[ERROR] token expired, please login.")
                sys.exit(1)
            except Exception as e:
                print(datetime.datetime.utcnow())
                print(traceback.format_exc())
                print(e)
                sys.exit(1)
    except KeyboardInterrupt:
        dlp_exit()
    except Exception:
        print(traceback.format_exc())
        dlp_exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(datetime.datetime.utcnow())
        print("[ERROR]\t%s" % err)
    print("Dataloop.ai CLI. Type dlp --help for options")
