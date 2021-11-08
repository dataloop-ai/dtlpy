import threading
from .. import entities


class BaseServiceRunner:
    _do_reset = False
    _auto_refresh_dtlpy_token = None
    _refresh_dtlpy_token = None
    _threads_terminated = list()
    _threads_terminated_lock = threading.Lock()
    _service_entity = None

    def do_reset(self):
        self._do_reset = True

    def _terminate(self, tid):
        with self._threads_terminated_lock:
            self._threads_terminated.append(tid)

    def kill_event(self):
        ident = threading.get_ident()
        if ident in self._threads_terminated:
            with self._threads_terminated_lock:
                self._threads_terminated.pop(self._threads_terminated.index(ident))
            raise InterruptedError('Execution received termination signal')

    @property
    def service_entity(self) -> entities.Service:
        assert isinstance(self._service_entity, entities.Service), "service_entity must be a dl.Service object"
        return self._service_entity

    @service_entity.setter
    def service_entity(self, value):
        assert isinstance(value, entities.Service), "service_entity must be a dl.Service object"
        self._service_entity = value


class Progress:

    def update(self, status=None, progress=0, message=None, output=None):
        pass
