"""Tests for Azure blob storage utilities."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

from src.utils.azure_blob import upload_to_azure_blob


class TestUploadToAzureBlob:
    """Test the upload_to_azure_blob function."""

    def test_upload_successful(self):
        """Test successful file upload to Azure Blob Storage."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
                'AZURE_STORAGE_CONTAINER': 'test_container'
            }):
                with patch('src.utils.azure_blob.BlobServiceClient') as mock_blob_service_class:
                    mock_blob_client = MagicMock()
                    mock_blob_service_instance = MagicMock()
                    mock_blob_service_class.from_connection_string.return_value = mock_blob_service_instance
                    mock_blob_service_instance.get_blob_client.return_value = mock_blob_client
                    mock_blob_client.url = "https://test.blob.core.windows.net/test/test_file.txt"

                    # Call function
                    result = upload_to_azure_blob(temp_file_path, "test_file.txt")

                    # Assertions
                    assert result == "https://test.blob.core.windows.net/test/test_file.txt"
                    mock_blob_service_class.from_connection_string.assert_called_once_with('test_connection_string')
                    mock_blob_client.upload_blob.assert_called_once()

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_upload_with_default_blob_name(self):
        """Test upload with default blob name (filename)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_file.write("col1,col2\nval1,val2")
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
                'AZURE_STORAGE_CONTAINER': 'test_container'
            }):
                with patch('src.utils.azure_blob.BlobServiceClient') as mock_blob_service_class:
                    mock_blob_client = MagicMock()
                    mock_blob_service_instance = MagicMock()
                    mock_blob_service_class.from_connection_string.return_value = mock_blob_service_instance
                    mock_blob_service_instance.get_blob_client.return_value = mock_blob_client
                    mock_blob_client.url = "https://test.blob.core.windows.net/test/test.csv"

                    # Call function without blob_name
                    result = upload_to_azure_blob(temp_file_path)

                    # Should use filename as blob name
                    expected_blob_name = Path(temp_file_path).name
                    mock_blob_service_instance.get_blob_client.assert_called_once_with(
                        container='test_container',
                        blob=expected_blob_name
                    )

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_upload_missing_connection_string(self):
        """Test upload fails when connection string is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                upload_to_azure_blob("/fake/path.txt")

            assert "AZURE_STORAGE_CONNECTION_STRING environment variable is required" in str(exc_info.value)

    def test_upload_missing_container_name(self):
        """Test upload fails when container name is empty."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
                'AZURE_STORAGE_CONTAINER': ''  # Empty container name
            }):
                with pytest.raises(ValueError) as exc_info:
                    upload_to_azure_blob(temp_file_path)

                assert "AZURE_STORAGE_CONTAINER environment variable is required" in str(exc_info.value)

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_upload_file_not_found(self):
        """Test upload fails when file doesn't exist."""
        with patch.dict(os.environ, {
            'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
            'AZURE_STORAGE_CONTAINER': 'test_container'
        }):
            with pytest.raises(FileNotFoundError) as exc_info:
                upload_to_azure_blob("/nonexistent/file.txt")

            assert "File not found: /nonexistent/file.txt" in str(exc_info.value)

    def test_upload_azure_error(self):
        """Test upload fails when Azure operation fails."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
                'AZURE_STORAGE_CONTAINER': 'test_container'
            }):
                with patch('src.utils.azure_blob.BlobServiceClient') as mock_blob_service_class:
                    mock_blob_client = MagicMock()
                    mock_blob_service_instance = MagicMock()
                    mock_blob_service_class.from_connection_string.return_value = mock_blob_service_instance
                    mock_blob_service_instance.get_blob_client.return_value = mock_blob_client
                    mock_blob_client.upload_blob.side_effect = Exception("Azure error")

                    with pytest.raises(Exception) as exc_info:
                        upload_to_azure_blob(temp_file_path)

                    assert "Failed to upload" in str(exc_info.value)
                    assert "Azure error" in str(exc_info.value)

        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_upload_with_pathlib_path(self):
        """Test upload works with pathlib.Path objects."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = Path(temp_file.name)

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string',
                'AZURE_STORAGE_CONTAINER': 'test_container'
            }):
                with patch('src.utils.azure_blob.BlobServiceClient') as mock_blob_service_class:
                    mock_blob_client = MagicMock()
                    mock_blob_service_instance = MagicMock()
                    mock_blob_service_class.from_connection_string.return_value = mock_blob_service_instance
                    mock_blob_service_instance.get_blob_client.return_value = mock_blob_client
                    mock_blob_client.url = "https://test.blob.core.windows.net/test/test_file.txt"

                    # Call function with Path object
                    result = upload_to_azure_blob(temp_file_path, "test_file.txt")

                    assert result == "https://test.blob.core.windows.net/test/test_file.txt"

        finally:
            temp_file_path.unlink(missing_ok=True)

    def test_upload_default_container_name(self):
        """Test upload uses default container name when not specified."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        try:
            with patch.dict(os.environ, {
                'AZURE_STORAGE_CONNECTION_STRING': 'test_connection_string'
                # AZURE_STORAGE_CONTAINER not set
            }):
                with patch('src.utils.azure_blob.BlobServiceClient') as mock_blob_service_class:
                    mock_blob_client = MagicMock()
                    mock_blob_service_instance = MagicMock()
                    mock_blob_service_class.from_connection_string.return_value = mock_blob_service_instance
                    mock_blob_service_instance.get_blob_client.return_value = mock_blob_client

                    # This should work with default container name
                    upload_to_azure_blob(temp_file_path)

                    # Should use default container name
                    mock_blob_service_instance.get_blob_client.assert_called_once_with(
                        container='kiotviet-data',
                        blob=Path(temp_file_path).name
                    )

        finally:
            Path(temp_file_path).unlink(missing_ok=True)