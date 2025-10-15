import logging
import os

from .. import entities, repositories, services

logger = logging.getLogger(name='dtlpy')


class PackageCodebaseType:
    ITEM = 'item'
    GIT = 'git'
    FILESYSTEM = 'filesystem'
    LOCAL = 'local'


def Codebase(**kwargs):
    """
    Factory function to init all codebases types
    """
    client_api = kwargs.pop('client_api', None)
    # take it out because we dont need it from the factory method
    _dict = kwargs.pop('_dict', None)

    if kwargs['type'] == PackageCodebaseType.GIT:
        cls = GitCodebase.from_json(_json=kwargs,
                                    client_api=client_api)
    elif kwargs['type'] == PackageCodebaseType.ITEM:
        cls = ItemCodebase.from_json(_json=kwargs,
                                     client_api=client_api)
    elif kwargs['type'] == PackageCodebaseType.FILESYSTEM:
        cls = FilesystemCodebase.from_json(_json=kwargs,
                                           client_api=client_api)
    elif kwargs['type'] == PackageCodebaseType.LOCAL:
        cls = LocalCodebase.from_json(_json=kwargs,
                                      client_api=client_api)
    else:
        raise ValueError('[Codebase constructor] Unknown codebase type: {}'.format(kwargs['type']))
    return cls


class GitCodebase(entities.DlEntity):
    type = entities.DlProperty(location=['type'], _type=str, default='git')
    git_url = entities.DlProperty(location=['gitUrl'], _type=str)
    git_tag = entities.DlProperty(location=['gitTag'], _type=str)
    credentials = entities.DlProperty(location=['credentials'], _type=dict)
    _codebases = None
    client_api: 'services.ClientApi'

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return True

    @property
    def is_local(self):
        """ Return whether the codebase is locally and has no management implementations"""
        return not self.is_remote

    @property
    def codebases(self):
        if self._codebases is None:
            self._codebases = repositories.Codebases(client_api=self.client_api,
                                                     dataset=None)
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    def to_json(self) -> dict:
        _dict = self._dict.copy()
        return _dict

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(_dict=_json.copy(),
                   client_api=client_api)

    @property
    def git_user_name(self):
        return self.git_url.split('/')[-2]

    @property
    def git_repo_name(self):
        last = self.git_url.split('/')[-1]
        return os.path.splitext(last)[0]

    @property
    def git_username(self):
        if self.credentials is not None:
            return os.environ.get(
                self.credentials.get('username', {}).get('key', ''),
                None
            )
        return None

    @property
    def git_password(self):
        if self.credentials is not None:
            return os.environ.get(
                self.credentials.get('password', {}).get('key', ''),
                None
            )
        return None

    @staticmethod
    def is_git_repo(path):
        """
        :param path: `str` TODO: Currently only for local folder
        :return: `bool` testing if the path is valid git repo
        """
        return os.path.isdir(os.path.join(path, '.git'))

    def unpack(self, local_path):
        """
        Clones the git codebase
        :param local_path:
        """
        return self.codebases.clone_git(
            codebase=self,
            local_path=local_path
        )


class LocalCodebase(entities.DlEntity):
    type: str
    local_path: str
    _client_api: 'services.ClientApi'

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return False

    @property
    def is_local(self):
        """ Return whether the codebase is locally and has no management implementations"""
        return not self.is_remote

    def to_json(self):
        _json = {'type': self.type,
                 'localPath': self._local_path}
        return _json

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            client_api=client_api,
            local_path=_json.get('localPath', None),
            type=_json.get('type', None)
        )


class FilesystemCodebase(entities.DlEntity):
    type: str
    host_path: str
    container_path: str
    _client_api: 'services.ClientApi'

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return False

    @property
    def is_local(self):
        """ Return whether the codebase is locally and has no management implementations"""
        return not self.is_remote

    def to_json(self):
        _json = super().to_json()
        if self.host_path is not None:
            _json['hostPath'] = self.host_path
        if self.container_path is not None:
            _json['containerPath'] = self.container_path
        return _json

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            client_api=client_api,
            container_path=_json.get('containerPath', None),
            host_path=_json.get('hostPath', None),
            type=_json.get('type', None)
        )


class ItemCodebase(entities.DlEntity):
    type = entities.DlProperty(location=['type'], _type=str)
    item_id = entities.DlProperty(location=['itemId'], _type=str)
    _item = entities.DlProperty(location=['item'], _type=str, default=None)
    _codebases = None
    client_api: 'services.ClientApi'

    @property
    def item(self):
        if self._item is None:
            self._item = self.codebases.items_repository.get(item_id=self.item_id)
        return self._item

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return True

    @property
    def is_local(self):
        """ Return whether the codebase is locally and has no management implementations"""
        return not self.is_remote

    @property
    def codebases(self):
        if self._codebases is None:
            if self._item is not None:
                dataset = self.item.dataset
            else:
                dataset = None
            self._codebases = repositories.Codebases(client_api=self.client_api,
                                                     dataset=dataset)
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    def to_json(self) -> dict:
        _dict = self._dict.copy()
        _dict.pop('item', None)
        return _dict

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(_dict=_json.copy(),
                   client_api=client_api)

    def unpack(self, local_path):
        """
        Clones the git codebase
        :param local_path:
        """
        return self.codebases.unpack(
            codebase_id=self.item_id,
            local_path=local_path
        )

    @property
    def version(self):
        return str(self.item.name.split('.')[0])

    @property
    def md5(self):
        md5 = None
        if 'system' in self.item.metadata:
            md5 = self.item.metadata['system'].get('md5', None)
        return md5

    @md5.setter
    def md5(self, md5):
        if 'system' not in self.item.metadata:
            self.item.metadata['system'] = dict()
        self.item.metadata['system']['md5'] = md5

    @property
    def description(self):
        description = None
        if 'system' in self.item.metadata:
            description = self.item.metadata['system'].get('description', None)
        return description

    @description.setter
    def description(self, description):
        if 'system' not in self.item.metadata:
            self.item.metadata['system'] = dict()
        self.item.metadata['system']['description'] = description

    def list_versions(self):
        """
        List Codebase versions
        """
        # get codebase name
        codebase_name = self.item.filename.split('/')[len(self.item.filename.split('/')) - 2]
        return self.codebases.list_versions(codebase_name=codebase_name)
