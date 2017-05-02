import traceback

class UIHTTPException(Exception):
    def __init__(self, message, status_code):
        super(UIHTTPException, self).__init__(message)
        self.traceback = traceback.format_exc()
        self.status_code = status_code

    def to_dict(self):
        return {'message': str(self)}


class UITokenExpire(UIHTTPException):
    """Define the exception for token expire"""
    def __init__(self, message):
        super(UITokenExpire, self).__init__(message, 410)
