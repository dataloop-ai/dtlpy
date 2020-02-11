import requests

from . import services


class PlatformException(Exception):

    def __init__(self, error=None, message=None):
        self.status_code = None
        self.message = message

        exceptions = {
            '400': BadRequest,
            '401': Unauthorized,
            '403': Forbidden,
            '404': NotFound,
            '408': RequestTimeout,
            '500': InternalServerError,
            '600': TokenExpired,
            '1001': ShowAnnotationError,
            '1002': ExportAnnotationError,
            '2001': MissingEntity
        }

        if isinstance(error, requests.models.Response) or isinstance(error, services.AsyncResponse):
            if hasattr(error, 'status_code'):
                self.status_code = str(error.status_code)
            if hasattr(error, 'text'):
                try:
                    self.message = error.json().get('message', error.text)
                except Exception:
                    self.message = error.text

        else:
            self.status_code = error
            self.message = message

        if self.status_code in exceptions:
            raise exceptions[self.status_code](status_code=self.status_code, message=self.message)
        else:
            raise UnknownException(status_code=self.status_code, message=self.message)


class ExceptionMain(Exception):
    def __init__(self, status_code='Unknown Status Code', message='Unknown Error Message'):
        self.status_code = status_code
        self.message = message
        super().__init__(status_code, message)


class NotFound(ExceptionMain):
    pass


class InternalServerError(ExceptionMain):
    pass


class Forbidden(ExceptionMain):
    pass


class BadRequest(ExceptionMain):
    pass


class Unauthorized(ExceptionMain):
    pass


class RequestTimeout(ExceptionMain):
    pass


class TokenExpired(ExceptionMain):
    pass


class UnknownException(ExceptionMain):
    pass


class MissingEntity(ExceptionMain):
    pass


##########################
# annotations exceptions #
##########################
class ShowAnnotationError(ExceptionMain):
    """ raised when error in annotations drawing"""
    pass


class ExportAnnotationError(ExceptionMain):
    """ raised when error in annotations drawing"""
    pass
