import traceback
from enum import Enum
from typing import List, Dict
from ..services.api_client import ApiClient
from .. import repositories, entities


class ClusterProvider(str, Enum):
    GCP = 'gcp'
    AWS = 'aws'
    AZURE = 'azure'
    HPC = 'hpc'
    LOCAL = 'local'
    RANCHER_K3S = 'rancher-k3s'
    RANCHER_RKE = 'rancher-rke'
    OPENSHIFT = 'openshift'


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


class ComputeSettings(entities.DlEntity):
    default_namespace: str = entities.DlProperty(location=['defaultNamespace'], _type=str)
    consumption_method: str = entities.DlProperty(location=['consumptionMethod'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Toleration(entities.DlEntity):
    effect: str = entities.DlProperty(location=['effect'], _type=str)
    key: str = entities.DlProperty(location=['key'], _type=str)
    operator: str = entities.DlProperty(location=['operator'], _type=str)
    value: str = entities.DlProperty(location=['value'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class DeploymentResource(entities.DlEntity):
    gpu: int = entities.DlProperty(location=['gpu'], _type=int)
    cpu: int = entities.DlProperty(location=['cpu'], _type=int)
    memory: str = entities.DlProperty(location=['memory'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class DeploymentResources(entities.DlEntity):
    request: DeploymentResource = entities.DlProperty(location=['request'], _kls='DeploymentResource')
    limit: DeploymentResource = entities.DlProperty(location=['limit'], _kls='DeploymentResource')

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class NodePool(entities.DlEntity):
    name: str = entities.DlProperty(location=['name'], _type=str)
    is_dl_type_default: bool = entities.DlProperty(location=['isDlTypeDefault'], _type=bool)
    is_monitoring_configuration: bool = entities.DlProperty(location=['isMonitoringConfiguration'], _type=bool)
    dl_types: List[str] = entities.DlProperty(location=['dlTypes'], _type=list)
    tolerations: List[Toleration] = entities.DlProperty(location=['tolerations'], _kls='Toleration', default=[])
    description: str = entities.DlProperty(location=['description'], _type=str, default='')
    node_selector: str = entities.DlProperty(location=['nodeSelector'], _type=str, default='')
    preemptible: bool = entities.DlProperty(location=['preemptible'], _type=bool, default=False)
    deployment_resources: DeploymentResources = entities.DlProperty(location=['deploymentResources'], _kls='DeploymentResources')

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class AuthenticationIntegration(entities.DlEntity):
    id: str = entities.DlProperty(location=['id'], _type=str)
    type: str = entities.DlProperty(location=['type'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Authentication(entities.DlEntity):
    integration: AuthenticationIntegration = entities.DlProperty(location=['integration'], _kls='AuthenticationIntegration')

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class ComputeCluster(entities.DlEntity):
    name: str = entities.DlProperty(location=['name'], _type=str)
    endpoint: str = entities.DlProperty(location=['endpoint'], _type=str)
    kubernetes_version: str = entities.DlProperty(location=['kubernetesVersion'], _type=str)
    provider: str = entities.DlProperty(location=['provider'], _type=str)
    node_pools: List[NodePool] = entities.DlProperty(location=['nodePools'], _kls='NodePool', default=[])
    metadata: Dict = entities.DlProperty(location=['metadata'], _type=dict, default={})
    authentication: Authentication = entities.DlProperty(location=['authentication'], _kls='Authentication')
    plugins: dict = entities.DlProperty(location=['plugins'], _type=dict)
    deployment_configuration: Dict = entities.DlProperty(location=['deploymentConfiguration'], _type=dict, default={})

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)

    @classmethod
    def from_setup_json(cls, devops_output, integration):
        _json = {
            'name': devops_output['config']['name'],
            'endpoint': devops_output['config']['endpoint'],
            'kubernetesVersion': devops_output['config']['kubernetesVersion'],
            'provider': devops_output['config']['provider'],
            'nodePools': devops_output['config']['nodePools'],
            'metadata': {},
            'authentication': {'integration': {'id': integration.id, 'type': integration.type}},
            'plugins': devops_output['config'].get('plugins'),
            'deploymentConfiguration': devops_output['config'].get('deploymentConfiguration', {})
        }
        return cls(_dict=_json)


class ComputeContext(entities.DlEntity):
    labels: List[str] = entities.DlProperty(location=['labels'], _type=list, default=[])
    org: str = entities.DlProperty(location=['org'], _type=str)
    project: str = entities.DlProperty(location=['project'], _type=str)

    def to_json(self) -> dict:
        return self._dict.copy()

    @classmethod
    def from_json(cls, _json):
        return cls(_dict=_json)


class Compute(entities.DlEntity):
    id: str = entities.DlProperty(location=['id'], _type=str)
    name: str = entities.DlProperty(location=['name'], _type=str)
    context: ComputeContext = entities.DlProperty(location=['context'], _kls='ComputeContext')
    shared_contexts: List[ComputeContext] = entities.DlProperty(location=['sharedContexts'], _kls='ComputeContext', default=[])
    global_: bool = entities.DlProperty(location=['global'], _type=bool)
    status: str = entities.DlProperty(location=['status'], _type=str, default=ComputeStatus.INITIALIZING.value)
    type: str = entities.DlProperty(location=['type'], _type=str, default=ComputeType.KUBERNETES.value)
    features: Dict = entities.DlProperty(location=['features'], _type=dict, default={})
    metadata: Dict = entities.DlProperty(location=['metadata'], _type=dict, default={})
    settings: ComputeSettings = entities.DlProperty(location=['settings'], _kls='ComputeSettings')
    url: str = entities.DlProperty(location=['url'], _type=str)

    def __init__(self, _dict=None, client_api: ApiClient = None, **kwargs):
        super().__init__(_dict=_dict, **kwargs)
        self._client_api = client_api
        self._computes = None
        self._serviceDrivers = None

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
        return cls(_dict=_json, client_api=client_api)

    def to_json(self) -> dict:
        return self._dict.copy()


class KubernetesCompute(Compute):
    cluster: ComputeCluster = entities.DlProperty(location=['cluster'], _kls='ComputeCluster')

    @classmethod
    def from_json(cls, _json, client_api: ApiClient):
        return cls(_dict=_json, client_api=client_api)

    def to_json(self) -> dict:
        return self._dict.copy()
