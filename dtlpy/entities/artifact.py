import logging
from .. import miscellaneous, entities
import attr
import copy

logger = logging.getLogger(name=__name__)


@attr.s
class Artifact(entities.Item):

    @classmethod
    def from_json(cls, _json, client_api, dataset=None, project=None):
        """
        Build an Artifact entity object from a json
        :param project:
        :param _json: _json response from host
        :param dataset: Artifact's dataset
        :param client_api: client_api
        :return: Artifact object
        """

        return cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            project=project,
            # params
            annotations_link=_json.get('annotations_link', None),
            createdAt=_json.get('createdAt', None),
            datasetId=_json.get('datasetId', None),
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
            id=_json['id'])

    def print(self):
        """

        :return:
        """
        miscellaneous.List([self]).print()
