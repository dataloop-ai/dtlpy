import logging
import traceback
import subprocess
import jwt
import sys
import os
import datetime


class CommandExecutor:

    def __init__(self, dl, parser):
        self.dl = dl
        self.parser = parser

    def run(self, args):
        print(datetime.datetime.utcnow())

        ########################
        # Run Command if Exist #
        ########################
        operation = args.operation.lower().replace('-', '_')
        if hasattr(self, operation):
            getattr(self, operation)(args)

        ###############
        # Catch typos #
        ###############
        elif args.operation in ["project", 'dataset', 'item', 'deployment', 'plugin', 'video']:
            self.typos(args=args)

        #######################
        # Catch other options #
        #######################
        elif args.operation:
            print('dlp: "%s" is not an dlp command' % args.operation)
        print('See "dlp --help" for options')

    # noinspection PyUnusedLocal
    def login(self, args):
        self.dl.login()
        self.dl.info(with_token=False)

    def login_token(self, args):
        self.dl.login_token(args.token)
        self.dl.info(with_token=False)

    def login_secret(self, args):
        self.dl.login_secret(email=args.email,
                             password=args.password,
                             client_id=args.client_id,
                             client_secret=args.client_secret)
        self.dl.info(with_token=False)

    # noinspection PyUnusedLocal
    def init(self, args):
        self.dl.init()

    # noinspection PyUnusedLocal
    def checkout_state(self, args):
        state = self.dl.checkout_state()
        print('Checked-out:')
        for key, val in state.items():
            if key == 'project':
                try:
                    project_name = self.dl.projects.get(project_id=state['project']).name
                except Exception:
                    project_name = 'Project Not Found'
                print('Project name: {}\nProject id: {}'.format(project_name, val))
            if key == 'dataset':
                try:
                    dataset_name = self.dl.datasets.get(dataset_id=state['dataset']).name
                except Exception:
                    dataset_name = 'Dataset Not Found'
                print('Dataset name: {}\nDataset id: {}'.format(dataset_name, val))

    # noinspection PyUnusedLocal
    def version(self, args):
        print("[INFO] Dataloop SDK Version: {}".format(self.dl.__version__))

    # noinspection PyUnusedLocal
    def help(self, args):
        self.parser.print_help()

    def api(self, args):
        if args.api == "info":
            information = self.dl.info()
            print('-- Dataloop info --')
            _ = [print('{}: {}'.format(key, val)) for key, val in information.items()]

        if args.api == "setenv":
            self.dl.setenv(args.env)
            print("[INFO] Platform environment: {}".format(self.dl.environment()))

        if args.api == "upgrade":
            url = args.url
            payload = jwt.decode(self.dl.client_api.token, algorithms=['HS256'], verify=False)
            try:
                if 'admin' in payload['https://dataloop.ai/authorization']['roles']:
                    url = "https://storage.googleapis.com/dtlpy/dev/dtlpy-latest-py3-none-any.whl"
            except Exception:
                pass
            print("[INFO] Update DTLPy from {}".format(url))
            print("[INFO] Installing using pip...")
            cmd = "pip install {} --upgrade".format(url)
            subprocess.Popen(cmd, shell=True)
            sys.exit(0)

    def projects(self, args):
        if args.projects == "ls":
            self.dl.projects.list().print()
        elif args.projects == "web":
            self.dl.projects.open_in_web(project_name=args.project_name)
        elif args.projects == "create":
            project = self.dl.projects.create(args.project_name)
            project.print()
            if args.checkout:
                self.dl.projects.checkout(project.name)
        elif args.projects == "checkout":
            self.dl.projects.checkout(args.project_name)
        else:
            print('Type "dlp projects --help" for options')

    def datasets(self, args):
        if args.datasets == "ls":
            project = self.dl.projects.get(project_name=args.project_name)
            print(datetime.datetime.utcnow())
            project.datasets.list().print()

        elif args.datasets == "checkout":
            if args.project_name is not None:
                self.dl.projects.checkout(args.project_name)
            self.dl.datasets.checkout(args.dataset_name)

        elif args.datasets == "web":
            project = self.dl.projects.get(project_name=args.project_name)
            project.datasets.open_in_web(dataset_name=args.dataset_name)

        elif args.datasets == "create":
            project = self.dl.projects.get(project_name=args.project_name)
            print(datetime.datetime.utcnow())
            dataset = project.datasets.create(dataset_name=args.dataset_name)
            dataset.print()
            if args.checkout:
                self.dl.datasets.checkout(dataset.name)
        else:
            print('Type "dlp datasets --help" for options')

    def items(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        if args.items == "ls":
            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            if isinstance(args.page, str):
                try:
                    args.page = int(args.page)
                except ValueError:
                    raise ValueError("Input --page must be integer")
            filters = self.dl.Filters()

            # add filters
            if args.remote_path is not None:
                if isinstance(args.remote_path, list):
                    filters.add(field="filename", values=args.remote_path, operator="in")
                else:
                    filters.add(field="filename", values=args.remote_path)
            if args.type is not None:
                if isinstance(args.type, list):
                    filters.add(field='metadata.system.mimetype', values=args.type, operator="in")
                else:
                    filters.add(field="metadata.system.mimetype", values=args.type)

            pages = dataset.items.list(filters=filters, page_offset=args.page)
            pages.print()
            print("Displaying page %d/%d" % (args.page, pages.total_pages_count - 1))

        elif args.items == "web":
            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            dataset.items.open_in_web(filepath=args.remote_path)

        elif args.items == "upload":
            print(datetime.datetime.utcnow())
            print("[INFO] Uploading directory...")
            if isinstance(args.num_workers, str):
                args.num_workers = int(args.num_workers)
            if isinstance(args.file_types, str):
                args.file_types = [t.strip() for t in args.file_types.split(",")]
            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)

            dataset.items.upload(local_path=args.local_path,
                                 remote_path=args.remote_path,
                                 file_types=args.file_types,
                                 num_workers=args.num_workers,
                                 overwrite=args.overwrite,
                                 local_annotations_path=args.local_annotations_path)

        elif args.items == "download":
            print("[INFO] Downloading dataset...")

            if isinstance(args.num_workers, str):
                args.num_workers = int(args.num_workers)

            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)
            annotation_options = None
            if args.annotation_options is not None:
                annotation_options = [t.strip() for t in args.annotation_options.split(",")]

            # create remote path filters
            filters = self.dl.Filters()
            if args.remote_path is not None:
                remote_path = [t.strip() for t in args.remote_path.split(",")]
                if len(remote_path) == 1:
                    remote_path = remote_path[0]
                    if '*' in remote_path:
                        filters.add(field="dir", values=remote_path, operator='glob')
                    else:
                        filters.add(field="dir", values=remote_path)
                elif len(remote_path) > 1:
                    for item in remote_path:
                        if '*' in item:
                            filters.add(field="dir", values=item, operator='glob', method='or')
                            remote_path.pop(remote_path.index(item))
                    filters.add(field="dir", values=remote_path, operator='in', method='or')

            if not args.without_binaries:
                dataset.items.download(filters=filters,
                                       local_path=args.local_path,
                                       annotation_options=annotation_options,
                                       overwrite=args.overwrite,
                                       num_workers=args.num_workers,
                                       with_text=args.with_text,
                                       thickness=int(args.thickness),
                                       to_items_folder=not args.not_items_folder)
            else:
                dataset.download_annotations(filters=filters,
                                             local_path=args.local_path,
                                             annotation_options=annotation_options,
                                             overwrite=args.overwrite,
                                             with_text=args.with_text,
                                             thickness=int(args.thickness))

        else:
            print('Type "dlp items --help" for options')

    def videos(self, args):
        if self.dl.token_expired():
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
                self.dl.utilities.videos.Videos.split_and_upload(
                    project_name=args.project_name,
                    dataset_name=args.dataset_name,
                    filepath=args.filename,
                    remote_path=args.remote_path,
                    split_chunks=args.split_chunks,
                    split_seconds=args.split_seconds,
                    split_pairs=args.split_times,
                )
        else:
            print('Type "dlp videos --help" for options')

    def deployments(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        if args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
        else:
            project = self.dl.projects.get()

        if args.deployments == "generate":
            self.dl.deployments.generate_deployments_json(path=args.local_path)
        elif args.deployments == "deploy":
            if project is None:
                logging.error('Please provide project name or check out a project')
                return
            else:
                project.deployments.deploy_pipeline(deployment_json_path=args.local_path, project=args.project_name)
        elif args.deployments == "tear_down":
            if project is None:
                logging.error('Please provide project name or check out a project')
                return
            else:
                project.deployments.tear_down(deployment_json_path=args.local_path, project=args.project_name)
        elif args.deployments == "ls":
            if args.project_name is not None:
                project = self.dl.projects.get(project_name=args.project_name)
            else:
                project = self.dl.projects.get()
            project.deployments.list().print()
        elif args.deployments == "log":
            project = self.dl.projects.get(project_name=args.project_name)
            deployment = project.deployments.get(deployment_name=args.deployment_name)

            logs = deployment.log(start=args.start)
            try:
                for log in logs:
                    if isinstance(log, list):
                        for log_record in log:
                            print(log_record)
                    else:
                        print(log)
            except KeyboardInterrupt:
                pass

    def plugins(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        if args.plugins == "generate":
            if args.project_name is not None:
                plugins = self.dl.projects.get(project_name=args.project_name).plugins
            else:
                try:
                    project = self.dl.projects.get()
                    plugins = project.plugins
                except Exception:
                    plugins = self.dl.plugins
            plugins.generate(name=args.plugin_name, src_path=os.getcwd())
            print('Successfully generated plugin')

        elif args.plugins == "ls":
            if args.project_name is not None:
                plugins = self.dl.projects.get(project_name=args.project_name).plugins
            else:
                try:
                    project = self.dl.projects.get()
                    plugins = project.plugins
                except Exception:
                    plugins = self.dl.plugins
            plugins.list().print()

        elif args.plugins == "checkout":
            self.dl.plugins.checkout(args.plugin_name)

        elif args.plugins == "push":
            if args.project_name is None:
                plugins = self.dl.plugins
            else:
                plugins = self.dl.projects.get(project_name=args.project_name).plugins

            plugin = plugins.push(package_id=args.package_id,
                                  src_path=args.src_path,
                                  plugin_name=args.plugin_name)

            print("Successfully pushed plugin to platform\nPlugin id:{}".format(plugin.id))

        elif args.plugins == "test":
            go_back = False
            if 'src' in os.listdir(os.getcwd()):
                go_back = True
                os.chdir('./src')
            try:
                self.dl.plugins.test_local_plugin(concurrency=int(args.concurrency))
            except Exception:
                print(traceback.format_exc())
            finally:
                if go_back:
                    os.chdir('..')

        elif args.plugins == "deploy":
            deployment_name = self.dl.deployments.deploy_from_local_folder(deployment_file=args.deployment_file).name
            print("Successfully deployed the plugin, deployment name is: %s" % deployment_name)

        else:
            print('Type "dlp plugins --help" for options')

    # noinspection PyUnusedLocal
    @staticmethod
    def pwd(args):
        print(os.getcwd())

    @staticmethod
    def cd(args):
        directory = args.dir
        if directory == '..':
            directory = os.path.split(os.getcwd())[0]
        os.chdir(directory)
        print(os.getcwd())

    @staticmethod
    def mkdir(args):
        os.mkdir(args.name)

    # noinspection PyUnusedLocal
    @staticmethod
    def ls(args):
        print(os.getcwd())
        dirs = os.listdir(os.getcwd())
        import pprint

        pp = pprint.PrettyPrinter(indent=3)
        pp.pprint(dirs)

    # noinspection PyUnusedLocal
    @staticmethod
    def clear(args):
        if os.name == "nt":
            os.system('cls')
        else:
            os.system('clear')

    @staticmethod
    def typos(args):
        print('dlp: "{op}" is not an dlp command. Did you mean "{op}s"?'.format(op=args.operation))
