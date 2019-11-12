

class BasePluginRunner:
    _do_reset = False

    def do_reset(self):
        self._do_reset = True


class Progress:

    def update(self, status=None, progress=0, message=None, output=None):
        pass
