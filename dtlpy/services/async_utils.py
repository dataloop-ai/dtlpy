import threading
import asyncio
import logging
import io

logger = logging.getLogger(name='dtlpy')


class AsyncThreadEventLoop(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, loop, n, *args, **kwargs):
        super(AsyncThreadEventLoop, self).__init__(*args, **kwargs)
        self.loop = loop
        self.n = n
        self._count = 0
        self._semaphores = dict()

    def count_up(self):
        self._count += 1

    def count_down(self):
        self._count -= 1

    def run(self):
        def exception_handler(loop, context):
            logger.debug(
                "[Asyc] EventLoop: caught the following exception: {}".format(context['message']))

        self.loop.set_exception_handler(exception_handler)
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        logger.debug('Ended event loop with bounded semaphore to {}'.format(self.n))

    def semaphore(self, name, n=None):
        if n is None:
            n = self.n
        else:
            n = min(n, self.n)
        if name not in self._semaphores:
            self._semaphores[name] = asyncio.BoundedSemaphore(n)
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
    def __init__(self, buffer, callback=None, name='', chunk_timeout=10, max_retries=3):
        self.buffer = buffer
        self.buffer.seek(0)
        self.callback = callback
        self._name = name
        self.chunk_timeout = chunk_timeout
        self.max_retries = max_retries

    @property
    def name(self):
        return self._name

    async def async_read(self, size):
        retries = 0
        while retries < self.max_retries:
            try:
                import sys
                if sys.version_info < (3, 9):
                    loop = asyncio.get_event_loop()
                    data = await asyncio.wait_for(loop.run_in_executor(None, self.buffer.read, size),
                                                  timeout=self.chunk_timeout)
                else:
                    data = await asyncio.wait_for(asyncio.to_thread(self.buffer.read, size), timeout=self.chunk_timeout)
                if self.callback is not None:
                    self.callback(size)
                return data
            except asyncio.TimeoutError:
                retries += 1
                logger.warning(
                    f"Chunk read timed out after {self.chunk_timeout} seconds. Retrying {retries}/{self.max_retries}...")

        raise Exception(f"Chunk read failed after {self.max_retries} retries due to timeouts")

    def read(self, size):
        return asyncio.run(self.async_read(size))
