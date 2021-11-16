from enum import Enum

import attr
import traceback
from collections import namedtuple

from .. import repositories, entities, services


class FeatureEntityType(str, Enum):
    """Available types for Feature Set entities"""
    ITEM = 'item'
    ANNOTATION = 'annotation'
    DATASET = 'dataset'


@attr.s
class FeatureSet(entities.BaseEntity):
    """
    Com entity
    """
    # platform
    id = attr.ib()
    name = attr.ib()
    tags = attr.ib()
    url = attr.ib(repr=False)
    creator = attr.ib(repr=False)
    created_at = attr.ib()
    updated_by = attr.ib()
    size = attr.ib()
    set_type = attr.ib()
    entity_type = attr.ib()
    project_id = attr.ib()
    org_id = attr.ib()

    # sdk
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _repositories = attr.ib(repr=False)

    ################
    # repositories #
    ################
    @_repositories.default
    def set_repositories(self):
        reps = namedtuple('repositories',
                          field_names=['feature_sets', 'features'])
        feature_sets_repo = repositories.FeatureSets(client_api=self._client_api)
        features_repo = repositories.Features(client_api=self._client_api, feature_set=self)
        r = reps(feature_sets=feature_sets_repo,
                 features=features_repo)
        return r

    @property
    def feature_sets(self):
        assert isinstance(self._repositories.feature_sets, repositories.FeatureSets)
        return self._repositories.feature_sets

    @property
    def features(self):
        assert isinstance(self._repositories.features, repositories.Features)
        return self._repositories.features

    @staticmethod
    def _protected_from_json(_json, client_api, is_fetched=True):
        """
        Same as from_json but with try-except to catch if error
        :param _json: entity's object json
        :param client_api:
        :return:
        """
        try:
            feature_set = FeatureSet.from_json(_json=_json,
                                               client_api=client_api,
                                               is_fetched=is_fetched)
            status = True
        except Exception:
            feature_set = traceback.format_exc()
            status = False
        return status, feature_set

    @classmethod
    def from_json(cls, _json, client_api, is_fetched=True):
        """
        Build a Feature Set entity object from a json

        :param is_fetched: is Entity fetched from Platform
        :param _json: entity's object json
        :param client_api: client_api
        :return: Feature object
        """
        inst = cls(
            id=_json.get('id', None),
            name=_json.get('name', None),
            set_type=_json.get('type', None),
            entity_type=_json.get('entityType', None),
            size=_json.get('size', None),
            url=_json.get('url', None),
            project_id=_json.get('project', None),
            created_at=_json.get('createdAt', None),
            creator=_json.get('creator', None),
            updated_by=_json.get('updatedBy', None),
            tags=_json.get('tags', None),
            client_api=client_api,
            org_id=_json.get('org', None)
        )
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """

        _json = {'id': self.id,
                 'type': self.set_type,
                 'entityType': self.entity_type,
                 'project': self.project_id,
                 'creator': self.creator,
                 'createdAt': self.created_at,
                 'updatedBy': self.updated_by,
                 'name': self.name,
                 'tags': self.tags,
                 'size': self.size,
                 'url': self.url}
        if self.org_id is not None:
            _json['org'] = self.org_id

        return _json

    def delete(self):
        """
        Delete the feature set
        """
        return self.feature_sets.delete(feature_set_id=self.id)
