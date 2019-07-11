import logging
import pandas as pd

from .. import entities, utilities, PlatformException


class TimeSeries:
    def __init__(self, client_api, project=None):
        self.logger = logging.getLogger('dataloop.tasks')
        self.client_api = client_api
        self.project = project

    def get(self, filters=None):
        if filters is None:
            filters = dict()
        else:
            filters = {'filters': filters}
        success, response = self.client_api.gen_request(req_type='post',
                                                        path='/projects/{}/timeSeries'.format(self.project.id),
                                                        json_req=filters)
        if success:
            res = response.json()
            df = pd.DataFrame(res['samples'])
        else:
            raise PlatformException(response)
        return df
