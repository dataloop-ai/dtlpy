import os
import logging
import attr

from .. import utilities, entities

logger = logging.getLogger('dataloop.package')


@attr.s
class Package(entities.Item):
    """
    Package object
    """
    description = attr.ib(default=None)
    md5 = attr.ib(default=None)
    version = attr.ib(default=None, kw_only=True)

    @classmethod
    def from_json(cls, _json, dataset, client_api):
        """
        Build a Package entity object from a json

        :param _json: _json respons form host
        :param dataset: dataset in which the annotation's item is located
        :param client_api: client_api
        :return: Package object
        """
        if 'md5' in _json['metadata']['system']:
            md5 = _json['metadata']['system']['md5']
        else:
            md5 = None
        return cls(
            dataset=dataset,
            annotated=_json['annotated'],
            annotations_link=_json['annotations'],
            stream=_json['stream'],
            thumbnail=_json['thumbnail'],
            url=_json['url'],
            filename=_json['filename'],
            id=_json['id'],
            metadata=_json['metadata'],
            mimetype=_json['metadata']['system']['mimetype'],
            name=_json['name'],
            size=_json['metadata']['system']['size'],
            system=_json['metadata']['system'],
            type=_json['type'],
            version=int(os.path.splitext(_json['name'])[0]),
            md5=md5,
            client_api=client_api,
            annotations=None,
            width=None,
            height=None
        )

    def set_description(self, description):
        self.description = description

    def set_md5(self, md5):
        self.md5 = md5

    def print(self):
        utilities.List([self]).print()

    def unpack(self, local_path=None, version=None):
        """
        Unpack package locally. Download source code and unzip
        :param local_path: local path to save package source
        :param version: package version to unpack. default - latest
        :return: String (dirpath)
        """
        return self.dataset.project.packages.unpack(package_id=self.id, local_path=local_path, version=version)

    def list_versions(self):
        """
        List Package versions
        """
        # get package name
        package_name = self.filename.split('/')[len(self.filename.split('/')) - 2]
        return self.dataset.project.packages.list_versions(package_name=package_name)
