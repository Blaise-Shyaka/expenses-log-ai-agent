class AppException(Exception):
    """Base exception for the application"""


class RepositoryException(AppException):
    """Repository exception"""


class NotFoundException(AppException):
    """The requested resource does not exist, or belongs to another user"""


class AlreadyExistsException(AppException):
    """The resource being created already exists"""
