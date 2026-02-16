"""
Mnexium SDK Errors
"""

from typing import Optional


class MnexiumError(Exception):
    """Base exception for Mnexium SDK."""
    
    pass


class AuthenticationError(MnexiumError):
    """Authentication failed."""
    
    pass


class RateLimitError(MnexiumError):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        current: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        super().__init__(message)
        self.current = current
        self.limit = limit


class APIError(MnexiumError):
    """API error."""
    
    def __init__(self, message: str, status: int, code: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.code = code


class NotFoundError(APIError):
    """Resource not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404, "not_found")


class ValidationError(APIError):
    """Validation failed."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, 400, "validation_error")
