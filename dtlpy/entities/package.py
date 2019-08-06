import logging
import attr
import copy

from .. import utilities, entities, PlatformException

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
        try:
            md5 = _json['metadata']['system']['md5']
        except KeyError:
            md5 = None
        if _json['type'] == 'dir':
            return cls(
                client_api=client_api,
                dataset=dataset,
                annotated=None,
                annotations_link=None,
                stream=None,
                thumbnail=None,
                url=_json['url'],
                filename=_json['filename'],
                id=_json['id'],
                metadata=_json['metadata'],
                mimetype=None,
                name=_json['name'],
                size=None,
                system=None,
                type=_json['type'],
                fps=None,
                width=None,
                height=None,
                md5=md5,
                annotations=None,
                platform_dict=copy.deepcopy(_json),
                created_at=_json.get('createdAt', None))
        elif _json['type'] == 'file':
            return cls(
                client_api=client_api,
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
                fps=None,
                width=None,
                height=None,
                md5=md5,
                annotations=None,
                platform_dict=copy.deepcopy(_json),
                created_at=_json.get('createdAt', None)
            )
        else:
            message = 'Unknown item type: %s' % _json['type']
            raise PlatformException('404', message)

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
