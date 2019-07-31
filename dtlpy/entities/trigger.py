import attr
from .. import entities


@attr.s
class Trigger:
    """
    Trigger Entity
    """
    #######################
    # Platform attributes #
    #######################
    id = attr.ib()
    url = attr.ib()
    createdAt = attr.ib()
    updatedAt = attr.ib()
    resource = attr.ib()
    actions = attr.ib()
    active = attr.ib()

    ##############################
    # different name in platform #
    ##############################
    filters = attr.ib()
    deployment_ids = attr.ib()
    project_id = attr.ib()

    ##################
    # SDK attributes #
    ##################
    _project = attr.ib()
    client_api = attr.ib()

    @classmethod
    def from_json(cls, _json, client_api, project):
        return cls(
            id=_json['id'],
            url=_json['url'],
            project_id=_json.get('project', project.id),
            createdAt=_json['createdAt'],
            updatedAt=_json['updatedAt'],
            deployment_ids=_json['deploymentIds'],
            filters=_json['filter'],
            resource=_json['resource'],
            actions=_json['actions'],
            active=_json['active'],
            client_api=client_api,
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
        _json = attr.asdict(self, filter=attr.filters.exclude(attr.fields(Trigger).client_api,
                                                              attr.fields(Trigger).filters,
                                                              attr.fields(Trigger).project_id,
                                                              attr.fields(Trigger).deployment_ids,
                                                              attr.fields(Trigger)._project))
        # rename
        _json['filter'] = self.filters
        _json['project'] = self.project_id
        _json['deploymentIds'] = self.deployment_ids

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
