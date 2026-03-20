
class AppException(Exception):
    """Base exception for the application"""
    pass

class RepositoryException(AppException):
    """Repository exception"""
    pass
