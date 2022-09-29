import threading
import time
import traceback
import logging
import queue
import os

logger = logging.getLogger(name='dtlpy')


class Events(threading.Thread):
    def __init__(self, client_api, *args, **kwargs):
        super(Events, self).__init__(*args, **kwargs)
        self.client_api = client_api
        self.q = queue.Queue()
        self.mapping_events_dict = {
            'project': {'method': ['create', 'delete'], 'route': '/projects'},
            'task': {'method': ['create'], 'route': '/annotationtasks'},
        }

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

    def _valid_events(self, path):
        for route in self.mapping_events_dict.values():
            if path.startswith(route['route']) and 'sdk' not in path:
                return True
        return False

    def _add_info(self, event_payload, function, resp):
        if function in ['create']:
            event_source = event_payload.get('event', None)
            resp_json = resp.json()
            if event_source == 'dtlpy:project':
                event_payload['properties'].update({'project_id': resp_json['id'],
                                                    'project_name': resp_json['name']})
            if event_source == 'dtlpy:task' and function in ['create']:
                if 'createTaskPayload' in resp_json.get('spec', {}):
                    task_payload = resp_json.get('spec', {}).get('createTaskPayload', {})
                else:
                    task_payload = resp_json
                metadata = task_payload.get('metadata', {}).get('system', {})
                task_type = task_payload.get('spec', {}).get('type', {})
                allocation_method = 'Distribution'
                if 'batchSize' in metadata and 'maxBatchWorkload' in metadata and 'allowedAssignees' in metadata:
                    allocation_method = 'Pulling'
                event_payload['properties'].update({'task_type': task_type,
                                                    'allocation_method': allocation_method})

    def put(self, event, resp=None, path=None):
        send_event = True
        if path is not None and not self._valid_events(path=path):
            send_event = False

        if resp is not None and send_event:
            event_source = os.path.normpath(event.filename).split('\\')[-1][:-4]
            event_payload = {'event': 'dtlpy:' + event_source,
                             'properties': {'sdk_event': event.function + '_' + event_source}}
            if event_source in self.mapping_events_dict and \
                    event.function in self.mapping_events_dict[event_source]['method']:
                self._add_info(event_payload=event_payload, function=event.function, resp=resp)
            else:
                send_event = False
        else:
            event_payload = event
        if send_event:
            self.q.put(event_payload)
