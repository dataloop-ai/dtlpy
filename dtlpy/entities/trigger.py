import attr
from .. import entities, services


@attr.s
class Trigger:
    """
    Trigger Entity
    """
    #######################
    # Platform attributes #
    #######################
    name = attr.ib()
    id = attr.ib()
    url = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    resource = attr.ib()
    actions = attr.ib()
    active = attr.ib()
    executionMode = attr.ib()
    scope = attr.ib()
    deploymentId = attr.ib()

    ########
    # temp #
    ########
    special = attr.ib()

    ##############################
    # different name in platform #
    ##############################
    filters = attr.ib()
    project_id = attr.ib()

    ##################
    # SDK attributes #
    ##################
    _project = attr.ib()
    _client_api = attr.ib(type=services.ApiClient)

    @classmethod
    def from_json(cls, _json, client_api, project):
        filters = _json.get('filter', dict())

        return cls(
            id=_json['id'],
            name=_json.get('name', None),
            executionMode=_json.get('executionMode', None),
            project_id=_json.get('project', project.id),
            createdAt=_json.get('createdAt', None),
            updatedAt=_json.get('updatedAt', None),
            resource=_json.get('resource', None),
            special=_json.get('special', None),
            actions=_json.get('actions', None),
            active=_json.get('active', None),
            scope=_json.get('scope', None),
            deploymentId=_json.get('deploymentId', None),
            url=_json.get('url', None),
            client_api=client_api,
            filters=filters,
            project=project
        )

    @property
    def project(self):
        assert isinstance(self._project, entities.Project)
        return self._project

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        # get excluded
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Trigger)._client_api,
                                                              attr.fields(Trigger).project_id,
                                                              attr.fields(Trigger)._project,
                                                              attr.fields(Trigger).special,
                                                              attr.fields(Trigger).filters))
        # rename
        _json['project'] = self.project_id
        _json['filter'] = self.filters

        return _json

    def delete(self):
        """
        Delete Trigger object

        :return: True
        """
        return self.project.triggers.delete(trigger_id=self.id)

    def update(self):
        """

        :return: Trigger entity
        """
        return self.project.triggers.update(trigger=self)
