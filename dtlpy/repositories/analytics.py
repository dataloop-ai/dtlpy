import logging
import pandas as pd

from dtlpy import entities, exceptions, services

logger = logging.getLogger(name=__name__)


class Analytics:
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
    def get_samples(self, query=None, return_field='samples', return_raw=False) -> pd.DataFrame:
        """
        Get Analytics table
        :param query: match filters to get specific data from series
        :param return_field: name of field to return from response. default: "samples"
        :param return_raw: return the response with out converting
        :return:
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/analytics/itemQuery'.format(
                                                             self.project.id),
                                                         json_req=query)
        if success:
            res = response.json()[return_field]
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
