import traceback
import logging
import attr
import os

from .. import entities

logger = logging.getLogger(name='dtlpy')


class ArtifactType:
    ITEM = 'item'
    LOCAL = 'local'
    LINK = 'link'


@attr.s
class Artifact:
    @staticmethod
    def _protected_from_json(
            _json: dict,
            client_api,
            dataset=None,
            project=None,
            is_fetched: bool = True):
        """
        Same as from_json but with try-except to catch if error

        :param dict _json: platform json
        :param client_api: ApiClient entity
        :param dtlpy.entities.dataset.Dataset dataset: dataset entity
        :param dtlpy.entities.project.Project project: project entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: status and the artifact object
        """
        try:
            artifact = Artifact.from_json(_json=_json,
                                          client_api=client_api,
                                          dataset=dataset,
                                          project=project,
                                          is_fetched=is_fetched)
            status = True
        except Exception:
            artifact = traceback.format_exc()
            status = False
        return status, artifact

    @classmethod
    def from_json(cls,
                  _json: dict,
                  client_api,
                  dataset=None,
                  project=None,
                  model=None,
                  is_fetched: bool = True):
        artifact_type = _json.get('type', None)
        if artifact_type is None:
            raise ValueError('Missing `type` in artifact.')
        if artifact_type in ['file', 'dir']:
            # used as item directly
            artifact = ItemArtifact.from_json(_json=_json,
                                              client_api=client_api,
                                              dataset=dataset,
                                              project=project,
                                              model=model,
                                              is_fetched=is_fetched
                                              )
        elif artifact_type in ['item']:
            # used as an item reference
            artifact = ItemArtifact.from_json(_json={'id': _json.get('itemId'),
                                                     'type': 'item'},
                                              client_api=client_api,
                                              dataset=dataset,
                                              project=project,
                                              model=model,
                                              is_fetched=False
                                              )
        elif artifact_type in ['local']:
            artifact = LocalArtifact.from_json(_json=_json)
        elif artifact_type in ['link']:
            artifact = LinkArtifact.from_json(_json=_json)
        else:
            raise ValueError('Unknown dl.Artifact `type`: {}'.format(artifact_type))
        return artifact


@attr.s
class ItemArtifact(entities.Item, Artifact):

    def to_json(self, as_artifact=False):
        """
        Return dict representation of the artifact
        Using a flag to keep old artifact behaviour (for packages, returning the item itself and not the artifact)

        :param as_artifact: it True, return the Artifact json, otherwise, return item for backward compatibility
        :return:
        """
        if as_artifact:
            _json = {'type': self.type,
                     'itemId': self.id}
        else:
            _json = super(ItemArtifact, self).to_json()
        return _json


@attr.s
class LocalArtifact(Artifact):
    type = 'local'
    local_path = attr.ib(repr=True)

    @classmethod
    def from_json(cls, _json: dict):
        """
        Build an Artifact entity object from a json

        :param dict _json: platform json
        :return: Artifact object
        :rtype: dtlpy.entities.artifact.Artifact
        """

        inst = cls(local_path=_json.get('localPath'))
        return inst

    def to_json(self, as_artifact=True):
        """
        Return dict representation of the artifact
        Using a flag to keep old artifact behaviour (for packages).
        This flag is only relevant for ItemArtifact

        :param as_artifact: not is use, only to keep same signature for all artifacts
        :return:
        """
        _json = {'type': self.type,
                 'localPath': self.local_path}
        return _json


@attr.s
class LinkArtifact(Artifact):
    type = 'link'
    url = attr.ib(repr=True)
    filename = attr.ib(repr=True)

    @classmethod
    def from_json(cls,
                  _json: dict,
                  is_fetched: bool = True):
        """
        Build an Artifact entity object from a json

        :param dict _json: platform json
        :rtype: dtlpy.entities.artifact.Artifact
        """
        url = _json.get('url')
        filename = _json.get('filename')
        if filename is None:
            filename = os.path.basename(url)
        inst = cls(url=url,
                   filename=filename)
        inst.is_fetched = is_fetched
        return inst

    def to_json(self, as_artifact=True):
        """
        Return dict representation of the artifact
        Using a flag to keep old artifact behaviour (for packages).
        This flag is only relevant for ItemArtifact

        :param as_artifact: not is use, only to keep same signature for all artifacts
        :return:
        """
        _json = {'type': self.type,
                 'url': self.url}
        return _json
