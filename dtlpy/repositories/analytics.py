import logging
import pandas as pd

from dtlpy import entities, exceptions

logger = logging.getLogger(name=__name__)


class Analytics:
    """
    Time series Repository
    """

    def __init__(self, client_api, project=None):
        self._client_api = client_api
        self._project = project

    ############
    # entities #
    ############
    @property
    def project(self):
        if self._project is None:
            raise exceptions.PlatformException(
                error='2001',
                message='Missing "project". need to set a Project entity or use project.times_series repository')
        assert isinstance(self._project, entities.Project)
        return self._project

    @project.setter
    def project(self, project):
        if not isinstance(project, entities.Project):
            raise ValueError('Must input a valid Project entity')
        self._project = project

    ############
    #  methods #
    ############
    def get_samples(self, query=None):
        """
        Get Analytics table
        :param query: match filters to get specific data from series
        :return:
        """
        success, response = self._client_api.gen_request(req_type='post',
                                                         path='/projects/{}/analytics/itemQuery'.format(self.project.id),
                                                         json_req=query)
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