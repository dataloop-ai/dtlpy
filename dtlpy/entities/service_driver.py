import traceback
from typing import Dict
from ..services.api_client import ApiClient
from .. import repositories
from .compute import ComputeContext, ComputeType

class ServiceDriver:
    def __init__(
            self,
            name: str,
            context: ComputeContext,
            compute_id: str,
            client_api: ApiClient,
            type: ComputeType = None,
            created_at: str = None,
            updated_at: str = None,
            namespace: str = None,
            metadata: Dict = None,
            url: str = None,
            archived: bool = None,
            id: str = None,
            is_cache_available: bool = None
    ):
        self.name = name
        self.context = context
        self.compute_id = compute_id
        self.client_api = client_api
        self.type = type or ComputeType.KUBERNETES
        self.created_at = created_at
        self.updated_at = updated_at
        self.namespace = namespace
        self.metadata = metadata
        self.url = url
        self.archived = archived
        self.id = id
        self.is_cache_available = is_cache_available
        self._service_drivers = None
        self._client_api = client_api

    @property
    def service_drivers(self):
        if self._service_drivers is None:
            self._service_drivers = repositories.ServiceDrivers(client_api=self._client_api)
        return self._service_drivers

    @staticmethod
    def _protected_from_json(_json: dict, client_api: ApiClient):
        """
        Same as from_json but with try-except to catch if error

        :param _json: platform json
        :param client_api: ApiClient entity
        :return:
        """
        try:
            service = ServiceDriver.from_json(_json=_json,
                                              client_api=client_api)
            status = True
        except Exception:
            service = traceback.format_exc()
            status = False
        return status, service

    @classmethod
    def from_json(cls, _json, client_api: ApiClient):
        return cls(
            name=_json.get('name'),
            context=ComputeContext.from_json(_json.get('context', dict())),
            compute_id=_json.get('computeId'),
            client_api=client_api,
            type=_json.get('type', None),
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            namespace=_json.get('namespace', None),
            metadata=_json.get('metadata', None),
            url=_json.get('url', None),
            archived=_json.get('archived', None),
            id=_json.get('id', None),
            is_cache_available=_json.get('isCacheAvailable', None)
        )

    def to_json(self):
        _json = {
            'name': self.name,
            'context': self.context.to_json(),
            'computeId': self.compute_id,
            'type': self.type,
        }
        if self.created_at is not None:
            _json['createdAt'] = self.created_at
        if self.updated_at is not None:
            _json['updatedAt'] = self.updated_at
        if self.namespace is not None:
            _json['namespace'] = self.namespace
        if self.metadata is not None:
            _json['metadata'] = self.metadata
        if self.url is not None:
            _json['url'] = self.url
        if self.archived is not None:
            _json['archived'] = self.archived
        if self.id is not None:
            _json['id'] = self.id
        if self.is_cache_available is not None:
            _json['isCacheAvailable'] = self.is_cache_available

        return _json

    def delete(self):
        """
        Delete a service driver
        """
        return self.service_drivers.delete(service_driver_id=self.id)

    def update(self):
        """
        Update a service driver
        """
        return self.service_drivers.update(service_driver=self)