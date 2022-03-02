import subprocess
import logging
import getpass
import json
import jwt
import sys
import os

from dtlpy import repositories

from .. import exceptions, entities

logger = logging.getLogger('dtlpy')


class CommandExecutor:

    def __init__(self, dl, parser):
        self.dl = dl
        self.parser = parser
        self.utils = Utils(dl)

    def run(self, args):
        ########################
        # Run Command if Exist #
        ########################
        if args.operation is None:
            logger.info('See "dlp --help" for options')
            return

        operation = args.operation.lower().replace('-', '_')
        if hasattr(self, operation):
            getattr(self, operation)(args)
        ###############
        # Catch typos #
        ###############
        elif args.operation in ["project", 'dataset', 'item', 'service', 'package', 'video', 'deploy', 'generate']:
            self.typos(args=args)
        #######################
        # Catch other options #
        #######################
        elif args.operation:
            print('dlp: "%s" is not an dlp command' % args.operation)
            print('See "dlp --help" for options')
        else:
            print('See "dlp --help" for options')

    def logout(self, args):
        self.dl.logout()
        logger.info('logout successful')

    # noinspection PyUnusedLocal
    def login(self, args):
        self.dl.login()
        self.dl.info(with_token=False)

    def login_token(self, args):
        self.dl.login_token(args.token)
        self.dl.info(with_token=False)

    def login_secret(self, args):
        self.login_m2m(args=args)

    def login_m2m(self, args):
        if args.email is None:
            args.email = input('Enter user email: ')
        if args.password is None:
            args.password = getpass.getpass('Enter password: ')
        if args.client_id is None:
            args.client_id = input('Enter client id: ')
        if args.client_secret is None:
            args.client_secret = getpass.getpass('Enter client secret (press Enter if None):')
            if not args.client_secret:
                args.client_secret = None
        self.dl.login_secret(email=args.email,
                             password=args.password,
                             client_id=args.client_id,
                             client_secret=args.client_secret)
        self.dl.info(with_token=False)

    def login_m2m(self, args):
        self.dl.login_m2m(email=args.email,
                          password=args.password,
                          client_id=args.client_id,
                          client_secret=args.client_secret)
        self.dl.info(with_token=False)

    def upgrade(self, args):
        url = 'dtlpy'
        if args.url is None:
            try:
                payload = jwt.decode(self.dl.client_api.token, algorithms=['HS256'],
                                     verify=False, options={'verify_signature': False})
                if 'admin' in payload['https://dataloop.ai/authorization']['roles']:
                    url = "https://storage.googleapis.com/dtlpy/dev/dtlpy-latest-py3-none-any.whl"
            except Exception:
                pass
        else:
            url = args.url

        logger.info("Update DTLPy from {}".format(url))
        logger.info("Installing using pip...")
        cmd = "pip install {} --upgrade".format(url)
        subprocess.Popen(cmd, shell=True)
        sys.exit(0)

    # noinspection PyUnusedLocal
    def init(self, args):
        self.dl.init()

    # noinspection PyUnusedLocal
    def checkout_state(self, args):
        state = self.dl.checkout_state()
        logger.info('Checked-out:')
        for key, val in state.items():
            try:
                msg = '{entity} name: {name}\t{entity} id: {id}'.format(entity=key, name=val['name'], id=val['id'])
            except KeyError:
                msg = '{entity} Not Found'.format(entity=key)
            logger.info(msg)

    # noinspection PyUnusedLocal
    def version(self, args):
        logger.info("Dataloop SDK Version: {}".format(self.dl.__version__))

    # noinspection PyUnusedLocal
    def help(self, args):
        self.parser.print_help()

    def api(self, args):
        if args.api == "info":
            information = self.dl.info()
            logger.info('-- Dataloop info --')
            _ = [logger.info('{}: {}'.format(key, val)) for key, val in information.items()]

        if args.api == "setenv":
            self.dl.setenv(args.env)
            logger.info("Platform environment: {}".format(self.dl.environment()))

    def projects(self, args):
        if args.projects == "ls":
            self.dl.projects.list().print()
        elif args.projects == "web":
            if args.project_name is None:
                args.project_name = self.dl.projects.get().name
            self.dl.projects.open_in_web(project_name=args.project_name)
        elif args.projects == "create":
            project = self.dl.projects.create(args.project_name)
            project.print()
            project.checkout()
        elif args.projects == "checkout":
            self.dl.projects.checkout(project_name=args.project_name)
        else:
            print('Type "dlp projects --help" for options')

    def datasets(self, args):
        if args.datasets == "ls":
            self.utils.get_datasets_repo(args=args).list().print()

        elif args.datasets == "checkout":
            self.dl.datasets.checkout(dataset_name=args.dataset_name)

        elif args.datasets == "web":
            if args.dataset_name is None:
                args.dataset_name = self.dl.datasets.get().name
            self.utils.get_datasets_repo(args=args).open_in_web(dataset_name=args.dataset_name)

        elif args.datasets == "create":
            dataset = self.utils.get_datasets_repo(args=args).create(dataset_name=args.dataset_name)
            dataset.print()
            if args.checkout:
                dataset.checkout()
        else:
            print('Type "dlp datasets --help" for options')

    def items(self, args):
        if self.dl.token_expired():
            logger.error("token expired, please login.")
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
                    filters.add(field="filename", values=args.remote_path, operator=entities.FiltersOperations.IN)
                else:
                    filters.add(field="filename", values=args.remote_path)
            if args.type is not None:
                if isinstance(args.type, list):
                    filters.add(field='metadata.system.mimetype', values=args.type,
                                operator=entities.FiltersOperations.IN)
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
            logger.info("Uploading directory...")
            if isinstance(args.file_types, str):
                args.file_types = [t.strip() for t in args.file_types.split(",")]
            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)

            dataset.items.upload(local_path=args.local_path,
                                 remote_path=args.remote_path,
                                 file_types=args.file_types,
                                 overwrite=args.overwrite,
                                 local_annotations_path=args.local_annotations_path)

        elif args.items == "download":
            logger.info("Downloading dataset...")
            project = self.dl.projects.get(project_name=args.project_name)
            dataset = project.datasets.get(dataset_name=args.dataset_name)

            annotation_options = None
            if args.annotation_options is not None:
                annotation_options = [t.strip() for t in args.annotation_options.split(",")]

            annotation_filters = None
            if args.annotation_filter_type is not None or args.annotation_filter_label is not None:
                annotation_filters = entities.Filters(resource=entities.FiltersResource.ANNOTATION)
                if args.annotation_filter_type is not None:
                    annotation_filter_type = [t.strip() for t in args.annotation_filter_type.split(",")]
                    annotation_filters.add(field='type',
                                           values=annotation_filter_type,
                                           operator=entities.FiltersOperations.IN)
                if args.annotation_filter_label is not None:
                    annotation_filter_label = [t.strip() for t in args.annotation_filter_label.split(",")]
                    annotation_filters.add(field='label',
                                           values=annotation_filter_label,
                                           operator=entities.FiltersOperations.IN)
            # create remote path filters
            filters = self.dl.Filters()
            if args.remote_path is not None:
                remote_path = [t.strip() for t in args.remote_path.split(",")]
                if len(remote_path) == 1:
                    remote_path = remote_path[0]
                    filters.add(field="filename", values=remote_path)
                elif len(remote_path) > 1:
                    for item in remote_path:
                        if '*' in item:
                            filters.add(field="dir", values=item, method='or')
                            remote_path.pop(remote_path.index(item))
                    filters.add(field="dir", values=remote_path, operator=entities.FiltersOperations.IN, method='or')

            if not args.without_binaries:
                dataset.items.download(filters=filters,
                                       local_path=args.local_path,
                                       annotation_options=annotation_options,
                                       annotation_filters=annotation_filters,
                                       overwrite=args.overwrite,
                                       with_text=args.with_text,
                                       thickness=int(args.thickness),
                                       to_items_folder=not args.not_items_folder)
            else:
                dataset.download_annotations(filters=filters,
                                             local_path=args.local_path,
                                             annotation_options=annotation_options,
                                             annotation_filters=annotation_filters,
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

    def services(self, args):
        if self.dl.token_expired():
            print("[ERROR] token expired, please login.")
            return

        elif args.services == "delete":
            service = self.utils.get_services_repo(args=args).get(service_name=args.service_name)
            service.delete()
            logger.info('Service: "{}" deleted successfully'.format(service.name))

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
                if args.service_name:
                    service = self.utils.get_services_repo(args=args).get(service_name=args.service_name)
                else:
                    service = self.dl.services.get()
            except Exception:
                logger.info('Please checkout a service')
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
                logger.info('Input should be json serializable')
                return
            if len(execution_input) == 0:
                execution_input = None

            logger.info('executing')
            service.execute(sync=not args.asynchronous,
                            execution_input=execution_input,
                            function_name=args.function_name,
                            resource=resource,
                            item_id=args.item_id,
                            dataset_id=args.dataset_id,
                            annotation_id=args.annotation_id)
            logger.info("Successfully executed function: {}".format(args.function_name))

        else:
            logger.info('Type "dlp packages --help" for options')

    def deploy(self, args):
        project = self.dl.projects.get(project_name=args.project_name)
        json_filepath = args.json_file
        deployed_services, package = self.dl.packages.deploy_from_file(project=project, json_filepath=json_filepath)
        logger.info("Successfully deployed {} from file: {}\nServices: {}".format(len(deployed_services),
                                                                                  json_filepath,
                                                                                  [s.name for s in deployed_services]))

    def generate(self, args):
        package_type = args.package_type if args.package_type else self.dl.PackageCatalog.DEFAULT_PACKAGE_TYPE
        self.dl.packages.generate(name=args.package_name, src_path=os.getcwd(), package_type=package_type)
        self.utils.dl.client_api.state_io.put('package', {'name': args.package_name})
        logger.info('Successfully generated package files')

    def triggers(self, args):

        if args.triggers == "create":
            args.actions = [t.strip() for t in args.actions.split(",")]
            try:
                service = self.utils.get_services_repo(args).get(service_name=args.service_name)
            except exceptions.NotFound:
                logger.critical('Service not found. Please check-out a service or provide valid service name')
                return

            trigger = service.triggers.create(name=args.name,
                                              filters=json.loads('{}'.format(args.filters.replace("'", '"'))),
                                              function_name=args.function_name,
                                              resource=args.resource,
                                              actions=args.actions)
            logger.info('Trigger created successfully: {}'.format(trigger.name))

        elif args.triggers == "delete":
            triggers = self.utils.get_triggers_repo(args=args)
            triggers.get(trigger_name=args.trigger_name).delete()
            logger.info('Trigger deleted successfully: {}'.format(args.trigger_name))
        elif args.triggers == "ls":
            triggers = self.utils.get_triggers_repo(args=args)
            triggers.list().print()
        else:
            logger.info('Type "dlp packages --help" for options')

    def packages(self, args):
        if self.dl.token_expired():
            logger.error("token expired, please login.")
            return

        elif args.packages == "delete":
            package = self.utils.get_packages_repo(args=args).get(package_name=args.package_name)
            package.delete()
            logger.info('Successfully deleted package {}'.format(package.name))

        elif args.packages == "ls":
            self.utils.get_packages_repo(args=args).list().print()

        elif args.packages == "checkout":
            self.dl.packages.checkout(package_name=args.package_name)

        elif args.packages == "push":
            packages = self.utils.get_packages_repo(args=args)

            package = packages.push(src_path=args.src_path,
                                    package_name=args.package_name,
                                    checkout=True)

            logger.info("Successfully pushed package to platform\n"
                        "Package id:{}\nPackage version:{}".format(package.id,
                                                                   package.version))

        elif args.packages == "test":
            go_back = False
            if 'src' in os.listdir(os.getcwd()):
                go_back = True
                os.chdir('./src')
            try:
                self.dl.packages.test_local_package(concurrency=int(args.concurrency),
                                                    function_name=args.function_name)
            except Exception:
                logger.exception('failed during test')
            finally:
                if go_back:
                    os.chdir('..')

        else:
            logger.info('Type "dlp packages --help" for options')

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
            package = packages.get(package_name=args.package_name)
            services = package.services

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
            package = packages.package_name(name=args.package_name)
            services = package.services

        if args.service_name is not None:
            service = services.get(service_name=args.service_name)
            triggers = service.triggers

        assert isinstance(triggers, repositories.Triggers)
        return triggers
