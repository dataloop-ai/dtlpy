import attr


@attr.s
class Assignment:
    """
    Assignment object
    """
    
    # platform
    name = attr.ib()
    annotator = attr.ib()
    status = attr.ib()
    projectId = attr.ib()
    metadata = attr.ib()
    id = attr.ib()
    url = attr.ib()
    
    # sdk
    _client_api = attr.ib()
    _task = attr.ib(default=None)
    _project = attr.ib(default=None)
    
    @classmethod
    def from_json(cls, _json, client_api, project=None, task=None):
        return cls(
            name=_json.get('name', None),
            annotator=_json.get('annotator', None),
            status=_json.get('status', None),
            projectId=_json.get('projectId', None),
            metadata=_json.get('metadata', dict()),
            url=_json.get('url', None),
            id=_json['id'],
            client_api=client_api,
            project=project,
            task=task
        )
    
    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        return attr.asdict(self, filter=attr.filters.exclude(attr.fields(Assignment)._client_api,
                                                             attr.fields(Assignment)._project,
                                                             attr.fields(Assignment)._task))
