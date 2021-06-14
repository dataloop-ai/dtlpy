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
    # shell #
    ########
    a = subparsers.add_parser("upgrade", help="Update dtlpy package")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-u", "--url", metavar='\b', help="Package url. default 'dtlpy'", default=None)

    ##################
    # Login / Logout #
    ##################
    subparsers.add_parser("logout", help="Logout")

    subparsers.add_parser("login", help="Login using web Auth0 interface")

    a = subparsers.add_parser("login-token", help="Login by passing a valid token")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-t", "--token", metavar='\b', help="valid token", required=True
    )

    a = subparsers.add_parser("login-secret", help="Login client id and secret")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-e", "--email", metavar='\b', help="user email", required=False, default=None
    )
    required.add_argument(
        "-p", "--password", metavar='\b', help="user password", required=False, default=None
    )
    required.add_argument(
        "-i", "--client-id", metavar='\b', help="client id", required=False, default=None
    )
    required.add_argument(
        "-s", "--client-secret", metavar='\b', help="client secret", required=False, default=None
    )

    a = subparsers.add_parser("login-m2m", help="Login client id and secret")
    required = a.add_argument_group("required named arguments")
    required.add_argument(
        "-e", "--email", metavar='\b', help="user email", required=False, default=None
    )
    required.add_argument(
        "-p", "--password", metavar='\b', help="user password", required=False, default=None
    )
    required.add_argument(
        "-i", "--client-id", metavar='\b', help="client id", required=False, default=None
    )
    required.add_argument(
        "-s", "--client-secret", metavar='\b', help="client secret", required=False, default=None
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
    parser.add_argument("-v", "--version", action="store_true", help="dtlpy version")
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
    optional.add_argument("-c", "--checkout", action='store_true', default=False, help="checkout the new dataset")

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
    optional.add_argument("-aft", "--annotation-filter-type", metavar='\b',
                          help="annotation type filter when downloading annotations. "
                               "options: box,segment,binary etc", default=None)
    optional.add_argument("-afl", "--annotation-filter-label", metavar='\b',
                          help="labels filter when downloading annotations.", default=None)
    optional.add_argument("-r", "--remote-path", metavar='\b', default=None,
                          help="remote path to upload to. default: /")
    optional.add_argument("-ow", "--overwrite", action='store_true', default=False,
                          help="Overwrite existing item")
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

    ############
    # Services #
    ############
    subparser = subparsers.add_parser("services", help="Operations with services")
    subparser_parser = subparser.add_subparsers(dest="services", help="services operations")

    # ACTIONS #

    # execute
    a = subparser_parser.add_parser("execute", help="Create an execution")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-f", "--function-name", dest="function_name", default=None,
                          help="which function to run")
    optional.add_argument("-s", "--service-name", dest="service_name", default=None,
                          help="which service to run")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-as", "--async", dest="asynchronous", default=True, action='store_false',
                          help="Async execution ")
    optional.add_argument("-i", "--item-id", dest="item_id", default=None,
                          help="Item input")
    optional.add_argument("-d", "--dataset-id", dest="dataset_id", default=None,
                          help="Dataset input")
    optional.add_argument("-a", "--annotation-id", dest="annotation_id", default=None,
                          help="Annotation input")
    optional.add_argument("-in", "--inputs", dest="inputs", default='{}',
                          help="Dictionary string input")

    # tear-down
    a = subparser_parser.add_parser(
        "tear-down", help="tear-down service of service.json file"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-l", "--local-path", dest="local_path", default=None,
                          help="path to service.json file")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # ls
    a = subparser_parser.add_parser("ls", help="List project's services")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")

    # log
    a = subparser_parser.add_parser("log", help="Get services log")
    optional = a.add_argument_group("required named arguments")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-f", "--service-name", dest="service_name", default=None,
                          help="Project name")
    optional.add_argument("-t", "--start", dest="start", default=None,
                          help="Log start time")

    # delete
    a = subparser_parser.add_parser("delete", help="Delete Service")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-f", "--service-name", dest="service_name", default=None,
                          help="Service name")
    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")

    ############
    # Triggers #
    ############
    subparser = subparsers.add_parser("triggers", help="Operations with triggers")
    subparser_parser = subparser.add_subparsers(dest="triggers", help="triggers operations")

    # ACTIONS #
    # create
    a = subparser_parser.add_parser("create", help="Create a Service Trigger")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-r", "--resource", dest="resource",
                          help="Resource name", required=True)
    required.add_argument("-a", "--actions", dest="actions", help="Actions", required=True)

    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")
    optional.add_argument("-f", "--service-name", dest="service_name",
                          help="Service name", default=None)
    optional.add_argument("-n", "--name", dest="name",
                          help="Trigger name", default=None)
    optional.add_argument("-fl", "--filters", dest="filters", default='{}',
                          help="Json filter")
    optional.add_argument("-fn", "--function-name", dest="function_name", default='run',
                          help="Function name")

    # delete
    a = subparser_parser.add_parser("delete", help="Delete Trigger")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-t", "--trigger-name", dest="trigger_name", default=None,
                          help="Trigger name", required=True)

    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-f", "--service-name", dest="service_name", default=None,
                          help="Service name")
    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")

    a = subparser_parser.add_parser("ls", help="List triggers")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-pr", "--project-name", dest="project_name", default=None,
                          help="Project name")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")
    optional.add_argument("-s", "--service-name", dest="service_name", default=None,
                          help="Service name")

    ############
    # Deploy   #
    ############
    # subparsers.add_parser("deploy", help="Login using web Auth0 interface")

    a = subparsers.add_parser("deploy", help="deploy with json file")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-f", dest="json_file", default=None,
                          help="Path to json file")
    required.add_argument("-p", dest="project_name", default=None,
                          help="Project name")

    ############
    # Generate   #
    ############
    # subparsers.add_parser("deploy", help="Login using web Auth0 interface")

    a = subparsers.add_parser("generate", help="generate a json file")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("--option", dest="package_type", default=None,
                          help="cataluge of examples")
    optional.add_argument("-p", "--package-name", dest="package_name", default=None,
                          help="Package name")

    ############
    # packages #
    ############
    subparser = subparsers.add_parser("packages", help="Operations with packages")
    subparser_parser = subparser.add_subparsers(
        dest="packages", help="package operations"
    )

    # ACTIONS #
    # ls
    a = subparser_parser.add_parser("ls", help="List packages")
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")

    # push
    a = subparser_parser.add_parser("push", help="Create package in platform")

    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-src", "--src-path", metavar='\b', default=None,
                          help="Revision to deploy if selected True")
    optional.add_argument("-cid", "--codebase-id", metavar='\b', default=None,
                          help="Revision to deploy if selected True")
    optional.add_argument("-pr", "--project-name", metavar='\b', default=None,
                          help="Project name")
    optional.add_argument("-p", "--package-name", metavar='\b', default=None,
                          help="Package name")

    # test
    a = subparser_parser.add_parser(
        "test", help="Tests that Package locally using mock.json"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-c", "--concurrency", metavar='\b', default=10,
                          help="Revision to deploy if selected True")
    optional.add_argument("-f", "--function-name", metavar='\b', default='run',
                          help="Function to test")
    # checkout
    a = subparser_parser.add_parser("checkout", help="checkout a package")
    required = a.add_argument_group("required named arguments")
    required.add_argument("-p", "--package-name", metavar='\b', help="package name")

    # delete
    a = subparser_parser.add_parser(
        "delete", help="Delete Package"
    )
    optional = a.add_argument_group("optional named arguments")
    optional.add_argument("-pkg", "--package-name", dest="package_name", default=None,
                          help="Package name")

    optional.add_argument("-p", "--project-name", dest="project_name", default=None,
                          help="Project name")

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
