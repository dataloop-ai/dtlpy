import logging
import pandas as pd
from dtlpy import entities, exceptions
from ..services.api_client import ApiClient

logger = logging.getLogger(name='dtlpy')


class Analytics:
    """
    Time series Repository
    """

    def __init__(self, client_api: ApiClient, project: entities.Project = None):
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
    def get_samples(self, query=None, return_field: str = None, return_raw: bool = False) -> pd.DataFrame:
        """
        Get Analytics table

        :param dict query: match filters to get specific data from series
        :param str return_field: name of field to return from response. default: "samples"
        :param bool return_raw: return the response with out converting
        :return: Analytics table
        :rtype: pd.DataFrame
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/analytics/query',
                                                         json_req=query)
        if success:
            if return_field is not None:
                res = response.json()[return_field]
            else:
                res = response.json()
            if return_raw:
                return res
            if isinstance(res, dict):
                df = pd.DataFrame.from_dict(res, orient="index")
            elif isinstance(res, list):
                df = pd.DataFrame(res)
            else:
                raise ValueError('unknown return type for time series: {}'.format(type(res)))
        else:
            raise exceptions.PlatformException(response)
        return df

    def report_metrics(self, samples):
        """
        Report metrics

        :param samples: table samples to report
        :return: True/ False
        :rtype: bool
        """
        if not isinstance(samples, list):
            samples = [samples]

        samples = [s.to_json() if not isinstance(s, dict) else s for s in samples]

        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/analytics/metric',
                                                         json_req=samples)
        return success
