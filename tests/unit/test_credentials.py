"""Tests for credentials model."""

import pytest
from src.models.credentials import AccessCredentials


class TestAccessCredentials:
    """Test the AccessCredentials dataclass."""

    def test_access_credentials_creation(self):
        """Test creating AccessCredentials with required fields."""
        creds = AccessCredentials(
            access_token="test_token",
            retailer_id="test_retailer",
            branch_id=123
        )

        assert creds.access_token == "test_token"
        assert creds.retailer_id == "test_retailer"
        assert creds.branch_id == 123
        assert creds.expires_at is None

    def test_access_credentials_with_expires_at(self):
        """Test creating AccessCredentials with expires_at."""
        creds = AccessCredentials(
            access_token="test_token",
            retailer_id="test_retailer",
            branch_id=123,
            expires_at="2024-01-01T00:00:00Z"
        )

        assert creds.access_token == "test_token"
        assert creds.retailer_id == "test_retailer"
        assert creds.branch_id == 123
        assert creds.expires_at == "2024-01-01T00:00:00Z"

    def test_access_credentials_equality(self):
        """Test equality of AccessCredentials objects."""
        creds1 = AccessCredentials(
            access_token="token1",
            retailer_id="retailer1",
            branch_id=1
        )

        creds2 = AccessCredentials(
            access_token="token1",
            retailer_id="retailer1",
            branch_id=1
        )

        creds3 = AccessCredentials(
            access_token="token2",
            retailer_id="retailer1",
            branch_id=1
        )

        assert creds1 == creds2
        assert creds1 != creds3

    def test_access_credentials_repr(self):
        """Test string representation of AccessCredentials."""
        creds = AccessCredentials(
            access_token="test_token",
            retailer_id="test_retailer",
            branch_id=123
        )

        repr_str = repr(creds)
        assert "AccessCredentials" in repr_str
        assert "test_token" in repr_str
        assert "test_retailer" in repr_str
        assert "123" in repr_str

    def test_access_credentials_immutable(self):
        """Test that AccessCredentials fields can be modified (dataclass default)."""
        creds = AccessCredentials(
            access_token="test_token",
            retailer_id="test_retailer",
            branch_id=123
        )

        # Test that we can modify fields (dataclass default behavior)
        creds.access_token = "new_token"
        creds.retailer_id = "new_retailer"
        creds.branch_id = 456
        creds.expires_at = "2024-01-01"

        assert creds.access_token == "new_token"
        assert creds.retailer_id == "new_retailer"
        assert creds.branch_id == 456
        assert creds.expires_at == "2024-01-01"