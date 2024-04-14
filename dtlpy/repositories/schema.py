from typing import List
import logging

from .. import entities, exceptions
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class UnsearchablePaths:
    """
    Unsearchable Paths

    """

    def __init__(self, client_api: ApiClient, dataset: entities.Dataset = None):
        self._client_api = client_api
        self._dataset = dataset

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Cannot perform action WITHOUT Dataset entity in {} repository.'.format(
                    self.__class__.__name__) + ' Please use dataset.schema or set a dataset')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    def __unsearchable_paths_request(self, payload):
        """
        Set unsearchable paths in dataset schema
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/datasets/{}/schema/items'.format(self.dataset.id),
                                                         json_req=
                                                         {
                                                             "unsearchablePaths": payload
                                                         })
        if not success:
            raise exceptions.PlatformException(response)

        resp = response.json()
        if isinstance(resp, dict):
            command = entities.Command.from_json(_json=resp,
                                                 client_api=self._client_api)

            try:
                command.wait()
            except Exception as e:
                logger.error('Command failed: {}'.format(e))
        else:
            logger.warning(resp)
        return success

    def add(self, paths: List[str]):
        """
        Add metadata paths to `unsearchablePaths` to exclude keys under these paths from indexing, making them unsearchable through the Dataset Browser UI and DQL queries.

        :param paths: list of paths to create
        :return: true if success, else raise exception
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dataset.schema.unsearchable_paths.add(paths=['metadata.key1', 'metadata.key2'])
        """
        return self.__unsearchable_paths_request(payload={"add": paths})

    def remove(self, paths: List[str]):
        """
        Remove metadata paths from `unsearchablePaths` to index keys under these paths, making them searchable through the Dataset Browser UI and DQL queries.

        :param paths: list of paths to delete
        :return: true if success, else raise exception
        :rtype: bool

        **Example**:

        .. code-block:: python

            success = dataset.schema.unsearchable_paths.remove(paths=['metadata.key1', 'metadata.key2'])
        """
        return self.__unsearchable_paths_request(payload={"remove": paths})


class Schema:
    """
    Schema Repository
    """

    def __init__(self, client_api: ApiClient, dataset: entities.Dataset):
        self._client_api = client_api
        self.dataset = dataset
        self.unsearchable_paths = UnsearchablePaths(client_api=self._client_api, dataset=dataset)

    ###########
    # methods #
    ###########
    def get(self):
        """
        Get dataset schema

        :return: dataset schema
        :rtype: dict

        **Example**:

        .. code-block:: python

            json = dataset.schema.get()
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/datasets/{}/schema'.format(self.dataset.id))
        if not success:
            raise exceptions.PlatformException(response)

        return response.json()
