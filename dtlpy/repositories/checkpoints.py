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

    def __init__(self, client_api, model=None, project=None, artifacts=None, project_id=None):
        self._client_api = client_api
        self._project = project
        self._model = model
        self._artifacts = artifacts
        self._project_id = project_id

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            if self._project_id is not None:
                projects = repositories.Projects(client_api=self._client_api)
                self._project = projects.get(project_id=self._project_id)
        if self._project is None:
            if self._model is not None:
                if self._model._project is not None:
                    self._project = self._model._project
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.checkpoints repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    @property
    def artifacts(self):
        assert isinstance(self.project.artifacts, repositories.Artifacts)
        return self.project.artifacts

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
            checkpoints = self.list(entities.Filters(resource=entities.FiltersResource.CHECKPOINT,
                                                     field='name',
                                                     values=checkpoint_name))
            if checkpoints.items_count == 0:
                raise exceptions.PlatformException(
                    error='404',
                    message='Checkpoint not found. Name: {}'.format(checkpoint_name))
            elif checkpoints.items_count > 1:
                raise exceptions.PlatformException(
                    error='400',
                    message='More than one file found by the name of: {}'.format(checkpoint_name))
            checkpoint = checkpoints[0]
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Checked out not found, must provide either checkpoint id or checkpoint name')

        return checkpoint

    def _build_entities_from_response(self, response_items):
        jobs = [None for _ in range(len(response_items))]
        pool = self._client_api.thread_pools(pool_name='entity.create')

        # return triggers list
        for i_service, service in enumerate(response_items):
            jobs[i_service] = pool.apply_async(entities.Checkpoint._protected_from_json,
                                               kwds={'client_api': self._client_api,
                                                     '_json': service,
                                                     'model': self._model,
                                                     'project': self._project})
        # wait for all jobs
        _ = [j.wait() for j in jobs]
        # get all results
        results = [j.get() for j in jobs]
        # log errors
        _ = [logger.warning(r[1]) for r in results if r[0] is False]
        # return good jobs
        return miscellaneous.List([r[1] for r in results if r[0] is True])

    def _list(self, filters):
        url = '/query/machine-learning'
        # TODO change endpoint to models/{}/query with filters

        # query_params = {
        #     'modelId': model_id,
        #     'creator': creator,
        #     'name': checkpoint_name
        # }
        #
        # if self._project is not None:
        #     query_params['projects'] = self._project.id
        #
        # url += '?{}'.format(urlencode({key: val for key, val in query_params.items() if val is not None}, doseq=True))

        # request
        success, response = self._client_api.gen_request(req_type='POST',
                                                         path=url,
                                                         json_req=filters.prepare())
        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    def list(self, filters=None, page_offset=None, page_size=None):
        """
        List project checkpoints
        :return:
        """
        # default filters
        if filters is None:
            filters = entities.Filters(resource=entities.FiltersResource.CHECKPOINT)
            if self._project is not None:
                filters.add(field='projectId', values=self._project.id)
            if self._model is not None:
                filters.add(field='modelId', values=self._model.id)

        # assert type filters
        if not isinstance(filters, entities.Filters):
            raise exceptions.PlatformException('400', 'Unknown filters type')

        # page size
        if page_size is None:
            # take from default
            page_size = filters.page_size
        else:
            filters.page_size = page_size

        # page offset
        if page_offset is None:
            # take from default
            page_offset = filters.page
        else:
            filters.page = page_offset

        paged = entities.PagedEntities(items_repository=self,
                                       filters=filters,
                                       page_offset=page_offset,
                                       page_size=page_size,
                                       client_api=self._client_api)
        paged.get_page()
        return paged

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
        else:
            if self._project is not None and self._project.id != project_id:
                self._project = None
            self._project_id = project_id

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
        filters.add(field='type', values='dir')
        filters.recursive = False
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
            artifacts = self.artifacts.items_repository.download(
                filters=filters,
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
