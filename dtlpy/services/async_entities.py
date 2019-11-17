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


class AsyncUploadStream(io.IOBase):
    def __init__(self, buffer, callback=None):
        self.buffer = buffer
        self.buffer.seek(0)
        self.callback = callback

    def read(self, size):
        if self.callback is not None:
            self.callback(size)
        return self.buffer.read(size)
