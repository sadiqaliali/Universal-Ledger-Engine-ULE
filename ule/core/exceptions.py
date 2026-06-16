"""Custom exceptions for ULE."""


class ULEError(Exception):
    """Base exception for ULE."""
    pass


class DatabaseError(ULEError):
    """Database operation error."""
    pass


class AuthenticationError(ULEError):
    """Authentication/authorization error."""
    pass


class SecurityError(ULEError):
    """Security-related error."""
    pass


class QueryError(ULEError):
    """Query execution error."""
    pass


class ValidationError(ULEError):
    """Data validation error."""
    pass
