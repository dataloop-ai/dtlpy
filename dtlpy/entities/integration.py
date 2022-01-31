import logging
import attr

from .. import entities, services, exceptions, repositories

logger = logging.getLogger(name='dtlpy')


@attr.s
class Integration(entities.BaseEntity):
    """
    Integration object
    """
    id = attr.ib()
    name = attr.ib()
    type = attr.ib()
    org = attr.ib()
    created_at = attr.ib()
    created_by = attr.ib()
    update_at = attr.ib()
    _client_api = attr.ib(type=services.ApiClient, repr=False)
    _project = attr.ib(default=None, repr=False)

    @classmethod
    def from_json(cls,
                  _json: dict,
                  client_api: services.ApiClient,
                  is_fetched=True):
        """
        Build a Integration entity object from a json

        :param _json: _json response from host
        :param client_api: ApiClient entity
        :param is_fetched: is Entity fetched from Platform
        :return: Integration object
        """
        inst = cls(id=_json.get('id', None),
                   name=_json.get('name', None),
                   created_by=_json.get('createdBy', None),
                   created_at=_json.get('createdAt', None),
                   update_at=_json.get('updateAt', None),
                   type=_json.get('type', None),
                   org=_json.get('org', None),
                   client_api=client_api)
        inst.is_fetched = is_fetched
        return inst

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        :rtype: dict
        """
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Integration)._client_api,
                                                              attr.fields(Integration)._project))
        return _json

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    def update(self, new_name: str):
        """
        Update the integrations name

        :param str new_name: new name
        """
        if self.project is not None:
            identifier = self.project
        elif self.org is not None:
            identifier = repositories.organizations.Organizations(client_api=self._client_api).get(
                organization_id=self.org)
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        identifier.integrations.update(new_name=new_name, integrations_id=self.id)

    def delete(self,
               sure: bool = False,
               really: bool = False) -> bool:
        """
        Delete integrations from the Organization

        :param bool sure: are you sure you want to delete?
        :param bool really: really really?
        :return: True
        :rtype: bool
        """
        if self.project is not None:
            identifier = self.project
        elif self.org is not None:
            identifier = repositories.organizations.Organizations(client_api=self._client_api).get(
                organization_id=self.org)
        else:
            raise exceptions.PlatformException(
                error='400',
                message='Must provide an identifier in inputs')

        return identifier.integrations.delete(integrations_id=self.id, sure=sure, really=really)
