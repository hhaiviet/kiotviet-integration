"""Custom exceptions for API operations."""


class KiotVietAPIError(Exception):
    """Base exception for KiotViet API errors."""


class AuthenticationError(KiotVietAPIError):
    """Raised when authentication fails."""


class RateLimitError(KiotVietAPIError):
    """Raised when API rate limit is exceeded."""


class DataValidationError(KiotVietAPIError):
    """Raised when data validation fails."""


class ConfigurationError(KiotVietAPIError):
    """Raised when configuration or credential files are invalid."""
