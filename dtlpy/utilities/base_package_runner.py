class BaseServiceRunner:
    _do_reset = False
    _auto_refresh_dtlpy_token = None
    _refresh_dtlpy_token = None

    def do_reset(self):
        self._do_reset = True


class Progress:

    def update(self, status=None, progress=0, message=None, output=None):
        pass
