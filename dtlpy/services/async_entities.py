import io


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
        self.status = 400
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
