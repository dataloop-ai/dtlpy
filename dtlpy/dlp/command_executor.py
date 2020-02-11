import logging
import traceback
import subprocess
import jwt
import sys
import os
import datetime
import json
from dtlpy import repositories

from .. import exceptions


class CommandExecutor:

    def __init__(self, dl, parser):
        self.dl = dl
        self.parser = parser
        self.utils = Utils(dl)

    def run(self, args):
        print(datetime.datetime.utcnow())

        ########################
        # Run Command if Exist #
        ########################
        if args.operation is None:
            print('See "dlp --help" for options')
            return

        operation = args.operation.lower().replace('-', '_')
        if hasattr(self, operation):
            getattr(self, operation)(args)
        ###############
        # Catch typos #
        ###############
        elif args.operation in ["project", 'dataset', 'item', 'service', 'package', 'video']:
            self.typos(args=args)
        #######################
        # Catch other options #
        #######################
        elif args.operation:
            print('dlp: "%s" is not an dlp command' % args.operation)
            print('See "dlp --help" for options')
        else:
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

    def upgrade(self, args):
        url = 'dtlpy'
        if args.url is None:
            try:
                payload = jwt.decode(self.dl.client_api.token, algorithms=['HS256'], verify=False)
                if 'admin' in payload['https://dataloop.ai/authorization']['roles']:
                    url = "https://storage.googleapis.com/dtlpy/dev/dtlpy-latest-py3-none-any.whl"
            except Exception:
                pass
        else:
            url = args.url

        print("[INFO] Update DTLPy from {}".format(url))
        print("[INFO] Installing using pip...")
        cmd = "pip install {} --upgrade".format(url)
        subprocess.Popen(cmd, shell=True)
        sys.exit(0)

    # noinspection PyUnusedLocal
    def init(self, args):
        self.dl.init()

    # noinspection PyUnusedLocal
    def checkout_state(self, args):
        state = self.dl.checkout_state()
        print('Checked-out:')
        for key, val in state.items():
            try:
                msg = '{entity} name: {name}\t{entity} id: {id}'.format(entity=key, name=val['name'], id=val['id'])
            except KeyError:
                msg = '{entity} Not Found'.format(entity=key)
            print(msg)

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

    def projects(self, args):
        if args.projects == "ls":
            self.dl.projects.list().print()
        elif args.projects == "web":
            self.dl.projects.open_in_web(project_name=args.project_name)
        elif args.projects == "create":
            project = self.dl.projects.create(args.project_name)
            project.print()
            if args.checkout:
                project.checkout()
        elif args.projects == "checkout":
            self.dl.projects.checkout(project_name=args.project_name)
        else:
            print('Type "dlp projects --help" for options')

    def datasets(self, args):
        if args.datasets == "ls":
            print(datetime.datetime.utcnow())
            self.utils.get_datasets_repo(args=args).list().print()

        elif args.datasets == "checkout":
            self.dl.datasets.checkout(dataset_name=args.dataset_name)

        elif args.datasets == "web":
            self.utils.get_datasets_repo(args=args).open_in_web(dataset_name=args.dataset_name)

        elif args.datasets == "create":
            print(datetime.datetime.utcnow())
            dataset = self.utils.get_datasets_repo(args=args).create(dataset_name=args.dataset_name)
            dataset.print()
            if args.checkout:
                dataset.checkout()
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
                        filters.add(field="filename", values=remote_path, operator='glob')
                    else:
                        filters.add(field="filename", values=remote_path)
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
                if isinstance(args.remote_path, str):
                    remote_path = args.remote_path
                else:
                    remote_path = None
                dataset.download_annotations(filters=filters,
                                             local_path=args.local_path,
                                             annotation_options=annotation_options,
                                             overwrite=args.overwrite,
                                             with_text=args.with_text,
                                             thickness=int(args.thickness),
                                             remote_path=remote_path)

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

    def services(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        if hasattr(args, 'project_name ') and args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
        else:
            try:
                project = self.dl.projects.get()
            except exceptions.NotFound:
                project = None

        if args.services == "generate":
            self.dl.services.generate_services_json(path=args.local_path)
        elif args.services == "delete":
            services = self.utils.get_services_repo(args=args).list(name=args.service_name)
            if len(services) == 0:
                print('Service not found: {}'.format(args.service_name))
            elif len(services) > 1:
                print('More than one services found by the same name: {}'.format(args.service_name))
            else:
                service_name = services[0].name
                services[0].delete()
                print('Service: "{}" deleted successfully'.format(service_name))

        elif args.services == "deploy":
            if project is None:
                logging.error('Please provide project name or check out a project')
                return
            else:
                project.services.deploy_pipeline(bot=args.bot, service_json_path=args.local_path,
                                                 project=args.project_name)
        elif args.services == "tear_down":
            if project is None:
                logging.error('Please provide project name or check out a project')
                return
            else:
                project.services.tear_down(service_json_path=args.local_path, project=args.project_name)
        elif args.services == "ls":
            self.utils.get_services_repo(args=args).list().print()
        elif args.services == "log":
            project = self.dl.projects.get(project_name=args.project_name)
            service = project.services.get(service_name=args.service_name)

            logs = service.log(start=args.start)
            try:
                for log in logs:
                    if isinstance(log, list):
                        for log_record in log:
                            print(log_record)
                    else:
                        print(log)
            except KeyboardInterrupt:
                pass

        elif args.services == "execute":
            try:
                service = self.dl.services.get()
            except Exception:
                print('Please checkout a service')
                return

            if args.annotation_id is not None:
                resource = 'Annotation'
            elif args.item_id is not None:
                resource = 'Item'
            elif args.dataset_id is not None:
                resource = 'Dataset'
            else:
                resource = None

            try:
                execution_input = json.loads(args.inputs)
            except Exception:
                print('Input should be json serializable')
                return
            if len(execution_input) == 0:
                execution_input = None

            print('invoking')
            service.execute(sync=args.sync,
                            execution_input=execution_input,
                            function_name=args.function_name,
                            resource=resource,
                            item_id=args.item_id,
                            dataset_id=args.dataset_id,
                            annotation_id=args.annotation_id)
            print("Successfully deployed the package, service name is: %s" % service.name)

        else:
            print('Type "dlp packages --help" for options')

    def triggers(self, args):

        if args.triggers == "create":
            triggers = self.utils.get_triggers_repo(args=args)
            args.actions = [t.strip() for t in args.actions.split(",")]

            trigger = triggers.create(name=args.name,
                                      filters=json.loads('{}'.format(args.filters.replace("'", '"'))),
                                      function_name=args.function_name,
                                      resource=args.resource, actions=args.actions)

            print('Trigger created successfully: {}'.format(trigger.name))

        if args.triggers == "delete":
            triggers = self.utils.get_triggers_repo(args=args)
            triggers.get(trigger_name=args.trigger_name).delete()

            print('Trigger deleted successfully: {}'.format(args.trigger_name))

    def packages(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        if args.packages == "generate":
            packages = self.utils.get_packages_repo(args=args)
            packages.generate(name=args.package_name, src_path=os.getcwd())
            self.utils.dl.client_api.state_io.put('package', {'name': args.package_name})
            print('Successfully generated package')

        elif args.packages == "delete":
            packages = self.utils.get_packages_repo(args=args).list(name=args.package_name)
            if len(packages) == 0:
                print('Package not found: {}'.format(args.package_name))
            elif len(packages) > 1:
                print('More than one Packages found by the same name: {}'.format(args.package_name))
            else:
                packages[0].delete()

        elif args.packages == "ls":
            self.utils.get_packages_repo(args=args).list().print()

        elif args.packages == "checkout":
            self.dl.packages.checkout(package_name=args.package_name)

        elif args.packages == "push":
            packages = self.utils.get_packages_repo(args=args)

            package = packages.push(codebase_id=args.codebase_id,
                                    src_path=args.src_path,
                                    package_name=args.package_name,
                                    checkout=args.checkout)

            print("Successfully pushed package to platform\nPackage id:{}".format(package.id))

        elif args.packages == "test":
            go_back = False
            if 'src' in os.listdir(os.getcwd()):
                go_back = True
                os.chdir('./src')
            try:
                self.dl.packages.test_local_package(concurrency=int(args.concurrency))
            except Exception:
                print(traceback.format_exc())
            finally:
                if go_back:
                    os.chdir('..')

        elif args.packages == "deploy":
            project = self.dl.projects.get()
            package = self.dl.packages.get()
            if project is None or package is None:
                print('Please checkout a project and a package')
                return
            services = package.services
            services._project = project
            service = services.deploy_from_local_folder(bot=args.bot,
                                                        service_file=args.service_file,
                                                        checkout=args.checkout)
            print("Successfully deployed the package, service name is: %s" % service.name)

        else:
            print('Type "dlp packages --help" for options')

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


class Utils:
    def __init__(self, dl):
        self.dl = dl

    def get_packages_repo(self, args):
        if args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
            packages = project.packages
        else:
            try:
                packages = self.dl.projects.get().packages
            except Exception:
                packages = self.dl.packages

        assert isinstance(packages, repositories.Packages)
        return packages

    def get_datasets_repo(self, args):
        if args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
            datasets = project.datasets
        else:
            try:
                datasets = self.dl.projects.get().datasets
            except Exception:
                datasets = self.dl.datasets

        assert isinstance(datasets, repositories.Datasets)
        return datasets

    def get_services_repo(self, args):
        if args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
            packages = project.packages
            services = project.services
        else:
            try:
                packages = self.dl.projects.get().packages
                services = self.dl.projects.get().services
            except Exception:
                packages = self.dl.packages
                services = self.dl.services

        if args.package_name is not None:
            package_list = packages.list(name=args.package_name)
            if len(package_list) == 0:
                print('Package not found: {}'.format(args.package_name))
            elif len(package_list) > 1:
                print('More than one Packages found by the same name: {}'.format(args.package_name))
            else:
                services = package_list[0].services

        assert isinstance(services, repositories.Services)
        return services

    def get_triggers_repo(self, args):
        if args.project_name is not None:
            project = self.dl.projects.get(project_name=args.project_name)
            packages = project.packages
            services = project.services
            triggers = project.triggers
        else:
            try:
                packages = self.dl.projects.get().packages
                services = self.dl.projects.get().services
                triggers = self.dl.projects.get().triggers
            except Exception:
                packages = self.dl.packages
                services = self.dl.services
                triggers = self.dl.triggers

        if args.package_name is not None:
            package_list = packages.list(name=args.package_name)
            if len(package_list) == 0:
                print('Package not found: {}'.format(args.package_name))
            elif len(package_list) > 1:
                print('More than one Packages found by the same name: {}'.format(args.package_name))
            else:
                services = package_list[0].services

        service_list = services.list(name=args.service_name)
        if len(service_list) == 0:
            print('Package not found: {}'.format(args.package_name))
        elif len(service_list) > 1:
            print('More than one Packages found by the same name: {}'.format(args.package_name))
        else:
            triggers = service_list[0].triggers

        assert isinstance(triggers, repositories.Triggers)
        return triggers
