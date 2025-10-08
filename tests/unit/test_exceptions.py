"""Tests for API exceptions."""

import pytest
from src.api.exceptions import (
    KiotVietAPIError,
    AuthenticationError,
    RateLimitError,
    DataValidationError,
    ConfigurationError,
)


class TestKiotVietAPIError:
    """Test the base API exception."""

    def test_base_exception_creation(self):
        """Test creating the base exception."""
        error = KiotVietAPIError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception."""
        error = KiotVietAPIError("Test")
        assert isinstance(error, Exception)


class TestAuthenticationError:
    """Test authentication error exception."""

    def test_authentication_error_creation(self):
        """Test creating authentication error."""
        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, KiotVietAPIError)
        assert isinstance(error, Exception)

    def test_authentication_error_inheritance(self):
        """Test authentication error inheritance."""
        error = AuthenticationError("Test")
        assert isinstance(error, KiotVietAPIError)


class TestRateLimitError:
    """Test rate limit error exception."""

    def test_rate_limit_error_creation(self):
        """Test creating rate limit error."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, KiotVietAPIError)
        assert isinstance(error, Exception)

    def test_rate_limit_error_inheritance(self):
        """Test rate limit error inheritance."""
        error = RateLimitError("Test")
        assert isinstance(error, KiotVietAPIError)


class TestDataValidationError:
    """Test data validation error exception."""

    def test_data_validation_error_creation(self):
        """Test creating data validation error."""
        error = DataValidationError("Invalid data format")
        assert str(error) == "Invalid data format"
        assert isinstance(error, KiotVietAPIError)
        assert isinstance(error, Exception)

    def test_data_validation_error_inheritance(self):
        """Test data validation error inheritance."""
        error = DataValidationError("Test")
        assert isinstance(error, KiotVietAPIError)


class TestConfigurationError:
    """Test configuration error exception."""

    def test_configuration_error_creation(self):
        """Test creating configuration error."""
        error = ConfigurationError("Missing configuration")
        assert str(error) == "Missing configuration"
        assert isinstance(error, KiotVietAPIError)
        assert isinstance(error, Exception)

    def test_configuration_error_inheritance(self):
        """Test configuration error inheritance."""
        error = ConfigurationError("Test")
        assert isinstance(error, KiotVietAPIError)