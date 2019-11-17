import traceback
import logging
import attr
import copy

from .. import miscellaneous, entities, repositories

logger = logging.getLogger(name=__name__)


@attr.s
class Package(entities.Item):
    """
    Package object
    """

    @staticmethod
    def _protected_from_json(_json, client_api, dataset=None):
        """
        Same as from_json but with try-except to catch if error
        :param _json:
        :param client_api:
        :param dataset:
        :return:
        """
        try:
            item = Package.from_json(_json=_json,
                                     client_api=client_api,
                                     dataset=dataset)
            status = True
        except Exception:
            item = traceback.format_exc()
            status = False
        return status, item

    @classmethod
    def from_json(cls, _json, client_api, dataset=None):
        """
        Build a Package entity object from a json

        :param _json: _json respons form host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: client_api
        :return: Package object
        """
        return cls(
            # sdk
            platform_dict=copy.deepcopy(_json),
            client_api=client_api,
            dataset=dataset,
            # params
            annotations_link=_json.get('annotations', None),
            createdAt=_json.get('createdAt', None),
            datasetId=_json.get('datasetId', None),
            annotated=_json.get('annotated', None),
            thumbnail=_json.get('thumbnail', None),
            dataset_url=_json.get('dataset', None),
            hidden=_json.get('hidden', False),
            stream=_json.get('stream', None),
            dir=_json.get('dir', None),
            filename=_json['filename'],
            metadata=_json['metadata'],
            name=_json['name'],
            type=_json['type'],
            url=_json['url'],
            id=_json['id'])

    @property
    def version(self):
        return str(self.name.split('.')[0])

    @property
    def md5(self):
        md5 = None
        if 'system' in self.metadata:
            md5 = self.metadata['system'].get('md5', None)
        return md5

    @md5.setter
    def md5(self, md5):
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system']['md5'] = md5

    @property
    def description(self):
        description = None
        if 'system' in self.metadata:
            description = self.metadata['system'].get('description', None)
        return description

    @description.setter
    def description(self, description):
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system']['description'] = description

    @property
    def packages(self):
        if self._repositories.packages is None:
            if self.dataset is not None and self.dataset.project is not None:
                packages = self.dataset.project.packages
            else:
                packages = repositories.Packages(client_api=self._client_api,
                                                 dataset=self.dataset)
            self._repositories = self._repositories._replace(packages=packages)
        assert isinstance(self._repositories.packages, repositories.Packages)
        return self._repositories.packages

    def unpack(self, local_path=None, version=None):
        """
        Unpack package locally. Download source code and unzip
        :param local_path: local path to save package source
        :param version: package version to unpack. default - latest
        :return: String (dirpath)
        """
        return self.packages.unpack(package_id=self.id, local_path=local_path, version=version)

    def list_versions(self):
        """
        List Package versions
        """
        # get package name
        package_name = self.filename.split('/')[len(self.filename.split('/')) - 2]
        return self.packages.list_versions(package_name=package_name)

    def print(self):
        miscellaneous.List([self]).print()
