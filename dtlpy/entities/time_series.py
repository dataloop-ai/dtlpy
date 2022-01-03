import attr
from .. import entities
import logging

logger = logging.getLogger(name='dtlpy')


@attr.s
class TimeSeries(entities.BaseEntity):
    """
    Time Series object
    """
    # platform
    created_at = attr.ib()
    updated_at = attr.ib(repr=False)
    owner = attr.ib()
    name = attr.ib()
    id = attr.ib()
    # entities
    _project = attr.ib(repr=False)

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at

    @property
    def project(self):
        assert isinstance(self._project, entities.Project)
        return self._project

    @classmethod
    def from_json(cls, _json, project):
        """
        Build a TimeSeries entity object from a json

        :param _json: _json response from host
        :param project: project id
        :return: Time Series object
        """
        return cls(
            created_at=_json.get('createdAt', None),
            updated_at=_json.get('updatedAt', None),
            owner=_json.get('owner', None),
            name=_json.get('name', None),
            id=_json.get('id', None),
            project=project,
        )

    def to_json(self):
        """
        Returns platform _json format of object

        :return: platform json format of object
        """
        _json = attr.asdict(self,
                            filter=attr.filters.exclude(attr.fields(TimeSeries)._project,
                                                        attr.fields(TimeSeries).created_at,
                                                        attr.fields(TimeSeries).updated_at,
                                                        ))
        _json['createdAt'] = self.created_at
        _json['updatedAt'] = self.updated_at
        return _json

    ##########
    # Entity #
    ##########
    def delete(self):
        """
        delete the time series
        :return:
        """
        return self.project.times_series.delete(series=self)

    ##########
    # Series #
    ##########
    def samples(self, filters=None):
        """
        get the time table according to filters
        :param filters: Filters entity or a dictionary containing filters parameters
        :return:
        """
        return self.project.times_series.get_samples(series_id=self.id, filters=filters)

    def add_samples(self, data):
        """
        add data to time series table
        :param data:
        :return:
        """
        return self.project.times_series.add_samples(series_id=self.id, data=data)

    def delete_samples(self, filters):
        """
        add data to time series table
        :param filters: Filters entity or a dictionary containing filters parameters
        :return:
        """
        return self.project.times_series.delete_samples(series_id=self.id, filters=filters)

    ###########
    # Samples #
    ###########
    def sample(self, sample_id):
        """
        get a sample line by id
        :param sample_id:
        :return:
        """
        return self.project.times_series.get_sample(series_id=self.id,
                                                    sample_id=sample_id)

    def update_sample(self, sample_id, data):
        """
        Update a sample line by id
        :param sample_id:
        :param data:
        :return:
        """
        return self.project.times_series.update_sample(series_id=self.id,
                                                       sample_id=sample_id,
                                                       data=data)

    def delete_sample(self, sample_id):
        """
        Delete a single sample line from time series
        :param sample_id:
        :return:
        """
        return self.project.times_series.delete_sample(series_id=self.id,
                                                       sample_id=sample_id)
