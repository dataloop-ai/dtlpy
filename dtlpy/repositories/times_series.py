import logging
import pandas as pd
import datetime
from dtlpy import entities, miscellaneous, exceptions, services

logger = logging.getLogger(name='dtlpy')


class TimesSeries:
    """
    Time series Repository
    """

    def __init__(self, client_api: services.ApiClient, project: entities.Project = None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self) -> entities.Project:
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.times_series repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project: entities.Project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ############
    #  methods #
    ############
    def create(self, series_name) -> entities.TimeSeries:
        """
        Create a new time series

        :param str series_name: name
        :return: TimeSeries object
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries'.format(self.project.id),
                                                         json_req={'name': series_name})
        if success:
            ts = entities.TimeSeries.from_json(_json=response.json(),
                                               project=self.project)
        else:
            raise exceptions.PlatformException(response)
        assert isinstance(ts, entities.TimeSeries)
        return ts

    def list(self) -> miscellaneous.List[entities.TimeSeries]:
        """
        List all time series for project

        :return:
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/timeSeries'.format(self.project.id))
        if success:
            tss = miscellaneous.List([entities.TimeSeries.from_json(_json=_json, project=self.project)
                                      for _json in response.json()])
        else:
            raise exceptions.PlatformException(response)
        return tss

    def get(self, series_name=None, series_id=None) -> entities.TimeSeries:
        """
        Get time series entity

        :param str series_name: by name
        :param str series_id: by id
        :return:
        """
        if series_id is not None:
            # get series
            success, response = self._client_api.gen_request(req_type='get',
                                                             path='/projects/{}/timeSeries/{}'.format(self.project.id,
                                                                                                      series_id))
            if success:
                ts = entities.TimeSeries.from_json(_json=response.json(),
                                                   project=self.project)
            else:
                raise exceptions.PlatformException(response)
            # verify input service name is same as the given id
            if series_name is not None and ts.name != series_name:
                logger.warning(
                    "Mismatch found in timeSeries.get: series_name is different then timeSeries.name:"
                    " {!r} != {!r}".format(
                        series_name,
                        ts.name))
        elif series_name is not None:
            tss = self.list()
            ts = [ts for ts in tss if ts.name == series_name]
            if not ts:
                # empty list
                raise exceptions.PlatformException(error='404',
                                                   message='Time Series not found. Name: {}'.format(series_name))
            elif len(ts) > 1:
                raise exceptions.PlatformException(error='400',
                                                   message='More than one Time Series with same name.')
            else:
                ts = ts[0]
        else:
            raise exceptions.PlatformException(error='400',
                                               message='Must choose by "series_id" or "series_name"')
        assert isinstance(ts, entities.TimeSeries)
        return ts

    def delete(self, series_id=None, series=None):
        """
        Delete a Time Series

        :param str series_id: optional - search by id
        :param series: optional - TimeSeries object
        :return: True
        :rtype: bool
        """
        if series_id is not None:
            pass
        elif series is not None and isinstance(series, entities.TimeSeries):
            series_id = series.id
        else:
            msg = 'Must choose by at least one of: "series_id", "series"'
            logger.error(msg)
            raise ValueError(msg)
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path='/projects/{}/timeSeries/{}'.format(self.project.id,
                                                                                                  series_id))
        if not success:
            raise exceptions.PlatformException(response)
        logger.info('Time series id {} deleted successfully'.format(series_id))
        return True

    #########
    # Table #
    #########
    def delete_samples(self, series_id, filters):
        """
        Delete samples from table

        :param str series_id: time series id
        :param dtlpy.entities.filters.Filters filters: query to delete by
        :return:
        """
        filters = self._validate_query(query=filters)
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries/{}/remove'.format(
                                                             self.project.id,
                                                             series_id),
                                                         json_req=filters)
        if not success:
            raise exceptions.PlatformException(response)
        return True

    @staticmethod
    def _validate_query(query):
        default_start_time = 0
        default_end_time = datetime.datetime.now().timestamp() * 1000

        if query is None:
            query = dict(startTime=default_start_time, endTime=default_end_time)
        else:
            query['startTime'] = query.get('startTime', default_start_time)
            query['endTime'] = query.get('endTime', default_end_time)

        return query

    def get_samples(self, series_id, filters=None) -> pd.DataFrame:
        """
        Get Series table

        :param str series_id: TimeSeries id
        :param dtlpy.entities.filters.Filters filters: match filters to get specific data from series
        :return:
        """
        filters = self._validate_query(query=filters)
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries/{}/query'.format(self.project.id,
                                                                                                        series_id),
                                                         json_req=filters)
        if success:
            res = response.json()['samples']
            if isinstance(res, dict):
                df = pd.DataFrame([res])
            elif isinstance(res, list):
                df = pd.DataFrame(res)
            else:
                raise ValueError('unknown return type for time series: {}'.format(type(res)))
        else:
            raise exceptions.PlatformException(response)
        return df

    def add_samples(self, series_id, data):
        """
        Add samples to series

        :param str series_id: TimeSeries id
        :param data: list or dictionary of samples
        :return:
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries/{}/add'.format(self.project.id,
                                                                                                      series_id),
                                                         json_req=data)

        if not success:
            raise exceptions.PlatformException(response)
        return response.json()

    ######################
    # Samples Operations #
    ######################
    def get_sample(self, series_id, sample_id) -> pd.DataFrame:
        """
        Get single sample from series

        :param str series_id: TimeSeries id
        :param str sample_id: id of sample line
        :return:
        """
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/timeSeries/{}/samples/{}'.format(
                                                             self.project.id,
                                                             series_id,
                                                             sample_id))
        if success:
            res = response.json()
            if isinstance(res, dict):
                df = pd.DataFrame([res])
            elif isinstance(res, list):
                df = pd.DataFrame(res)
            else:
                raise ValueError('unknown return type for time series: {}'.format(type(res)))
        else:
            raise exceptions.PlatformException(response)
        return df

    def update_sample(self, series_id, sample_id, data):
        """
        Add data to existing sample

        :param str series_id: time series id
        :param str sample_id: sample line id
        :param dict data: dictionary
        :return:
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries/{}/samples/{}'.format(
                                                             self.project.id,
                                                             series_id,
                                                             sample_id),
                                                         json_req=data)
        if not success:
            raise exceptions.PlatformException(response)

    def delete_sample(self, series_id, sample_id):
        """
        Delete single samples form time series

        :param str series_id:
        :param str sample_id:
        :return:
        """
        success, response = self._client_api.gen_request(req_type='delete',
                                                         path='/projects/{}/timeSeries/{}/samples/{}'.format(
                                                             self.project.id,
                                                             series_id,
                                                             sample_id))
        if not success:
            raise exceptions.PlatformException(response)
        return True
