import traceback
from enum import Enum
from typing import List, Optional, Dict
from ..services.api_client import ApiClient
from .. import repositories


class ClusterProvider(str, Enum):
    GCP = 'gcp'
    AWS = 'aws'
    AZURE = 'azure'
    HPC = 'hpc'
    LOCAL = 'local'
    RANCHER_K3S = 'rancher-k3s'
    RANCHER_RKE = 'rancher-rke'


class ComputeType(str, Enum):
    KUBERNETES = "kubernetes"


class ComputeStatus(str, Enum):
    READY = "ready"
    INITIALIZING = "initializing"
    PAUSE = "pause"
    FAILED = "failed"
    VALIDATING = "validating"


class ComputeConsumptionMethod(str, Enum):
    MQ = "MQ",
    API = "API"


class ComputeSettings:
    def __init__(self, default_namespace: str, consumption_method: ComputeConsumptionMethod):
        self.consumption_method = consumption_method
        self.default_namespace = default_namespace

    @classmethod
    def from_json(cls, _json):
        return cls(
            default_namespace=_json.get('defaultNamespace'),
            consumption_method=_json.get('consumptionMethod')
        )

    def to_json(self):
        return {
            'defaultNamespace': self.default_namespace,
            'consumptionMethod': self.consumption_method
        }


class Toleration:
    def __init__(self, effect: str, key: str, operator: str, value: str):
        self.effect = effect
        self.key = key
        self.operator = operator
        self.value = value

    @classmethod
    def from_json(cls, _json):
        return cls(
            effect=_json.get('effect'),
            key=_json.get('key'),
            operator=_json.get('operator'),
            value=_json.get('value')
        )

    def to_json(self):
        return {
            'effect': self.effect,
            'key': self.key,
            'operator': self.operator,
            'value': self.value
        }


class DeploymentResource:
    def __init__(self, gpu: int, cpu: int, memory: str):
        self.gpu = gpu
        self.cpu = cpu
        self.memory = memory

    @classmethod
    def from_json(cls, _json):
        return cls(
            gpu=_json.get('gpu', None),
            cpu=_json.get('cpu', None),
            memory=_json.get('memory', None)
        )

    def to_json(self):
        _json = {}
        if self.gpu is not None:
            _json['gpu'] = self.gpu
        if self.cpu is not None:
            _json['cpu'] = self.cpu
        if self.memory is not None:
            _json['memory'] = self.memory


class DeploymentResources:
    def __init__(self, request: DeploymentResource, limit: DeploymentResource):
        self.request = request
        self.limit = limit

    @classmethod
    def from_json(cls, _json):
        return cls(
            request=DeploymentResource.from_json(_json.get('request') or dict()),
            limit=DeploymentResource.from_json(_json.get('limit') or dict())
        )

    def to_json(self):
        return {
            'request': self.request.to_json(),
            'limit': self.limit.to_json()
        }


class NodePool:
    def __init__(
            self,
            name: str,
            is_dl_type_default: bool,
            dl_types: Optional[List[str]] = None,
            tolerations: Optional[List[Toleration]] = None,
            description: str = "",
            node_selector: str = "",
            preemptible: bool = False,
            deployment_resources: DeploymentResources = None
    ):
        self.name = name
        self.is_dl_type_default = is_dl_type_default
        self.dl_types = dl_types
        self.tolerations = tolerations if tolerations is not None else []
        self.description = description
        self.node_selector = node_selector
        self.preemptible = preemptible
        self.deployment_resources = deployment_resources

    @classmethod
    def from_json(cls, _json):
        node_pool = cls(
            name=_json.get('name'),
            is_dl_type_default=_json.get('isDlTypeDefault'),
            dl_types=_json.get('dlTypes'),
            description=_json.get('description'),
            node_selector=_json.get('nodeSelector'),
            preemptible=_json.get('preemptible'),
            deployment_resources=DeploymentResources.from_json(_json.get('deploymentResources', dict())),
            tolerations=[Toleration.from_json(t) for t in _json.get('tolerations', list())]
        )

        return node_pool

    def to_json(self):
        _json = {
            'name': self.name,
            'isDlTypeDefault': self.is_dl_type_default,
            'description': self.description,
            'nodeSelector': self.node_selector,
            'preemptible': self.preemptible,
            'deploymentResources': self.deployment_resources.to_json(),
            'tolerations': [t.to_json() for t in self.tolerations]
        }

        if self.dl_types is not None:
            _json['dlTypes'] = self.dl_types

        return _json


class AuthenticationIntegration:
    def __init__(self, id: str, type: str):
        self.id = id
        self.type = type

    @classmethod
    def from_json(cls, _json):
        return cls(
            id=_json.get('id'),
            type=_json.get('type')
        )

    def to_json(self):
        return {
            'id': self.id,
            'type': self.type
        }


class Authentication:
    def __init__(self, integration: AuthenticationIntegration):
        self.integration = integration

    @classmethod
    def from_json(cls, _json):
        return cls(
            integration=AuthenticationIntegration.from_json(_json.get('integration', dict()))
        )

    def to_json(self):
        return {
            'integration': self.integration.to_json()
        }


class ComputeCluster:
    def __init__(
            self,
            name: str,
            endpoint: str,
            kubernetes_version: str,
            provider: ClusterProvider,
            node_pools: Optional[List[NodePool]] = None,
            metadata: Optional[Dict] = None,
            authentication: Optional[Authentication] = None,
            plugins: Optional[dict] = None
    ):
        self.name = name
        self.endpoint = endpoint
        self.kubernetes_version = kubernetes_version
        self.provider = provider
        self.node_pools = node_pools if node_pools is not None else []
        self.metadata = metadata if metadata is not None else {}
        self.authentication = authentication if authentication is not None else Authentication(
            AuthenticationIntegration("", ""))
        self.plugins = plugins

    @classmethod
    def from_json(cls, _json):
        return cls(
            name=_json.get('name'),
            endpoint=_json.get('endpoint'),
            kubernetes_version=_json.get('kubernetesVersion'),
            provider=ClusterProvider(_json.get('provider')),
            node_pools=[NodePool.from_json(np) for np in _json.get('nodePools', list())],
            metadata=_json.get('metadata'),
            authentication=Authentication.from_json(_json.get('authentication', dict())),
            plugins=_json.get('plugins')
        )

    def to_json(self):
        return {
            'name': self.name,
            'endpoint': self.endpoint,
            'kubernetesVersion': self.kubernetes_version,
            'provider': self.provider.value,
            'nodePools': [np.to_json() for np in self.node_pools],
            'metadata': self.metadata,
            'authentication': self.authentication.to_json(),
            'plugins': self.plugins
        }

    @classmethod
    def from_setup_json(cls, devops_output, integration):
        node_pools = [NodePool.from_json(n) for n in devops_output['config']['nodePools']]
        return cls(
            name=devops_output['config']['name'],
            endpoint=devops_output['config']['endpoint'],
            kubernetes_version=devops_output['config']['kubernetesVersion'],
            provider=ClusterProvider(devops_output['config']['provider']),
            node_pools=node_pools,
            metadata={},
            authentication=Authentication(AuthenticationIntegration(integration.id, integration.type)),
            plugins=devops_output['config'].get('plugins')
        )


class ComputeContext:
    def __init__(self, labels: List[str], org: str, project: Optional[str] = None):
        self.labels = labels
        self.org = org
        self.project = project

    @classmethod
    def from_json(cls, _json):
        return cls(
            labels=_json.get('labels', list()),
            org=_json.get('org'),
            project=_json.get('project')
        )

    def to_json(self):
        return {
            'labels': self.labels,
            'org': self.org,
            'project': self.project
        }


class Compute:
    def __init__(
            self,
            id: str,
            name: str,
            context: ComputeContext,
            client_api: ApiClient,
            shared_contexts: Optional[List[ComputeContext]] = None,
            global_: Optional[bool] = None,
            status: ComputeStatus = ComputeStatus.INITIALIZING,
            type: ComputeType = ComputeType.KUBERNETES,
            features: Optional[Dict] = None,
            metadata: Optional[Dict] = None,
            settings: Optional[ComputeSettings] = None,
            url: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.context = context
        self.shared_contexts = shared_contexts if shared_contexts is not None else []
        self.global_ = global_
        self.status = status
        self.type = type
        self.features = features if features is not None else dict()
        self.metadata = metadata if metadata is not None else dict()
        self._client_api = client_api
        self._computes = None
        self._serviceDrivers = None
        self.settings = settings
        self.url = url

    @property
    def computes(self):
        if self._computes is None:
            self._computes = repositories.Computes(client_api=self._client_api)
        return self._computes

    def delete(self, skip_destroy: bool = False):
        return self.computes.delete(compute_id=self.id, skip_destroy=skip_destroy)

    def update(self):
        return self.computes.update(compute=self)

    @staticmethod
    def _protected_from_json(_json: dict, client_api: ApiClient):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            compute = Compute.from_json(_json=_json,
                                        client_api=client_api)
            status = True
        except Exception:
            compute = traceback.format_exc()
            status = False
        return status, compute

    @classmethod
    def from_json(cls, _json, client_api: ApiClient):
        return cls(
            id=_json.get('id'),
            name=_json.get('name'),
            context=ComputeContext.from_json(_json.get('context', dict())),
            shared_contexts=[ComputeContext.from_json(sc) for sc in _json.get('sharedContexts', list())],
            global_=_json.get('global'),
            status=ComputeStatus(_json.get('status')),
            type=ComputeType(_json.get('type')),
            features=_json.get('features'),
            client_api=client_api,
            metadata=_json.get('metadata'),
            settings=ComputeSettings.from_json(_json.get('settings', dict())) if _json.get('settings') else None,
            url=_json.get('url'),
        )

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'context': self.context.to_json(),
            'sharedContexts': [sc.to_json() for sc in self.shared_contexts],
            'global': self.global_,
            'status': self.status.value,
            'type': self.type.value,
            'features': self.features,
            'metadata': self.metadata,
            'settings': self.settings.to_json() if isinstance(self.settings, ComputeSettings) else self.settings,
            'url': self.url
        }


class KubernetesCompute(Compute):
    def __init__(
            self,
            id: str,
            name: str,
            context: ComputeContext,
            cluster: ComputeCluster,
            shared_contexts: Optional[List[ComputeContext]] = None,
            global_: Optional[bool] = None,
            status: ComputeStatus = ComputeStatus.INITIALIZING,
            type: ComputeType = ComputeType.KUBERNETES,
            features: Optional[Dict] = None,
            metadata: Optional[Dict] = None,
            client_api: ApiClient = None,
            settings: Optional[ComputeSettings] = None,
            url: Optional[str] = None
    ):
        super().__init__(id=id, context=context, shared_contexts=shared_contexts, global_=global_, status=status,
                         type=type, features=features, metadata=metadata, client_api=client_api, settings=settings,
                         name=name, url=url)
        self.cluster = cluster

    @classmethod
    def from_json(cls, _json, client_api: ApiClient):
        return cls(
            id=_json.get('id'),
            name=_json.get('name'),
            context=ComputeContext.from_json(_json.get('context', dict())),
            cluster=ComputeCluster.from_json(_json.get('cluster', dict())),
            shared_contexts=[ComputeContext.from_json(sc) for sc in _json.get('sharedContexts', list())],
            global_=_json.get('global'),
            status=ComputeStatus(_json.get('status')),
            type=ComputeType(_json.get('type')),
            features=_json.get('features'),
            metadata=_json.get('metadata'),
            client_api=client_api,
            settings=ComputeSettings.from_json(_json.get('settings', dict())) if _json.get('settings') else None,
            url=_json.get('url'),
        )

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'context': self.context.to_json(),
            'cluster': self.cluster.to_json(),
            'sharedContexts': [sc.to_json() for sc in self.shared_contexts],
            'global': self.global_,
            'status': self.status.value,
            'type': self.type.value,
            'features': self.features,
            'metadata': self.metadata,
            'settings': self.settings.to_json() if isinstance(self.settings, ComputeSettings) else self.settings,
            'url': self.url
        }
