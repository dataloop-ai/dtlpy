import threading
import asyncio
import logging

import io

logger = logging.getLogger(name=__name__)


class AsyncThreadEventLoop(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, loop, n, name, *args, **kwargs):
        super(AsyncThreadEventLoop, self).__init__(*args, **kwargs)
        self.loop = loop
        self.n = n
        self.name = name
        self._count = 0
        self._semaphores = dict()

    def count_up(self):
        self._count += 1
        # logger.debug('eventloop {} with {} tasks'.format(self.name, self._count))

    def count_down(self):
        self._count -= 1
        # logger.debug('eventloop {} with {} tasks'.format(self.name, self._count))

    def run(self):
        logger.debug('Starting event loop "{}" with bounded semaphore to {}'.format(self.name, self.n))
        
        def exception_handler(loop, context):
            logger.debug("[Asyc] EventLoop: {} caught the following exception: {}".format(self.name, context['message']))

        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        logger.debug('Ended event loop "{}" with bounded semaphore to {}'.format(self.name, self.n))

    def semaphore(self, name):
        if name not in self._semaphores:
            self._semaphores[name] = asyncio.Semaphore(self.n, loop=self.loop)
        return self._semaphores[name]

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)  # here


class AsyncResponse:
    def __init__(self, text, _json, async_resp):
        self.text = text
        self._json = _json
        self.async_resp = async_resp

    def json(self):
        return self._json

    @property
    def status_code(self):
        return self.async_resp.status

    @property
    def reason(self):
        return self.async_resp.reason

    @property
    def ok(self):
        return self.async_resp.status < 400

    @property
    def request(self):
        return self.async_resp.request_info

    @property
    def headers(self):
        return self.async_resp.headers


class DummyErrorResponse:
    def __init__(self, error, trace):
        self.status = 3001  # SDK Error
        self.reason = trace
        self.error = error
        self.request_info = {}
        self.headers = {}


class AsyncResponseError(AsyncResponse):
    def __init__(self, error, trace):
        async_resp = DummyErrorResponse(error=error, trace=trace)
        _json = {'error': error}
        text = error
        super().__init__(async_resp=async_resp,
                         _json=_json,
                         text=text)


class AsyncUploadStream(io.IOBase):
    def __init__(self, buffer, callback=None):
        self.buffer = buffer
        self.buffer.seek(0)
        self.callback = callback

    def read(self, size):
        if self.callback is not None:
            self.callback(size)
        return self.buffer.read(size)
