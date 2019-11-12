import argparse


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

    ##################
    # Checkout state #
    ##################
    subparsers.add_parser("checkout-state", help="Print checkout state")

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
    required.add_argument("-e", "--env", metavar='\b', help="working environment", required=True)

    # upgrade
    a = subparser_parser.add_parser("upgrade", help="Update dtlpy package")
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
    required.add_argument("-c", "--checkout", action='store_true', default=False, help="checkout the new project")

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
    required.add_argument("-c", "--checkout", action='store_true', default=False, help="checkout the new dataset")

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
    subparser_parser = subparser.add_subparsers(dest="items", help="items operations")

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
    optional.add_argument("-t", "--type", metavar='\b', help="Item type", default=None)

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

    # download
    a = subparser_parser.add_parser("download", help="Download dataset to a local directory")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", metavar='\b', default=None,
                          help="project name. Default taken from checked out (if checked out)")
    optional.add_argument("-d", "--dataset-name", metavar='\b', default=None,
                          help="dataset name. Default taken from checked out (if checked out)")
    optional.add_argument("-ao", "--annotation-options", metavar='\b',
                          help="which annotation to download. options: json,instance,mask", default=None)
    optional.add_argument("-r", "--remote-path", metavar='\b', default=None,
                          help="remote path to upload to. default: /")
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
    optional.add_argument("-wb", "--without-binaries", action='store_true', default=False,
                          help="Don't download item binaries")

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

    ###############
    # Deployments #
    ###############
    subparser = subparsers.add_parser("deployments", help="Operations with deployments")
    subparser_parser = subparser.add_subparsers(
        dest="deployments", help="deployments operations"
    )

    # ACTIONS #

    # generate
    a = subparser_parser.add_parser(
        "generate", help="Generate deployment.json file"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-l", "--local-path", dest="local_path", default=None,
                          help="path to deployment.json file")

    # deploy
    a = subparser_parser.add_parser(
        "deploy", help="Deploy deployment from deployment.json file"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-l", "--local-path", dest="local_path", default=None,
                          help="path to deployment.json file")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # tear-down
    a = subparser_parser.add_parser(
        "tear-down", help="tear-down deployment of deployment.json file"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-l", "--local-path", dest="local_path", default=None,
                          help="path to deployment.json file")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # ls
    a = subparser_parser.add_parser(
        "ls", help="List project's deployments"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # log
    a = subparser_parser.add_parser(
        "log", help="Get deployments log"
    )
    required = a.add_argument_group("required named arguments")
    required.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name", required=True)
    required.add_argument("-d", "--deployment-name", dest="deployment_name", default=None,
                          help="Project name", required=True)

    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-t", "--start", dest="start", default=None,
                          help="Log start time")

    ###########
    # Plugins #
    ###########
    subparser = subparsers.add_parser("plugins", help="Operations with plugins")
    subparser_parser = subparser.add_subparsers(
        dest="plugins", help="plugin operations"
    )

    # ACTIONS #

    # deploy
    a = subparser_parser.add_parser(
        "deploy", help="Deploy plugin from local directory"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-df", "--deployment-file", dest="deployment_file", default=None,
                          help="Path to deployment file")

    # generate
    a = subparser_parser.add_parser(
        "generate", help="Create a boilerplate for a new plugin"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-p", "--plugin-name", dest="plugin_name", default=None,
                          help="Plugin name")

    # ls
    a = subparser_parser.add_parser("ls", help="List plugins")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # push
    a = subparser_parser.add_parser("push", help="Create plugin in platform")

    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-src", "--src-path", metavar='\b', default=None,
                          help="Revision to deploy if selected True")
    optional.add_argument("-pkg", "--package-id", metavar='\b', default=None,
                          help="Revision to deploy if selected True")
    optional.add_argument("-pr", "--project-name", metavar='\b', default=None,
                          help="Project name")
    optional.add_argument("-p", "--plugin-name", metavar='\b', default=None,
                          help="Plugin name")

    # test
    a = subparser_parser.add_parser(
        "test", help="Tests that plugin locally using mock.json"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-c", "--concurrency", metavar='\b', default=None,
                          help="Revision to deploy if selected True")

    # checkout
    a = subparser_parser.add_parser("checkout", help="checkout a plugin")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-p", "--plugin-name", metavar='\b', help="plugin name")

    #########
    # Shell #
    #########
    # ls
    subparsers.add_parser("ls", help="List directories")
    #
    # pwd
    subparsers.add_parser("pwd", help="Get current working directory")

    # cd
    subparser = subparsers.add_parser("cd", help="Change current working directory")
    subparser.add_argument(dest='dir')

    # mkdir
    subparser = subparsers.add_parser("mkdir", help="Make directory")
    subparser.add_argument(dest='name')

    # clear
    subparsers.add_parser("clear", help="Clear shell")

    ########
    # Exit #
    ########
    subparsers.add_parser("exit", help="Exit interactive shell")

    return parser
