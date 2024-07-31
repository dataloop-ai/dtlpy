class Dtlpy:
    from .services.api_client import client as client_api
    from .services.api_client import VerboseLoggingLevel, ApiClient
    from .services import DataloopLogger, DtlpyFilter, check_sdk, Reporter, service_defaults
    from .services.api_reference import api_reference as _api_reference
    from .caches.cache import CacheConfig, CacheType
    from .exceptions import PlatformException
    from . import repositories, exceptions, entities, examples
    from .entities import (
        # main entities
        Project, Dataset, ExpirationOptions, ExportVersion, Trigger, Item, Execution, AnnotationCollection, Annotation,
        Recipe, IndexDriver, AttributesTypes, AttributesRange, Dpk, App, AppModule, AppScope,
        Ontology, Label, Task, TaskPriority, ConsensusTaskType, Assignment, Service, Package, Codebase, Model,
        PackageModule, PackageFunction,
        # annotations
        Box, Cube, Cube3d, Point, Note, Message, Segmentation, Ellipse, Classification, Subtitle, Polyline, Pose,
        Description,
        Polygon, Text, FreeText, RefImage,
        # filters
        Filters, FiltersKnownFields, FiltersResource, FiltersOperations, FiltersMethod, FiltersOrderByDirection,
        FiltersKnownFields as KnownFields,
        # triggers
        TriggerResource, TriggerAction, TriggerExecutionMode, TriggerType,
        # faas
        FunctionIO, KubernetesAutuscalerType, KubernetesRabbitmqAutoscaler, KubernetesAutoscaler, KubernetesRuntime,
        InstanceCatalog, PackageInputType, ServiceType, ServiceModeType,
        PackageSlot, SlotPostAction, SlotPostActionType, SlotDisplayScope, SlotDisplayScopeResource, UiBindingPanel,
        # roberto
        DatasetSubsetType, ModelStatus, PlotSample, ArtifactType, Artifact, ItemArtifact, LinkArtifact, LocalArtifact,
        EntityScopeLevel,
        # features
        FeatureEntityType, Feature, FeatureSet,
        #
        RequirementOperator, PackageRequirement,
        Command, CommandsStatus,
        LocalCodebase, GitCodebase, ItemCodebase, FilesystemCodebase, PackageCodebaseType,
        MemberRole, MemberOrgRole,
        Webhook, HttpMethod,
        ViewAnnotationOptions, AnnotationStatus, AnnotationType,
        ItemStatus, ExecutionStatus, ExportMetadata,
        PromptItem, Prompt, PromptType,
        ItemLink, UrlLink, LinkTypeEnum,
        Modality, ModalityTypeEnum, ModalityRefTypeEnum,
        Workload, WorkloadUnit, ItemAction,
        PipelineExecution, CycleRerunMethod, PipelineExecutionNode, Pipeline, PipelineConnection,
        PipelineNode, TaskNode, CodeNode, PipelineStats, PipelineSettings,
        PipelineNodeType, PipelineNameSpace, PipelineResumeOption, Variable, CompositionStatus,
        FunctionNode, DatasetNode, PipelineConnectionPort, PipelineNodeIO, Organization, OrganizationsPlans,
        Integration,
        Driver, S3Driver, GcsDriver, AzureBlobDriver, CacheAction, PodType,
        ExternalStorage, IntegrationType, Role, PlatformEntityType, SettingsValueTypes, SettingsTypes,
        SettingsSectionNames,
        SettingScope, BaseSetting, UserSetting, Setting, ServiceSample, ExecutionSample, PipelineExecutionSample,
        ResourceExecution, Message, NotificationEventContext
    )
    from .ml import BaseModelAdapter
    from .utilities import Converter, BaseServiceRunner, Progress, Context, AnnotationFormat
    from .repositories import FUNCTION_END_LINE, PackageCatalog

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
        self.dpks = self.repositories.Dpks(client_api=self.client_api)
        self.annotations = self.repositories.Annotations(client_api=self.client_api)
        self.models = self.repositories.Models(client_api=self.client_api)
        self.ontologies = self.repositories.Ontologies(client_api=self.client_api)
        self.recipes = self.repositories.Recipes(client_api=self.client_api)
        self.pipelines = self.repositories.Pipelines(client_api=self.client_api)
        self.pipeline_executions = self.repositories.PipelineExecutions(client_api=self.client_api)
        self.feature_sets = self.repositories.FeatureSets(client_api=self.client_api)
        self.features = self.repositories.Features(client_api=self.client_api)
        self.organizations = self.repositories.Organizations(client_api=self.client_api)
        self.analytics = self.repositories.Analytics(client_api=self.client_api)
        self.integrations = self.repositories.Integrations(client_api=self.client_api)
        self.drivers = self.repositories.Drivers(client_api=self.client_api)
        self.settings = self.repositories.Settings(client_api=self.client_api)
        self.apps = self.repositories.Apps(client_api=self.client_api)
        self.dpks = self.repositories.Dpks(client_api=self.client_api)
        self.messages = self.repositories.Messages(client_api=self.client_api)
        self.compositions = self.repositories.Compositions(client_api=self.client_api)

        self.verbose = self.client_api.verbose
        self.login = self.client_api.login
        self.logout = self.client_api.logout
        self.login_token = self.client_api.login_token
        self.login_secret = self.client_api.login_secret
        self.login_api_key = self.client_api.login_api_key
        self.login_m2m = self.client_api.login_m2m
        self.add_environment = self.client_api.add_environment
        self.setenv = self.client_api.setenv
        self.token_expired = self.client_api.token_expired
        self.info = self.client_api.info
        self.cache_state = self.client_api.cache_state
        self.attributes_mode = self.client_api.attributes_mode
        self.sdk_cache = self.client_api.sdk_cache
        self.platform_settings = self.client_api.platform_settings

    def __del__(self):
        for name, pool in self.client_api._thread_pools.items():
            pool.shutdown()

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
        HIGHMEM_MICRO = 'highmem-micro'
        HIGHMEM_XS = 'highmem-xs'
        HIGHMEM_S = 'highmem-s'
        HIGHMEM_M = 'highmem-m'
        HIGHMEM_L = 'highmem-l'
        GPU_K80_S = "gpu-k80-s"
        GPU_K80_M = "gpu-k80-m"
        GPU_T4_S = "gpu-t4-s"
        GPU_T4_M = "gpu-t4-m"

    class LoggingLevel:
        DEBUG = 'debug'
        WARNING = 'warning'
        CRITICAL = 'critical'
        INFO = 'info'
