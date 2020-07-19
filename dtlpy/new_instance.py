class Dtlpy:
    from .exceptions import PlatformException
    from . import repositories, exceptions, entities, examples
    from .__version__ import version as __version__
    from .entities import Box, Point, Segmentation, Polygon, Ellipse, Classification, Subtitle, Polyline, Filters, \
        Trigger, \
        AnnotationCollection, Annotation, Item, Codebase, Filters, Execution, Recipe, Ontology, Label, Similarity, \
        ItemLink, UrlLink, PackageModule, PackageFunction, FunctionIO, Modality, Workload, WorkloadUnit
    from .utilities import Converter, BaseServiceRunner, Progress
    from .services import ApiClient, check_sdk

    def __init__(self, cookie_filepath=None):
        self.client_api = self.ApiClient(cookie_filepath=cookie_filepath)
        self.projects = self.repositories.Projects(client_api=self.client_api)
        self.datasets = self.repositories.Datasets(client_api=self.client_api,
                                                   project=None)
        self.items = self.repositories.Items(client_api=self.client_api,
                                             datasets=self.datasets)
        self.packages = self.repositories.Packages(client_api=self.client_api)
        self.executions = self.repositories.Executions(client_api=self.client_api)
        self.services = self.repositories.Services(client_api=self.client_api)
        self.webhooks = self.repositories.Webhooks(client_api=self.client_api)
        self.triggers = self.repositories.Triggers(client_api=self.client_api)
        self.assignments = self.repositories.Assignments(client_api=self.client_api)
        self.tasks = self.repositories.Tasks(client_api=self.client_api)
        self.annotations = self.repositories.Annotations(client_api=self.client_api)
        self.verbose = self.client_api.verbose
        self.login = self.client_api.login
        self.login_token = self.client_api.login_token
        self.login_secret = self.client_api.login_secret
        self.add_environment = self.client_api.add_environment
        self.setenv = self.client_api.setenv
        self.token_expired = self.client_api.token_expired
        self.info = self.client_api.info

    def __del__(self):
        for name, pool in self.client_api._thread_pools.items():
            pool.close()
            pool.terminate()

    def token(self):
        """
        token
        :return: token in use
        """
        return self.client_api.token

    def environment(self):
        """
        environment
        :return: current environment
        """
        return self.client_api.environment

    def init(self):
        """
        init current directory as a Dataloop working directory
        :return:
        """
        from .services import CookieIO
        self.client_api.state_io = CookieIO.init_local_cookie(create=True)
        assert isinstance(self.client_api.state_io, CookieIO)

    def checkout_state(self):
        """
        Return the current checked out state
        :return:
        """
        state = self.client_api.state_io.read_json()
        return state

    class ModalityTypeEnum:
        """
        State enum
        """
        OVERLAY = 'overlay'

    class SimilarityTypeEnum:
        """
        State enum
        """
        ID = 'id'
        URL = 'url'

    class LinkTypeEnum:
        """
        State enum
        """
        ID = 'id'
        URL = 'url'

    class TriggerResource:
        ITEM = 'Item'
        DATASET = 'Dataset'
        ANNOTATION = 'Annotation'

    class TriggerAction:
        CREATED = 'Created'
        UPDATED = 'Updated'
        DELETED = 'Deleted'

    class TriggerExecutionMode:
        ONCE = 'Once'
        ALWAYS = 'Always'

    class PackageInputType:
        ITEM = 'Item'
        DATASET = 'Dataset'
        ANNOTATION = 'Annotation'
        JSON = 'Json'

    class FiltersResource:
        ITEM = 'items'
        ANNOTATION = 'annotations'

    class FiltersOperations:
        OR = 'or'
        AND = 'and'
        IN = 'in'
        NOT_EQUAL = 'ne'
        EQUAL = 'eq'
        GREATER_THAN = 'gt'
        GLOB = 'glob'
        LESS_THAN = 'lt'

    class FiltersMethod:
        OR = 'or'
        AND = 'and'

    class FiltersOrderByDirection:
        DESCENDING = 'descending'
        ASCENDING = 'ascending'

    class KnownFields:
        DIR = 'dir'
        ANNOTATED = 'annotated'
        FILENAME = 'filename'
        CREATED_AT = 'createdAt'
        UPDATED_AT = 'updatedAt'
        LABEL = 'label'
        NAME = 'name'
        HIDDEN = 'hidden'

    class ExecutionStatus:
        SUCCESS = 'success'
        FAILED = 'failed'
        IN_PROGRESS = 'inProgress'
        CREATED = 'created'

    class HttpMethod:
        GET = 'GET'
        POST = 'POST'
        DELETE = 'DELETE'
        PATCH = 'PATCH'

    class ViewAnnotationOptions:
        JSON = 'json'
        MASK = 'mask'
        INSTANCE = 'instance'

    class AnnotationFormat:
        COCO = 'coco'
        VOC = 'voc'
        YOLO = 'yolo'
        DATALOOP = 'dataloop'

    class InstanceCatalog:
        REGULAR_MICRO = 'regular-micro'
        REGULAR_XS = 'regular-xs'
        REGULAR_S = 'regular-s'
        REGULAR_M = 'regular-m'
        REGULAR_L = 'regular-l'
        REGULAR_XL = 'regular-xl'
        HIGHMEM_MICRO = 'highmem-micro'
        HIGHMEM_XS = 'highmem-xs'
        HIGHMEM_S = 'highmem-s'
        HIGHMEM_M = 'highmem-m'
        HIGHMEM_L = 'highmem-l'
        HIGHMEM_XL = 'highmem-xl'
        GPU_K80_S = 'gpu-k80-s'

    class LoggingLevel:
        DEBUG = 'debug'
        WARNING = 'warning'
        CRITICAL = 'critical'
        INFO = 'info'
