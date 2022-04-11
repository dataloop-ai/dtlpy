import threading
import traceback
import logging
import queue
import os

logger = logging.getLogger('dtlpy')


class Events(threading.Thread):
    def __init__(self, client_api, *args, **kwargs):
        super(Events, self).__init__(*args, **kwargs)
        self.client_api = client_api
        self.q = queue.Queue()

    def track(self, event):
        try:
            return_type, resp = self.client_api.gen_request(req_type='POST',
                                                            path='/analytics/metric/pendo',
                                                            json_req=event,
                                                            log_error=False)
            if not resp.ok:
                logger.debug('failed send event to analytics: {}'.format(resp.text))
        except Exception:
            logger.debug('failed send track event: {}'.format(traceback.format_exc()))

    def run(self):
        while True:
            try:
                event = self.q.get()
                self.track([event])
                self.q.task_done()
            except Exception:
                logger.exception('failed in loop')

    def put(self, event, resp=None, path=None):
        send_event = True
        if path is not None and ('sdk' in path or not path.startswith('/projects')):
            send_event = False

        if resp is not None and send_event:
            event_source = os.path.normpath(event.filename).split('\\')[-1][:-4]
            event_payload = {'event': 'dtlpy:' + event_source,
                             'properties': {'sdk_event': event.function + '_' + event_source}}
            if event_payload.get('event', None) == 'dtlpy:project' and event.function in ['create', 'delete']:
                if event.function in ['create']:
                    event_payload['properties'].update({'project_id': resp.json()['id'],
                                                        'project_name': resp.json()['name']})
            else:
                send_event = False
        else:
            event_payload = event
        if send_event:
            self.q.put(event_payload)
