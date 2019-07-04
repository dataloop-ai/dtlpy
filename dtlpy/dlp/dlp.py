#! /usr/bin/python3
import argparse
import logging
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


dl_keywords = [
    "login",
    "login-token",
    "login-secret",
    "init",
    "api",
    "projects",
    "datasets",
    "files",
    "videos",
    "packages",
    "plugins",
    "checkout",
    "sessions",
    "pipes",
    "exit",
]
flags = {
    "login-token": ["-t", "--token"],
    "login-secret": [
        "-e",
        "--email",
        "-p",
        "--password",
        "-i",
        "--client-id",
        "-s",
        "--client-secret",
    ],
    "setenv": ["-e", "--env"],
    "update": ["-u", "--url"],
    "create": [
        "-p",
        "--project-name",
        "-d",
        "--dataset-name",
        "-g",
        "--package-name",
        "-d",
        "--description",
        "--session-name",
        "-g",
        "--package-id",
        "-p",
        "--pipe-id",
    ],
    "ls": [
        "-p",
        "--project-name",
        "-d",
        "--dataset-name",
        "-o",
        "--page",
        "-r",
        "--remote-path",
        "-g",
        "--package-id",
        "-i",
        "--session-id",
    ],
    "upload": [
        "-p",
        "--project-name",
        "-d",
        "--dataset-name",
        "-l",
        "--local-path",
        "-r",
        "--remote-path",
        "-f",
        "--file-types",
        "-nw",
        "--num-workers",
        "-u",
        "--upload-options",
        "-f",
        "--filename",
        "-t",
        "--item-type",
        "-sc",
        "--split-chunks",
        "-ss",
        "--split-seconds",
        "-st",
        "--split-times",
        "-e",
        "--encode",
        "-s",
        "--session-id",
        "-t",
        "--type",
        "-d",
        "--description",
    ],
    "download": [
        "-p",
        "--project-name",
        "-d",
        "--dataset-name",
        "-r",
        "--remote-path",
        "-ao",
        "--annotation_options",
        "-do",
        "--download_options",
        "-di",
        "--dl_img",
        "-nw",
        "--num_workers",
        "-l",
        "--local-path",
        "-s",
        "--session-id",
        "-a",
        "--artifact-id",
        "-d",
    ],
    "play": ["-l", "--item_path", "-d", "--dataset_name", "-p", "--project-name"],
    "pack": ["-d", "--directory", "-g", "--package-id"],
    "unpack": ["-g", "--package-id", "-d", "--directory"],
    "tree": ["-p", "--project-name", "-s"],
    "run": [
        "-s",
        "--session-id",
        "-ps",
        "--prev-session-id",
        "--project-name",
        "--dataset-name",
        "--pipe-id",
        "--package-id",
        "--session-name",
        "--config-filename",
        "-r",
        "--remote-run",
        "-i",
        "--input",
    ],
}
commands = {
    "api": ["info", "setenv", "update"],
    "projects": ["ls", "create"],
    "datasets": ["ls", "create", "upload", "download"],
    "files": ["ls", "upload"],
    "videos": ["play"],
    "packages": ["ls", "create", "pack", "unpack"],
    "plugins": ["generate", "push", "test", "status"],
    "checkout": ["projects", "dataset", "plugin"],
    "sessions": ["ls", "tree", "create", "upload", "download"],
    "pipes": ["run"],
}

class DlpCompleter(Completer):
    def get_completions(self, document, complete_event):
        # fix input
        cmd = " ".join(document.text.split())
        cmd = cmd.split(" ")

        # get current word
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        keywords = dl_keywords

        if len(cmd) == 1:
            if cmd[0] in flags:
                keywords = flags[cmd[0]]
            elif cmd[0] in commands:
                keywords = commands[cmd[0]]
        elif len(cmd) >= 2:
            if cmd[0] in flags:
                keywords = flags[cmd[0]]
            elif cmd[0] in commands:
                if cmd[1] in flags:
                    keywords = flags[cmd[1]]
                else:
                    keywords = commands[cmd[0]]

        matches = fuzzyfinder(word_before_cursor, keywords)
        for match in matches:
            yield Completion(match, start_position=-len(word_before_cursor))


def login_input():
    print("email:")
    email = input()
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
        description="CLI for Dataloop", formatter_class=argparse.RawTextHelpFormatter
    )

    ###############
    # sub parsers #
    ###############
    subparsers = parser.add_subparsers(dest="operation", help="supported operations")

    ########
    # Login #
    ########
    subparsers.add_parser("login", help="Login using web Auth0 interface")

    a = subparsers.add_parser("login-token", help="Login by passing a valid token")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-t", "--token", metavar="", help="valid token", required=True
    )

    a = subparsers.add_parser("login-secret", help="Login client id and secret")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-e", "--email", metavar="", help="user email", required=True)
    required.add_argument(
        "-p", "--password", metavar="", help="user password", required=True
    )
    required.add_argument(
        "-i", "--client-id", metavar="", help="client id", required=True
    )
    required.add_argument(
        "-s", "--client-secret", metavar="", help="client secret", required=True
    )

    ########
    # Init #
    ########
    subparsers.add_parser("init", help="Initialize a .dataloop context")

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
        "-e", "--env", metavar="", help="working environment", required=True
    )

    # update
    a = subparser_parser.add_parser("update", help="Update dtlpy package")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-u",
        "--url",
        metavar="",
        help="package url",
        default="https://storage.googleapis.com/dtlpy/dev/dtlpy-1.0-py3-none-any.whl",
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
    required.add_argument("-p", "--project-name", metavar="", help="project name")

    ############
    # Datasets #
    ############
    subparser = subparsers.add_parser("datasets", help="Operations with datasets")
    subparser_parser = subparser.add_subparsers(
        dest="datasets", help="datasets operations"
    )

    # ACTIONS #

    # list
    a = subparser_parser.add_parser("ls", help="List of datasets in project")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )

    # create
    a = subparser_parser.add_parser("create", help="Create a new dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar="", help="dataset name", required=True
    )

    # upload
    a = subparser_parser.add_parser("upload", help="Upload directory to dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar="", help="dataset name", required=True
    )
    required.add_argument(
        "-l", "--local-path", metavar="", help="local path", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-r",
        "--remote-path",
        metavar="",
        help="remote path to upload to. default: /",
        default="/",
    )
    optional.add_argument(
        "-f",
        "--file-types",
        metavar="",
        help='Comma separated list of file types to upload, e.g ".jpg,.png". default: all',
        default=None,
    )
    optional.add_argument(
        "-nw", "--num-workers", metavar="", help="num of threads workers", default=None
    )
    optional.add_argument(
        "-u",
        "--upload-options",
        metavar="",
        help='"overwrite" or "merge"',
        default="merge",
    )

    # download
    a = subparser_parser.add_parser(
        "download", help="Download dataset to a local directory"
    )
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar="", help="dataset name", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-r",
        "--remote-path",
        metavar="",
        help="remote path to download from. default: /",
        default="/",
    )
    optional.add_argument(
        "-ao",
        "--annotation_options",
        metavar="",
        help="which annotation to download. options: json,instance,mask",
        default="",
    )
    optional.add_argument(
        "-do",
        "--download_options",
        metavar="",
        help="download options CSV : merge/overwrite,relative-path/absolute-path",
        default="",
    )
    optional.add_argument(
        "-di",
        "--dl_img",
        help="download image or not",
        action="store_true",
        default=True,
    )
    optional.add_argument(
        "-nw",
        "--num_workers",
        metavar="",
        help="number of download workers",
        default=None,
    )
    # optional.add_argument('-o', '--opacity', metavar='', type=float,
    #                       help='opacity when marking image. range:[0,1]. default: 1', default=1)
    optional.add_argument(
        "-l", "--local-path", metavar="", help="local path", default=None
    )

    ###################
    # files and items #
    ###################
    subparser = subparsers.add_parser("files", help="Operations with files and items")
    subparser_parser = subparser.add_subparsers(
        dest="files", help="datasets files and items"
    )

    # ACTIONS #

    # list
    a = subparser_parser.add_parser("ls", help="List of files in dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar="", help="dataset name", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-o", "--page", metavar="", help="page number (integer)", default=0
    )
    optional.add_argument(
        "-r", "--remote-path", metavar="", help="remote path", default="/"
    )

    # upload
    a = subparser_parser.add_parser("upload", help="Upload a single file")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-f", "--filename", metavar="", help="local filename to upload", required=True
    )
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    required.add_argument(
        "-d", "--dataset-name", metavar="", help="dataset name", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-r", "--remote-path", metavar="", help="remote path", default="/"
    )
    optional.add_argument(
        "-t", "--item-type", metavar="", help='"folder", "file"', default="file"
    )

    # split video to chunks
    optional.add_argument(
        "-sc",
        "--split-chunks",
        metavar="",
        help="Video splitting parameter: Number of chunks to split",
        default=None,
    )
    optional.add_argument(
        "-ss",
        "--split-seconds",
        metavar="",
        help="Video splitting parameter: Seconds of each chuck",
        default=None,
    )
    optional.add_argument(
        "-st",
        "--split-times",
        metavar="",
        help="Video splitting parameter: List of seconds to split at. e.g 600,1800,2000",
        default=None,
    )
    # encode
    optional.add_argument(
        "-e",
        "--encode",
        help="encode video to mp4, remove bframes and upload",
        action="store_true",
        default=False,
    )
    # # disassemble
    # optional.add_argument('-ds', '--disass', help='disassemble according to fps and upload', action='store_true',
    #                       default=False)
    # optional.add_argument('-rt', '--fps', metavar='', help='disassemble frame rate (number of frames per second',
    #                       default=None)

    ##########
    # videos #
    ##########
    subparser = subparsers.add_parser("videos", help="Operations with videos")
    subparser_parser = subparser.add_subparsers(dest="videos", help="videos operations")

    # ACTIONS #

    # play
    a = subparser_parser.add_parser("play", help="List all package")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-l",
        "--item_path",
        metavar="",
        help="Video remote path in platform. e.g /dogs/dog.mp4",
        default=None,
    )
    optional.add_argument(
        "-d", "--dataset_name", metavar="", help="Dataset name", default=None
    )
    optional.add_argument(
        "-p", "--project-name", metavar="", help="Project name", default=None
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
        metavar="",
        help="list a project's package",
        default=None,
    )
    optional.add_argument(
        "-g", "--package-id", metavar="", help="list package's artifacts", default=None
    )

    # create
    a = subparser_parser.add_parser("create", help="Create a new package")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-g", "--package-name", metavar="", help="package name", required=True
    )
    required.add_argument(
        "-d", "--description", metavar="", help="package description", required=True
    )

    a = subparser_parser.add_parser("delete", help="Delete a package forever...")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-g", "--package-id", metavar="", help="package id", required=True
    )

    # pack
    a = subparser_parser.add_parser(
        "pack", help="Create a new package and add source code"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-d",
        "--directory",
        metavar="",
        help="source code directory. default: cwd",
        default=os.getcwd(),
    )

    # unpack
    a = subparser_parser.add_parser("unpack", help="Download and unzip source code")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-g", "--package-id", metavar="", help="package id", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-d",
        "--directory",
        metavar="",
        help="source code directory. default: cwd",
        default=os.getcwd(),
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
    subparser_parser.add_parser(
        "generate", help="Create a boilerplate for a new plugin"
    )

    # push
    subparser_parser.add_parser("push", help="Push the plugin to the platform")

    # test
    subparser_parser.add_parser(
        "test", help="Tests that plugin locally using mock.json"
    )

    # status
    subparser_parser.add_parser("status", help="?")

    ############
    # Checkout #
    ############
    subparser = subparsers.add_parser(
        "checkout", help="Operations with setting the state of the cli"
    )
    subparser_parser = subparser.add_subparsers(
        dest="checkout", help="package operations"
    )

    a = subparser_parser.add_parser("project", help="Checks out to a different project")
    required = a.add_argument_group("required named arguments")
    required.add_argument("project", metavar="Project", type=str, help="project name")

    a = subparser_parser.add_parser("dataset", help="Checks out to a different dataset")
    required = a.add_argument_group("required named arguments")
    required.add_argument("dataset", metavar="Dataset", type=str, help="dataset name")

    a = subparser_parser.add_parser("plugin", help="Checks out to a different plugin")
    required = a.add_argument_group("required named arguments")
    required.add_argument("plugin", metavar="Plugin", type=str, help="plugin name")

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
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-i", "--session-id", metavar="", help="List artifacts in session id"
    )

    # tree
    a = subparser_parser.add_parser(
        "tree", help="Print tree representation of sessions"
    )
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-p", "--project-name", metavar="", help="project name", required=True
    )

    # create
    a = subparser_parser.add_parser("create", help="Create a new Session")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-s", "--session-name", metavar="", help="session name", required=True
    )
    required.add_argument(
        "-g", "--package-id", metavar="", help="source code", required=True
    )
    required.add_argument(
        "-p", "--pipe-id", metavar="", help="pip to run", required=True
    )
    required.add_argument(
        "-d", "--description", metavar="", help="session description", required=True
    )

    # upload
    a = subparser_parser.add_parser("upload", help="Add artifact to session")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-s", "--session-id", metavar="", help="session id", required=True
    )
    required.add_argument(
        "-f", "--filename", metavar="", help="local filename to add", required=True
    )
    required.add_argument(
        "-t", "--type", metavar="", help="artifact type", required=True
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-d",
        "--description",
        metavar="",
        help="file description. default: ''",
        default="",
    )

    # download
    a = subparser_parser.add_parser("download", help="Download artifact from session")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-s", "--session-id", metavar="", help="session id", required=True
    )
    required.add_argument(
        "-a", "--artifact-id", metavar="", help="artifact id", required=True
    )
    required.add_argument(
        "-d", "--local-path", metavar="", help="download to location", required=True
    )

    #########
    # Pipes #
    #########
    subparser = subparsers.add_parser("pipes", help="Operations with pipes")
    subparser_parser = subparser.add_subparsers(dest="pipes", help="Pipes operations")
    subparser_parser.add_parser("ls", help="List all pipes.")

    # ACTIONS #

    # run
    a = subparser_parser.add_parser("run", help="Run a pipe")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument(
        "-s", "--session-id", metavar="", help="Current session id to run"
    )
    optional.add_argument(
        "-ps",
        "--prev-session-id",
        metavar="",
        help="Create new session with revious session id to start from",
    )
    optional.add_argument(
        "--project-name", metavar="", help="project name. default: None", default=None
    )
    optional.add_argument(
        "--dataset-name", metavar="", help="dataset name. default: None", default=None
    )
    optional.add_argument(
        "--pipe-id", metavar="", help="pipe id. default: None", default=None
    )
    optional.add_argument(
        "--package-id", metavar="", help="package id. default: None", default=None
    )
    optional.add_argument(
        "--session-name",
        metavar="",
        help="new session name. default: None",
        default=None,
    )
    optional.add_argument(
        "--config-filename",
        metavar="",
        help="new configuration filename. default: None",
        default=None,
    )
    optional.add_argument(
        "-r",
        "--remote-run",
        action="store_true",
        help="Run session remotely",
        default=False,
    )

    ####
    # inputs
    optional.add_argument(
        "-i",
        "--input",
        action="append",
        type=lambda kv: kv.split("="),
        dest="pipe_kwargs",
        help='Input args for pipe. Use: ["--input key1=val1 --input key2=val2"]',
    )

    ########
    # Exit #
    ########

    subparsers.add_parser("exit", help="Exit bash")

    return parser


def main():
    ##########
    # Logger #
    ##########
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("dataloop.cli")
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)

    # while True:
        # text = prompt(
        #     u"dl>",
        #     history=FileHistory(".history.txt"),
        #     auto_suggest=AutoSuggestFromHistory(),
        #     completer=DlpCompleter(),
        # )

    parser = get_parser()
    args = parser.parse_args()
    # try:
    #     args = parser.parse_args(text.split(" "))
    # except:
    #     continue

    ###############
    # Run command #
    ###############
    try:
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
            from ..utilities.plugin_bootstraping.dataloop_folder_initializator import (
                init_dataloop_folder,
            )

            init_dataloop_folder()

        #######
        # api #
        #######
        elif args.operation == "api":
            if args.api == "info":
                print("environment")
                print(dlp.environment())
                print("token")
                print(dlp.token())

            if args.api == "setenv":
                dlp.setenv(args.env)
                print("[INFO] Platform environment: %s" % dlp.environment())

            if args.api == "update":
                url = args.url
                print("[INFO] Update DTLPy from %s" % url)
                print("[INFO] Installing using pip...")
                cmd = "pip install %s --upgrade " % url
                p = subprocess.Popen(cmd, shell=True)
                return

        ############
        # Projects #
        ############
        elif args.operation == "projects":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.projects == "ls":
                dlp.projects.list().print()

            elif args.projects == "create":
                dlp.projects.create(args.project_name).print()

            else:
                print('Type "dlp projects --help" for options')

        ############
        # Datasets #
        ############
        elif args.operation == "datasets":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.datasets == "ls":
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception(
                        "Project wasnt found. name: %s" % args.project_name
                    )
                    raise ValueError(
                        "Project wasnt found. name: %s" % args.project_name
                    )
                project.datasets.list().print()

            elif args.datasets == "create":
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception(
                        "Project was not found. name: %s" % args.project_name
                    )
                    raise ValueError(
                        "Project was not found. name: %s" % args.project_name
                    )
                project.datasets.create(dataset_name=args.dataset_name).print()

            elif args.datasets == "upload":
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
                    filet_ypes=args.file_types,
                    num_workers=args.num_workers,
                    upload_options=args.upload_options,
                )

            elif args.datasets == "download":
                print("[INFO] Downloading dataset...")
                if isinstance(args.num_workers, str):
                    args.num_workers = int(args.num_workers)
                project = dlp.projects.get(project_name=args.project_name)
                dataset = project.datasets.get(dataset_name=args.dataset_name)
                download_options = {}
                if len(args.download_options) > 0:
                    do_arr = args.download_options.split(",")
                    if len(do_arr) > 0 and do_arr[0] == "overwrite":
                        download_options["overwrite"] = True
                        print("[INFO] Overwrite mode")
                    if len(do_arr) > 1 and do_arr[1] == "relative-path":
                        download_options["relative_path"] = True
                        print("[INFO] relative path")
                annotation_options = list()
                if len(args.annotation_options) > 0:
                    annotation_options = args.annotation_options.split(",")
                dataset.items.download(
                    filters=dlp.Filters(filenames=[args.remote_path]),
                    local_path=args.local_path,
                    annotation_options=annotation_options,
                    download_options=download_options,
                    num_workers=args.num_workers,
                )
            else:
                print('Type "dlp datasets --help" for options')

        ###################
        # Files and items #
        ###################
        elif args.operation == "files":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.files == "ls":
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    msg = "Project was not found. name: %s" % args.project_name
                    raise ValueError(msg)
                dataset = project.datasets.get(dataset_name=args.dataset_name)
                if isinstance(args.page, str):
                    try:
                        args.page = int(args.page)
                    except ValueError:
                        raise ValueError("Input --page must be integer")
                pages = dataset.items.list(
                    filters=dlp.Filters(filenames=[args.remote_path]),
                    page_offset=args.page,
                )
                pages.print()
                print("Displaying page %d/%d" % (args.page + 1, pages.pages_count))

            elif args.files == "upload":
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception(
                        "Project wasnt found. name: %s" % args.project_name
                    )
                    raise ValueError(
                        "Project wasnt found. name: %s" % args.project_name
                    )
                project.datasets.get(dataset_name=args.dataset_name).items.upload(
                    filepath=args.filename, remote_path=args.remote_path
                )

            else:
                print('Type "dlp files --help" for options')

        ##########
        # Videos #
        ##########
        elif args.operation == "videos":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.videos == "play":
                from dtlpy.utilities.videos.video_player import VideoPlayer

                VideoPlayer(
                    item_filepath=args.item_path,
                    dataset_name=args.dataset_name,
                    project_name=args.project_name,
                )
            #
            # elif args.videos == 'upload':
            #     if (args.split_chunks is not None) or \
            #             (args.split_seconds is not None) or \
            #             (args.split_times is not None):
            #         # upload with split
            #         if isinstance(args.split_chunks, str):
            #             args.split_chunks = int(args.split_chunks)
            #         if isinstance(args.split_seconds, str):
            #             args.split_seconds = int(args.split_seconds)
            #         if isinstance(args.split_times, str):
            #             args.split_times = [int(sec) for sec in args.split_times.split(',')]
            #         r.videos_split_and_upload(project_name=args.project_name,
            #                                   dataset_name=args.dataset_name,
            #                                   item=args.filename,
            #                                   remote_path=args.remote_path,
            #                                   split_chunks=args.split_chunks,
            #                                   split_seconds=args.split_seconds,
            #                                   split_times=args.split_times
            #                                   )
            #     elif args.encode:
            #         r.videos_encode_and_upload(project_name=args.project_name,
            #                                    dataset_name=args.dataset_name,
            #                                    item=args.filename,
            #                                    remote_path=args.remote_path)

            else:
                print('Type "dlp files --help" for options')

        ############
        # Packages #
        ############
        elif args.operation == "packages":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.packages == "ls":
                if args.project_name is not None:
                    # list project's packages
                    dlp.projects.get(
                        project_name=args.project_name
                    ).packages.list().print()
                elif args.package_id is not None:
                    # list package artifacts
                    dlp.packages.get(package_id=args.package_id).print()
                else:
                    # list user's package
                    dlp.packages.list().print()

            elif args.packages == "create":
                if args.project_name is not None:
                    dlp.projects.get(args.project_name).packages.create(
                        name=args.package_name, description=args.description
                    )
                else:
                    dlp.packages.create(
                        name=args.package_name, description=args.description
                    )

            elif args.packages == "delete":
                if args.project_name is not None:
                    dlp.projects.get(args.project_name).packages.delete(
                        package_id=args.package_id
                    )
                else:
                    dlp.packages.delete(package_id=args.package_id)

            elif args.packages == "pack":
                print("Packing source: %s" % args.directory)
                dlp.packages.pack(
                    directory=args.directory,
                    name=args.name,
                    description=args.description,
                )
            elif args.packages == "unpack":
                print("Unpacking source code...")
                dlp.packages.unpack(
                    package_id=args.package_id, local_directory=args.directory
                )

            else:
                print('Type "dlp packages --help" for options')

        ############
        # Plugins  #
        ############
        elif args.operation == "plugins":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.plugins == "generate":
                dlp.plugins.generate_local_plugin()

            elif args.plugins == "push":
                dlp.plugins.push_local_plugin()

            elif args.plugins == "test":
                dlp.plugins.test_local_plugin()

            elif args.plugins == "status":
                dlp.plugins.get_local_plugin_status()

        ############
        # Checkout #
        ############
        elif args.operation == "checkout":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.checkout == "project":
                from dtlpy.utilities.checkout_manager import checkout_project

                checkout_project(dlp, args.project)
            elif args.checkout == "dataset":
                from dtlpy.utilities.checkout_manager import checkout_dataset

                checkout_dataset(dlp, args.dataset)
            elif args.checkout == "plugin":
                from dtlpy.utilities.checkout_manager import checkout_plugin

                checkout_plugin(args.plugin)

            else:
                print('Type "dlp packages --help" for options')

        ############
        # Sessions #
        ############
        elif args.operation == "sessions":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.sessions == "ls":
                if args.session_id is not None:
                    dlp.sessions.get(session_id=args.session_id).print()
                elif args.project_name is not None:
                    dlp.projects.get(
                        project_name=args.project_name
                    ).sessions.list().print()
                else:
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
                print('Type "dlp sessions --help" for options')

        #########
        # Pipes #
        #########
        elif args.operation == "pipes":
            if dlp.token_expired():
                print("[ERROR] token expired, please login.")
                return

            if args.pipes == "ls":
                dlp.pipelines.list().print()

            elif args.pipes == "run":
                # get input parameters
                kwargs = dict()
                if args.pipe_kwargs is not None:
                    kwargs = dict(args.pipe_kwargs)

                if args.prev_session_id is not None:
                    dlp.sessions.run_from_previous(
                        prev_session_id=args.prev_session_id,
                        config_filename=args.config_filename,
                        input_params=kwargs,
                        pipe_id=args.pipe_id,
                        project_name=args.project_name,
                        dataset_name=args.dataset_name,
                        session_name=args.session_name,
                        package_id=args.package_id,
                        remote_run=args.remote_run,
                    )

                elif args.session_id is not None:
                    dlp.sessions.run(
                        session_id=args.session_id,
                        input_params=kwargs,
                        remote_run=args.remote_run,
                    )
                else:
                    print('[INFO] input missing. "session-id" or "prev-session-id"')
            else:
                print('Type "dlp pipes --help" for options')
        elif args.operation == "exit":
            print("Goodbye ;)")
            sys.exit(0)
        ###############
        # Catch typos #
        ###############
        elif args.operation == "project":
            print('dlp: "project" is not an dlp command. Did you mean "projects"?')
        elif args.operation == "dataset":
            print('dlp: "dataset" is not an dlp command. Did you mean "datasets"?')
        elif args.operation == "item":
            print('dlp: "file" is not an dlp command. Did you mean "files"?')
        elif args.operation == "session":
            print('dlp: "session" is not an dlp command. Did you mean "sessions"?')
        elif args.operation == "package":
            print('dlp: "package" is not an dlp command. Did you mean "packages"?')
        elif args.operation == "pipe":
            print('dlp: "pipe" is not an dlp command. Did you mean "pipes"?')

        #########################
        # Catch rest of options #
        #########################
        else:
            if args.operation:
                print('dlp: "%s" is not an dlp command' % args.operation)
            print('See "dlp --help" for options')

    except Exception as e:
        print(traceback.format_exc())
        print(e)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("[ERROR]\t%s" % err)
    print("Dataloop.ai CLI. Type dlp --help for options")

