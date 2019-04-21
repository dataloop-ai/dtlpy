#! /usr/bin/python3
import argparse
import logging
import os
import subprocess
import traceback

from dtlpy import platform_interface


def login_input():
    print('email:')
    email = input()
    print('password:')
    password = input()
    print()
    print()
    client_id = input()
    client_secret = input()
    return email, password, client_id, client_secret


# def prefix_completion(r, endpoint, prefix):
#     if endpoint == 'models':
#         verbose = r.verbose
#         r.verbose = False
#         r.modelsGet()
#         r.verbose = verbose
#         models = r.last_response.json()
#         model_id = list()
#         for model in models:
#             if model['id'].startswith(prefix):
#                 model_id.append(model['id'])
#         assert not len(model_id) == 0, '[ERROR] no model_id found with prefix: %s' % prefix
#         assert not len(model_id) > 1, '[ERROR] more than one model_id found with prefix: %s' % prefix
#         return model_id[0]


def get_parser():
    """
    Build the parser for CLI
    :return: parser object
    """
    parser = argparse.ArgumentParser(description='CLI for Dataloop', formatter_class=argparse.RawTextHelpFormatter)

    ###############
    # sub parsers #
    ###############
    subparsers = parser.add_subparsers(dest='operation', help='supported operations')

    ########
    # Login #
    ########
    subparsers.add_parser('login', help='Login using web Auth0 interface')

    a = subparsers.add_parser('login-token', help='Login by passing a valid token')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-t', '--token', metavar='', help='valid token', required=True)

    a = subparsers.add_parser('login-secret', help='Login client id and secret')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-e', '--email', metavar='', help='user email', required=True)
    required.add_argument('-p', '--password', metavar='', help='user password', required=True)
    required.add_argument('-i', '--client-id', metavar='', help='client id', required=True)
    required.add_argument('-s', '--client-secret', metavar='', help='client secret', required=True)

    #######
    # API #
    #######
    subparser = subparsers.add_parser('api', help='Connection and environment')
    subparser_parser = subparser.add_subparsers(dest='api', help='gate operations')

    subparser_parser.add_parser('info', help='Print api information')

    a = subparser_parser.add_parser('setenv', help='Set platform environment')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-e', '--env', metavar='', help='working environment', required=True)

    a = subparser_parser.add_parser('update', help='Update dtlpy package')
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-u', '--url', metavar='', help='package url',
                          default='https://storage.googleapis.com/dtlpy/dev/dtlpy-1.0-py3-none-any.whl')

    ############
    # Projects #
    ############
    subparser = subparsers.add_parser('projects', help='Operations with projects')
    subparser_parser = subparser.add_subparsers(dest='projects', help='projects operations')

    # actions
    subparser_parser.add_parser('ls', help='List all projects')

    a = subparser_parser.add_parser('create', help='Create a new project')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name')

    ############
    # Datasets #
    ############
    subparser = subparsers.add_parser('datasets', help='Operations with datasets')
    subparser_parser = subparser.add_subparsers(dest='datasets', help='datasets operations')

    # actions
    a = subparser_parser.add_parser('ls', help='List of datasets in project')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)

    a = subparser_parser.add_parser('create', help='Create a new dataset')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    required.add_argument('-d', '--dataset-name', metavar='', help='dataset name', required=True)

    a = subparser_parser.add_parser('upload', help='Upload directory to dataset')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    required.add_argument('-d', '--dataset-name', metavar='', help='dataset name', required=True)
    required.add_argument('-l', '--local-path', metavar='', help='local path', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-r', '--remote-path', metavar='', help='remote path to upload to. default: /', default='/')
    optional.add_argument('-f', '--file-types', metavar='',
                          help='Comma separated list of file types to upload, e.g ".jpg,.png". default: all', default=None)
    optional.add_argument('-nw', '--num-workers', metavar='', help='num of threads workers', default=None)
    optional.add_argument('-u', '--upload-options', metavar='', help='"overwrite" or "merge"', default='merge')

    a = subparser_parser.add_parser('download', help='Download dataset to a local directory')
    # TODO
    # error when too much args - sphinx argparser fails
    # check why, report..
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-r', '--remote-path', metavar='', help='remote path to download from. default: /',
                          default='/')
    optional.add_argument('-di', '--dl-img', action='store_true', help='download image. default: True',
                          default=True)
    optional.add_argument('-da', '--dl-ann', action='store_true', help='download annotations json files: False',
                          default=False)
    optional.add_argument('-do', '--download_options', metavar='', help='download options CSV : merge/overwrite,relative-path/absolute-path ',
                          default='')
    optional.add_argument('-nw', '--num_workers', metavar='',
                          help='number of download workers',
                          default='')

    optional.add_argument('-dn', '--dl-instance', action='store_true',
                          help='download annotations instance default: False',
                          default=False)
    # optional.add_argument('-dim', '--dl-img-mask', action='store_true',
    #                       help='download images with marked annotations. default: False',
    #                       default=False)
    # optional.add_argument('-o', '--opacity', metavar='', type=float,
    #                       help='opacity when marking image. range:[0,1]. default: 1', default=1)
    optional.add_argument('-l', '--local-path', metavar='', help='local path', default=None)
    # optional.add_argument('-nw', '--num-workers', metavar='', help='num of threads workers', default=None)

    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    required.add_argument('-d', '--dataset-name', metavar='', help='dataset name', required=True)

    ###################
    # files and items #
    ###################
    subparser = subparsers.add_parser('files', help='Operations with files and items')
    subparser_parser = subparser.add_subparsers(dest='files', help='datasets files and items')

    a = subparser_parser.add_parser('ls', help='List of files in dataset')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    required.add_argument('-d', '--dataset-name', metavar='', help='dataset name', required=True)
    required.add_argument('-o', '--page', metavar='', help='dataset name', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-r', '--remote-path', metavar='', help='remote path', default='/')

    a = subparser_parser.add_parser('upload', help='Upload a single file')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-f', '--filename', metavar='', help='local filename to upload', required=True)
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    required.add_argument('-d', '--dataset-name', metavar='', help='dataset name', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-r', '--remote-path', metavar='', help='remote path', default='/')
    optional.add_argument('-t', '--item-type', metavar='', help='"folder", "file"', default='file')
    # split video to chunks
    optional.add_argument('-sc', '--split-chunks', metavar='',
                          help='Video splitting parameter: Number of chunks to split', default=None)
    optional.add_argument('-ss', '--split-seconds', metavar='', help='Video splitting parameter: Seconds of each chuck',
                          default=None)
    optional.add_argument('-st', '--split-times', metavar='',
                          help='Video splitting parameter: List of seconds to split at. e.g 600,1800,2000',
                          default=None)
    # encode
    optional.add_argument('-e', '--encode', help='encode video to mp4, remove bframes and upload', action='store_true',
                          default=False)
    # # disassemble
    # optional.add_argument('-ds', '--disass', help='disassemble according to fps and upload', action='store_true',
    #                       default=False)
    # optional.add_argument('-rt', '--fps', metavar='', help='disassemble frame rate (number of frames per second',
    #                       default=None)

    ##########
    # videos #
    ##########
    subparser = subparsers.add_parser('videos', help='Operations with videos')
    subparser_parser = subparser.add_subparsers(dest='videos', help='videos operations')

    a = subparser_parser.add_parser('play', help='List all package')
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-l', '--item_path', metavar='', help='Video remote path in platform. e.g /dogs/dog.mp4',
                          default=None)
    optional.add_argument('-d', '--dataset_name', metavar='', help='Dataset name', default=None)
    optional.add_argument('-p', '--project-name', metavar='', help='Project name', default=None)

    ############
    # packages #
    ############
    subparser = subparsers.add_parser('packages', help='Operations with package')
    subparser_parser = subparser.add_subparsers(dest='packages', help='package operations')

    a = subparser_parser.add_parser('ls', help='List all package')
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-p', '--project-name', metavar='', help='list a project\'s package', default=None)
    optional.add_argument('-g', '--package-id', metavar='', help='list package\'s artifacts', default=None)

    a = subparser_parser.add_parser('create', help='Create a new package')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-g', '--package-name', metavar='', help='package name', required=True)
    required.add_argument('-d', '--description', metavar='', help='package description', required=True)

    a = subparser_parser.add_parser('delete', help='Delete a package forever...')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-g', '--package-id', metavar='', help='package id', required=True)

    a = subparser_parser.add_parser('pack', help='Create a new package and add source code')
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-d', '--directory', metavar='', help='source code directory. default: cwd',
                          default=os.getcwd())

    a = subparser_parser.add_parser('unpack', help='Download and unzip source code')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-g', '--package-id', metavar='', help='package id', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-d', '--directory', metavar='', help='source code directory. default: cwd',
                          default=os.getcwd())

    ############
    # Sessions #
    ############
    subparser = subparsers.add_parser('sessions', help='Operations with sessions')
    subparser_parser = subparser.add_subparsers(dest='sessions', help='Operations with sessions')

    a = subparser_parser.add_parser('ls', help='List artifacts for session')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-i', '--session-id', metavar='', help='List artifacts in session id')

    a = subparser_parser.add_parser('tree', help='Print tree representation of sessions')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-p', '--project-name', metavar='', help='project name', required=True)

    a = subparser_parser.add_parser('create', help='Create a new Session')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-s', '--session-name', metavar='', help='session name', required=True)
    required.add_argument('-g', '--package-id', metavar='', help='source code', required=True)
    required.add_argument('-p', '--pipe-id', metavar='', help='pip to run', required=True)
    required.add_argument('-d', '--description', metavar='', help='session description', required=True)

    a = subparser_parser.add_parser('upload', help='Add artifact to session')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-s', '--session-id', metavar='', help='session id', required=True)
    required.add_argument('-f', '--filename', metavar='', help='local filename to add', required=True)
    required.add_argument('-t', '--type', metavar='', help='artifact type', required=True)
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-d', '--description', metavar='', help='file description. default: \'\'', default='')

    a = subparser_parser.add_parser('download', help='Download artifact from session')
    required = a.add_argument_group('required named arguments')
    required.add_argument('-s', '--session-id', metavar='', help='session id', required=True)
    required.add_argument('-a', '--artifact-id', metavar='', help='artifact id', required=True)
    required.add_argument('-d', '--local-path', metavar='', help='download to location', required=True)

    #########
    # Pipes #
    #########
    subparser = subparsers.add_parser('pipes', help='Operations with pipes')
    subparser_parser = subparser.add_subparsers(dest='pipes', help='Pipes operations')
    a = subparser_parser.add_parser('ls', help='List all pipes.')

    a = subparser_parser.add_parser('run', help='Run a pipe')
    optional = a.add_argument_group('optional named arguments')
    optional.add_argument('-s', '--session-id', metavar='', help='Current session id to run')
    optional.add_argument('-ps', '--prev-session-id', metavar='',
                          help='Create new session with revious session id to start from')
    optional.add_argument('--project-name', metavar='', help='project name. default: None', default=None)
    optional.add_argument('--dataset-name', metavar='', help='dataset name. default: None', default=None)
    optional.add_argument('--pipe-id', metavar='', help='pipe id. default: None', default=None)
    optional.add_argument('--package-id', metavar='', help='package id. default: None', default=None)
    optional.add_argument('--session-name', metavar='', help='new session name. default: None', default=None)
    optional.add_argument('--config-filename', metavar='', help='new configuration filename. default: None',
                          default=None)
    optional.add_argument('-r', '--remote-run', action='store_true', help='Run session remotely', default=False)

    ####
    # inputs
    optional.add_argument('-i', '--input', action='append', type=lambda kv: kv.split('='), dest='pipe_kwargs',
                          help='Input args for pipe. Use: ["--input key1=val1 --input key2=val2"]')

    return parser


def main():
    ##########
    # Logger #
    ##########
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('dataloop.cli')
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)

    ############################
    # Debug options
    ##########
    # args = parser.parse_args(['dataset', '-l'])
    # args = parser.parse_args('datasets ld --project-name seedo'.split())
    # args = parser.parse_args('package la --model-id 53624a4a-c5cb-4340-8f69-ab28e5b056e0'.split())

    ##################
    # Args from user #
    ##################
    parser = get_parser()
    args = parser.parse_args()

    ###############
    # Run command #
    ###############
    try:
        #########
        # Login #
        #########
        dlp = platform_interface.PlatformInterface()

        if args.operation == 'login':
            dlp.login()

        elif args.operation == 'login-token':
            dlp.login_token(args.token)

        elif args.operation == 'login-secret':
            dlp.login_secret(email=args.email,
                             password=args.password,
                             client_id=args.client_id,
                             client_secret=args.client_secret)

        #######
        # api #
        #######
        elif args.operation == 'api':
            if args.api == 'info':
                print('environment')
                print(dlp.environment)
                print('token')
                print(dlp.token)

            if args.api == 'setenv':
                dlp.setenv(args.env)
                print('[INFO] Platform environment: %s' % dlp.environment)

            if args.api == 'update':
                url = args.url
                print('[INFO] Update DTLPy from %s' % url)
                print('[INFO] Installing using pip...')
                cmd = 'pip install %s --upgrade ' % url
                p = subprocess.Popen(cmd, shell=True)
                return

        ############
        # Projects #
        ############
        elif args.operation == 'projects':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.projects == 'ls':
                dlp.projects.list().print()

            elif args.projects == 'create':
                dlp.projects.create(args.project_name).print()

            else:
                print('Type "dlp projects --help" for options')

        ############
        # Datasets #
        ############
        elif args.operation == 'datasets':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.datasets == 'ls':
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception('Project wasnt found. name: %s' % args.project_name)
                    raise ValueError('Project wasnt found. name: %s' % args.project_name)
                project.datasets.list().print()

            elif args.datasets == 'create':
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception('Project was not found. name: %s' % args.project_name)
                    raise ValueError('Project was not found. name: %s' % args.project_name)
                project.datasets.create(dataset_name=args.dataset_name).print()

            elif args.datasets == 'upload':
                print('[INFO] Uploading directory...')
                if isinstance(args.num_workers, str):
                    args.num_workers = int(args.num_workers)
                if isinstance(args.file_types, str):
                    args.file_types = args.file_types.split(',')
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    msg = 'Project wasnt found. name: %s' % args.project_name
                    logger.exception(msg)
                    raise ValueError(msg)
                project.datasets.upload(dataset_name=args.dataset_name,
                                        local_path=args.local_path,
                                        remote_path=args.remote_path,
                                        filetypes=args.file_types,
                                        num_workers=args.num_workers,
                                        upload_options=args.upload_options)

            elif args.datasets == 'download':
                print('[INFO] Downloading dataset...')
                if isinstance(args.num_workers, str):
                    args.num_workers = int(args.num_workers)
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception('Project wasnt found. name: %s' % args.project_name)
                    raise ValueError('Project wasnt found. name: %s' % args.project_name)
                download_options = {}
                if len(args.download_options)>0:
                    do_arr= args.download_options.split(',')
                    if len(do_arr)>0 and do_arr[0] == 'overwrite':
                        download_options['overwrite'] = True
                        print('[INFO] Overwrite mode')
                    if len(do_arr)>1 and do_arr[1] == 'relative-path':
                        download_options['relative_path'] = True
                        print('[INFO] relative path')
                project.datasets.download(query={'filenames': [args.remote_path]},
                                          dataset_name=args.dataset_name,
                                          local_path=args.local_path,
                                          download_item=args.dl_img,
                                          download_options=download_options,
                                          num_workers=args.num_workers
                                          # download_img_mask=args.dl_img_mask,
                                          # opacity=args.opacity,
                                          # filetypes=args.file_types,

                                          )
                if args.dl_ann:
                    project = dlp.projects.get(project_name=args.project_name)
                    if project is None:
                        logger.exception('Project wasnt found. name: %s' % args.project_name)
                        raise ValueError('Project wasnt found. name: %s' % args.project_name)
                    project.datasets.download_annotations(
                        dataset_name=args.dataset_name,
                        local_path=args.local_path
                    )

            else:
                print('Type "dlp datasets --help" for options')

        ###################
        # Files and items #
        ###################
        elif args.operation == 'files':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.files == 'ls':
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception('Project wasnt found. name: %s' % args.project_name)
                    raise ValueError('Project wasnt found. name: %s' % args.project_name)

                project.datasets.get(dataset_name=args.dataset_name).items.list()

            elif args.files == 'upload':
                project = dlp.projects.get(project_name=args.project_name)
                if project is None:
                    logger.exception('Project wasnt found. name: %s' % args.project_name)
                    raise ValueError('Project wasnt found. name: %s' % args.project_name)
                project.datasets.get(dataset_name=args.dataset_name).items.upload(filepath=args.filename,
                                                                                  remote_path=args.remote_path)

            else:
                print('Type "dlp files --help" for options')

        ##########
        # Videos #
        ##########
        elif args.operation == 'videos':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.videos == 'play':
                from dtlpy.utilities.videos.video_player import VideoPlayer
                VideoPlayer(item_filepath=args.item_path,
                            dataset_name=args.dataset_name,
                            project_name=args.project_name)
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
        elif args.operation == 'packages':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.packages == 'ls':
                if args.project_name is not None:
                    # list project's packages
                    dlp.projects.get(project_name=args.project_name).packages.list().print()
                elif args.package_id is not None:
                    # list package artifacts
                    dlp.packages.get(package_id=args.package_id).print()
                else:
                    # list user's package
                    dlp.packages.list().print()

            elif args.packages == 'create':
                if args.project_name is not None:
                    dlp.projects.get(args.project_name).packages.create(name=args.package_name,
                                                                        description=args.description)
                else:
                    dlp.packages.create(name=args.package_name, description=args.description)

            elif args.packages == 'delete':
                if args.project_name is not None:
                    dlp.projects.get(args.project_name).packages.delete(package_id=args.package_id)
                else:
                    dlp.packages.delete(package_id=args.package_id)

            elif args.packages == 'pack':
                print('Packing source: %s' % args.directory)
                dlp.packages.pack(directory=args.directory,
                                  name=args.name,
                                  description=args.description)
            elif args.packages == 'unpack':
                print('Unpacking source code...')
                dlp.packages.unpack(package_id=args.package_id,
                                    local_directory=args.directory)
            else:
                print('Type "dlp packages --help" for options')

        ############
        # Sessions #
        ############
        elif args.operation == 'sessions':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.sessions == 'ls':
                if args.session_id is not None:
                    dlp.sessions.get(session_id=args.session_id).print()
                elif args.project_name is not None:
                    dlp.projects.get(project_name=args.project_name).sessions.list().print()
                else:
                    print('[ERROR] need to input session-id or project-name.')

            elif args.sessions == 'tree':
                dlp.projects.get(project_name=args.project_name).sessions.tree()

            elif args.sessions == 'create':
                dlp.projects.get(project_name=args.project_name).sessions.create(session_name=args.session_name,
                                                                                 dataset_name=args.dataset_name,
                                                                                 pipe_id=args.pipe_id,
                                                                                 package_id=args.package_id)

            elif args.sessions == 'upload':
                dlp.sessions.get(session_id=args.session_id).artifacts.upload(filepath=args.filename,
                                                                              artifact_type=args.type,
                                                                              description=args.description)

            elif args.sessions == 'download':
                dlp.sessions.get(session_id=args.session_id).artifacts.download(artifact_type=args.artifact_type,
                                                                                local_directory=args.local_dir)
            else:
                print('Type "dlp sessions --help" for options')

        #########
        # Pipes #
        #########
        elif args.operation == 'pipes':
            if dlp.token_expired():
                print('[ERROR] token expired, please login.')
                return

            if args.pipes == 'ls':
                dlp.pipelines.list().print()

            elif args.pipes == 'run':
                # get input parameters
                kwargs = dict()
                if args.pipe_kwargs is not None:
                    kwargs = dict(args.pipe_kwargs)

                if args.prev_session_id is not None:
                    dlp.sessions.run_from_previous(prev_session_id=args.prev_session_id,
                                                   config_filename=args.config_filename,
                                                   input_params=kwargs,
                                                   pipe_id=args.pipe_id,
                                                   project_name=args.project_name,
                                                   dataset_name=args.dataset_name,
                                                   session_name=args.session_name,
                                                   package_id=args.package_id,
                                                   remote_run=args.remote_run
                                                   )

                elif args.session_id is not None:
                    dlp.sessions.run(session_id=args.session_id,
                                     input_params=kwargs,
                                     remote_run=args.remote_run)
                else:
                    print('[INFO] input missing. "session-id" or "prev-session-id"')
            else:
                print('Type "dlp pipes --help" for options')

        ###############
        # Catch typos #
        ###############
        elif args.operation == 'project':
            print('dlp: "project" is not an dlp command. Did you mean "projects"?')
        elif args.operation == 'dataset':
            print('dlp: "dataset" is not an dlp command. Did you mean "datasets"?')
        elif args.operation == 'item':
            print('dlp: "file" is not an dlp command. Did you mean "files"?')
        elif args.operation == 'session':
            print('dlp: "session" is not an dlp command. Did you mean "sessions"?')
        elif args.operation == 'package':
            print('dlp: "package" is not an dlp command. Did you mean "packages"?')
        elif args.operation == 'pipe':
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
        print('[ERROR]\t%s' % err)
    print('Dataloop.ai CLI. Type dlp --help for options')
