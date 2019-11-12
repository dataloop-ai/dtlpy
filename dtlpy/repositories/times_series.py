import logging
import pandas as pd

from dtlpy import entities, miscellaneous, PlatformException

logger = logging.getLogger(name=__name__)


class TimesSeries:
    def __init__(self, client_api, project=None):
        self._client_api = client_api
        self._project = project

    @property
    def project(self):
        assert isinstance(self._project, entities.Project)
        return self._project

    def list(self):
        success, response = self._client_api.gen_request(req_type='get',
                                                         path='/projects/{}/timeSeries'.format(self.project.id))
        if success:
            tss = miscellaneous.List([entities.TimeSeries.from_json(_json=_json, project=self.project)
                                      for _json in response.json()])
        else:
            raise PlatformException(response)
        return tss

    def get(self, series_name=None, series_id=None):
        if series_id is not None:
            # get series
            success, response = self._client_api.gen_request(req_type='get',
                                                             path='/projects/{}/timeSeries/{}'.format(self.project.id,
                                                                                                      series_id))
            if success:
                ts = entities.TimeSeries.from_json(_json=response.json(),
                                                   project=self.project)
            else:
                raise PlatformException(response)
        elif series_name is not None:
            tss = self.list()
            ts = [ts for ts in tss if ts.name == series_name]
            if not ts:
                # empty list
                raise PlatformException('404', 'Time Series not found. Name: {}'.format(series_name))
            elif len(ts) > 1:
                # more than one time series
                logger.warning('More than one Time Series with same name. Please "get" by id')
                raise PlatformException('400', 'More than one Time Series with same name.')
            else:
                ts = ts[0]
        else:
            raise PlatformException('400', 'Must choose by "series_id" or "series_name"')
        assert isinstance(ts, entities.TimeSeries)
        return ts

    def get_table(self, series, filters=None):
        if filters is None:
            filters = dict()
        success, response = self._client_api.gen_request(req_type='post',
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
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries'.format(self.project.id),
                                                         json_req={'name': name})
        if success:
            ts = entities.TimeSeries.from_json(_json=response.json(),
                                               project=self.project)
        else:
            raise PlatformException(response)
        assert isinstance(ts, entities.TimeSeries)
        return ts

    def add(self, series, data):
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/timeSeries/{}/add'.format(self.project.id,
                                                                                                      series.id),
                                                         json_req=data)

        if not success:
            raise PlatformException(response)

    def delete(self, series_id=None, series=None):
        """
        Delete a Time Series
        :param series_id: optional - search by id
        :param series: optional - TimeSeries object
        :return: True
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
            raise PlatformException(response)
        logger.info('Time series id {} deleted successfully'.format(series_id))
        return True
