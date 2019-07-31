import logging
import pandas as pd

from dtlpy import entities, utilities, PlatformException


class TimesSeries:
    def __init__(self, client_api, project=None):
        self.logger = logging.getLogger('dataloop.repository.time_series')
        self.client_api = client_api
        self.project = project

    def list(self):
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/projects/{}/timeSeries'.format(self.project.id))
        if success:
            sessions = utilities.List(
                [entities.TimeSeries.from_json(_json=_json,
                                               project=self.project)
                 for _json in response.json()])
        else:
            self.logger.exception('Platform error listing sessions')
            raise PlatformException(response)
        return sessions

    def get(self, series_id):
        # get series
        success, response = self.client_api.gen_request(req_type='get',
                                                        path='/projects/{}/timeSeries/{}'.format(self.project.id,
                                                                                                 series_id))
        if success:
            session = entities.TimeSeries.from_json(_json=response.json(),
                                                    project=self.project)
        else:
            self.logger.exception('Platform error listing sessions')
            raise PlatformException(response)
        return session

    def get_table(self, series, filters=None):
        if filters is None:
            filters = dict()
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/projects/{}/timeSeries/{}/query'.format(self.project.id,
                                                                                                       series.id),
                                                        json_req=filters)
        if success:
            res = response.json()
            df = pd.DataFrame(res['samples'])
        else:
            raise PlatformException(response)
        return df

    def create(self, name):
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/projects/{}/timeSeries'.format(self.project.id),
                                                        json_req={'name': name})
        if success:
            session = entities.TimeSeries.from_json(_json=response.json(),
                                                    project=self.project)
        else:
            self.logger.exception('Platform error listing sessions')
            raise PlatformException(response)
        return session

    def add(self, series, data):
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/projects/{}/timeSeries/{}/add'.format(self.project.id,
                                                                                                     series.id),
                                                        json_req=data)

        if success:
            pass
            # session = entities.TimeSeries.from_json(_json=response.json(),
            #                                         project=self.project)
        else:
            self.logger.exception('Platform adding data to time series. id: {}'.format(series.id))
            raise PlatformException(response)

    def delete(self, series_id=None, series=None):
        """
        Delete a Time Series
        :param series_id: optional - search by id
        :param series: optional - Session object
        :return: True
        """
        if series_id is not None:
            pass
        elif series is not None and isinstance(series, entities.TimeSeries):
            series_id = series.id
        else:
            self.logger.exception(
                'Must choose by at least one. "series_id" or "series"')
            raise ValueError(
                'Must choose by at least one. "series_id" or "series"')
        success, response = self.client_api.gen_request(req_type='delete',
                                                        path='/projects/{}/timeSeries/{}'.format(self.project.id,
                                                                                                 series_id))
        if not success:
            self.logger.exception('Platform error deleting a series:')
            raise PlatformException(response)
        return True
