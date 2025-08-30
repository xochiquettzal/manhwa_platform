# exceptions.py
class ManhwaPlatformError(Exception):
    """Base exception for the Manhwa Platform"""
    pass

class ValidationError(ManhwaPlatformError):
    """Raised when data validation fails"""
    pass

class AuthenticationError(ManhwaPlatformError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(ManhwaPlatformError):
    """Raised when user is not authorized to perform an action"""
    pass

class DatabaseError(ManhwaPlatformError):
    """Raised when database operations fail"""
    pass

class ExternalAPIError(ManhwaPlatformError):
    """Raised when external API calls fail"""
    pass

class ImportError(ManhwaPlatformError):
    """Raised when data import operations fail"""
    pass

class SearchError(ManhwaPlatformError):
    """Raised when search operations fail"""
    pass

class FileUploadError(ManhwaPlatformError):
    """Raised when file upload operations fail"""
    pass
