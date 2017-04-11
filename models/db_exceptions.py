import traceback

class DatabaseException(Exception):
    """Base class for all database exceptions."""
    def __init__(self, message):
        super(DatabaseException, self).__init__(message)
        self.traceback = traceback.format_exc()
        self.status_code = 400

    def to_dict(self):
        return {'message': str(self)}


class InvalidParameter(DatabaseException):
    """Define the exception that the request has invalid or missing parameters.
    """
    def __init__(self, message):
        super(InvalidParameter, self).__init__(message)
        self.status_code = 400

class Unauthorized(DatabaseException):
    """Define the exception for invalid user login."""
    def __init__(self, message):
        super(Unauthorized, self).__init__(message)
        self.status_code = 401
