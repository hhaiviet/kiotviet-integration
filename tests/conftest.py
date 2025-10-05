"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path

@pytest.fixture
def sample_token():
    """Sample token data"""
    return {
        "access_token": "test_token_123",
        "retailer_id": "test_retailer",
        "branch_id": 1
    }

@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
