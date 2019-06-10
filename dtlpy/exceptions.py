import requests
class PlatformException(Exception):

    def __init__(self, error=None, message=None):
        self.status_code = None
        self.message = message

        exceptions = {
                    '404': NotFound, 
                    '500': InternalServerError,
                    '403': Forbidden,
                    '400': BadRequest,
                    '401': Unauthorized,
                    '408': RequestTimeout
                    }

        if not type(error) == requests.models.Response:
            self.status_code = error
            self.message = message
        else:
            if hasattr(error, 'status_code'):
                self.status_code = str(error.status_code)
            if hasattr(error, 'text'):
                self.message = '\ntext: %s' % error.text

        if self.status_code in exceptions:
            raise exceptions[self.status_code](self.status_code, self.message)
        else:
            raise UnknownException(self.status_code, self.message)
        
class ExceptionMain(Exception):
    def __init__(self, status_code='Unknown Status Code', message='Unknown Error Message'):
        return super().__init__(status_code, message)

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

class UnknownException(ExceptionMain):
    pass

