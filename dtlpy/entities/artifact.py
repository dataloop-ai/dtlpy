import traceback
import logging
import attr
import copy

from .. import entities

logger = logging.getLogger(name='dtlpy')


@attr.s
class Artifact(entities.Item):

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
                                          project=None,
                                          is_fetched=True)
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
                  is_fetched: bool = True):
        """
        Build an Artifact entity object from a json

        :param dict _json: platform json
        :param dl.ApiClient client_api: ApiClient entity
        :param dtlpy.entities.dataset.Dataset dataset: dataset entity
        :param dtlpy.entities.project.Project project: project entity
        :param bool is_fetched: is Entity fetched from Platform
        :return: Artifact object
        :rtype: dtlpy.entities.artifact.Artifact
        """

        inst = cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            project=project,
            # params
            annotations_link=_json.get('annotations_link', None),
            annotations_count=_json.get('annotationsCount', None),
            created_at=_json.get('createdAt', None),
            dataset_id=_json.get('datasetId', None),
            thumbnail=_json.get('thumbnail', None),
            annotated=_json.get('annotated', None),
            dataset_url=_json.get('dataset', None),
            filename=_json.get('filename', None),
            metadata=_json.get('metadata', None),
            hidden=_json.get('hidden', False),
            stream=_json.get('stream', None),
            name=_json.get('name', None),
            type=_json.get('type', None),
            dir=_json.get('dir', None),
            url=_json.get('url', None),
            id=_json['id'],
            spec=_json.get('spec', None),
            creator=_json.get('creator', None))
        inst.is_fetched = is_fetched
        return inst
