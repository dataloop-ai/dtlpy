import logging
from .. import utilities, entities
import attr

logger = logging.getLogger('dataloop.artifact')


@attr.s
class Artifact(entities.Item):
    description = attr.ib(default=None)
    creator = attr.ib(default=None)

    @classmethod
    def from_json(cls, _json, dataset, client_api):
        """
        Build an Artifact entity object from a json
        :param _json: _json response form host
        :param dataset: Artifact's dataset
        :param client_api: client_api
        :return: Artifact object
        """

        return cls(
            client_api=client_api,
            dataset=dataset,
            creator=_json.get('creator', None),
            description=_json.get('description', None),
            annotated=_json.get('annotated', None),
            annotations_link=_json.get('annotations_link', None),
            stream=_json.get('stream', None),
            thumbnail=_json.get('thumbnail', None),
            url=_json.get('url', None),
            filename=_json.get('filename', None),
            id=_json['id'],
            metadata=_json.get('metadata', None),
            mimetype=None,
            name=_json.get('name', None),
            size=None,
            system=None,
            type=_json.get('type', None),
            annotations=None,
            height=None,
            width=None,
            fps=None
        )

    def print(self):
        """

        :return:
        """
        utilities.List([self]).print()

    def download(self, session_id=None, task_id=None, local_path=None, overwrite=False, relative_path=False):
        """
        Download artifact binary. Get artifact by name, id or type
        :param local_path: artifact will be saved to this filepath
        :param relative_path: optional - default = False
        :param overwrite: optional - default = False
        :param session_id:
        :param task_id:
        :return: Artifact object
        """

        return self.dataset.project.artifacts.download(artifact_id=self.id, artifact_name=self.name,
                                                       session_id=session_id, task_id=task_id,
                                                       local_path=local_path, overwrite=overwrite,
                                                       relative_path=relative_path)
