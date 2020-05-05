import logging
import uuid
import os
from urllib.parse import urlencode

from .. import entities, repositories, exceptions, miscellaneous

logger = logging.getLogger(name=__name__)


class Checkpoints:
    """
    Checkpoints Repository
    """

    def __init__(self, client_api, model=None, project=None, artifacts=None):
        self._client_api = client_api
        self._project = project
        self._model = model
        self._artifacts = artifacts

    ############
    # entities #
    ############
    ############
    @property
    def project(self):
        if self._project is None:
            try:
                self._project = repositories.Projects(client_api=self._client_api).get()
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "project". need to set a Project entity or use project.checkpoints repository')
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def artifacts(self):
        if self._artifacts is None:
            try:
                self._artifacts = repositories.Artifacts(client_api=self._client_api,
                                                         project=self._project)
            except exceptions.NotFound:
                raise exceptions.PlatformException(
                    error='2001',
                    message='Missing "artifacts"')
        return self._artifacts

    @property
    def model(self):
        assert isinstance(self._model, entities.Model)
        return self._model

    ###########
    # methods #
    ###########
    def get(self, checkpoint_name=None, checkpoint_id=None):
        """
        Get checkpoint object

        :param checkpoint_id:
        :param checkpoint_name:
        :return: checkpoint object
        """

        if checkpoint_id is not None:
            success, response = self._client_api.gen_request(req_type="get",
                                                             path="/checkpoints/{}".format(checkpoint_id))
            if not success:
                raise exceptions.PlatformException(response)
            checkpoint = entities.Checkpoint.from_json(client_api=self._client_api,
                                                       _json=response.json(),
                                                       project=self._project,
                                                       model=self.model)
        elif checkpoint_name is not None:
            checkpoints = self.list(checkpoint_name=checkpoint_name)
            if len(checkpoints) == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message='Checkpoint not found. Name: {}'.format(checkpoint_name))
            elif len(checkpoints) > 1:
                raise exceptions.PlatformException(
                    error='400',
                    message='More than one file found by the name of: {}'.format(checkpoint_name))
            checkpoint = checkpoints[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Checked out not found, must provide either checkpoint id or checkpoint name')

        return checkpoint

    def list(self, model_id=None, creator=None, checkpoint_name=None):
        """
        List project checkpoints
        :return:
        """
        url = '/checkpoints'
        query_params = {
            'modelId': model_id,
            'creator': creator,
            'name': checkpoint_name
        }

        if self._project is not None:
            query_params['projects'] = self._project.id

        url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='get',
                                                         path=url)
        if not success:
            raise exceptions.PlatformException(response)

        # return checkpoints list
        checkpoints = miscellaneous.List()
        for checkpoint in response.json()['items']:
            checkpoints.append(entities.Checkpoint.from_json(client_api=self._client_api,
                                                             _json=checkpoint,
                                                             project=self._project,
                                                             model=self.model))
        return checkpoints

    def upload(self, checkpoint_name, local_path, description=None, project_id=None, scope='private'):
        """
        Create a checkpoint in platform

        :param local_path: path of artifacts to upload
        :param checkpoint_name:
        :param description:
        :param project_id:
        :param scope: 'global'
        :return: Checkpoint Entity
        """
        if project_id is None:
            project_id = self.project.id

        # upload artifacts
        artifacts = self.artifacts.upload(filepath=local_path,
                                          model_name=self.model.name,
                                          checkpoint_name='{}_{}'.format(checkpoint_name, str(uuid.uuid1())))
        # get dir item of the artifacts
        if isinstance(artifacts, list):
            if len(artifacts) == 0:
                raise ValueError('nothing uploaded')
            item = artifacts[0]
        elif isinstance(artifacts, entities.Item):
            item = artifacts
        else:
            raise ValueError('bad upload')
        filters = entities.Filters(field='filename', values=item.dir)
        filters.recursive = False
        filters.show_dirs = True
        pages = self.artifacts.dataset.items.list(filters=filters)
        if pages.items_count != 1:
            raise ValueError('cant find dir of artifacts item. received items count: {}'.format(pages.items_count))
        artifact_id = pages.items[0].id

        # create payload for request
        payload = {'name': checkpoint_name,
                   'description': description,
                   'modelId': self.model.id,
                   'projectId': project_id,
                   'artifactId': artifact_id,
                   'scope': scope}

        # request
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/checkpoints',
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        checkpoint = entities.Checkpoint.from_json(_json=response.json(),
                                                   client_api=self._client_api,
                                                   project=self._project,
                                                   model=self.model)
        return checkpoint

    def download(self, checkpoint_id=None, checkpoint=None, local_path=None):
        if checkpoint is None:
            if checkpoint_id is None:
                raise exceptions.PlatformException('400', 'Please provide checkpoint or checkpoint id')
            checkpoint = self.get(checkpoint_id=checkpoint_id)

        if local_path is None:
            local_path = os.getcwd()

        checkpoint_artifact_item = self.artifacts.get(artifact_id=checkpoint.artifacts_id)
        if checkpoint_artifact_item.type == 'dir':
            filters = entities.Filters(field='dir', values='{}*'.format(checkpoint_artifact_item.filename))
            artifacts = self.artifacts.items_repository.download(filters=filters,
                                                                 local_path=local_path,
                                                                 to_items_folder=False,
                                                                 without_relative_path=checkpoint_artifact_item.filename)
        else:
            artifacts = checkpoint_artifact_item.download(local_path=local_path)
        return artifacts

    def delete(self, checkpoint=None, checkpoint_name=None, checkpoint_id=None):
        """
        Delete Checkpoint object

        :param checkpoint:
        :param checkpoint_name:
        :param checkpoint_id:
        :return: True
        """
        # get id and name
        if checkpoint is None:
            checkpoint = self.get(checkpoint_id=checkpoint_id, checkpoint_name=checkpoint_name)
        try:
            self.artifacts.items_repository.delete(item_id=checkpoint.artifacts_id)
        except exceptions.NotFound:
            pass

        # request
        success, response = self._client_api.gen_request(
            req_type="delete",
            path="/checkpoints/{}".format(checkpoint.id)
        )

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return results
        return True

    def update(self, checkpoint):
        """
        Update Checkpoint changes to platform

        :param checkpoint:
        :return: Checkpoint entity
        """
        assert isinstance(checkpoint, entities.Checkpoint)

        # payload
        payload = checkpoint.to_json()

        # request
        success, response = self._client_api.gen_request(req_type='patch',
                                                         path='/checkpoints/{}'.format(checkpoint.id),
                                                         json_req=payload)

        # exception handling
        if not success:
            raise exceptions.PlatformException(response)

        # return entity
        return entities.Checkpoint.from_json(_json=response.json(),
                                             client_api=self._client_api,
                                             project=self._project,
                                             model=self.model)
