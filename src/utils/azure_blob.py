# azure_blob.py
"""Azure Blob Storage utilities."""

import os
from pathlib import Path
from typing import Union, Optional

from azure.storage.blob import BlobServiceClient


def upload_to_azure_blob(file_path: Union[str, Path], blob_name: Optional[str] = None) -> str:
    """Upload a file to Azure Blob Storage.

    Args:
        file_path: Path to the local file to upload
        blob_name: Name for the blob (defaults to filename)

    Returns:
        The blob URL if successful

    Raises:
        ValueError: If required environment variables are missing
        Exception: If upload fails
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable is required")

    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "kiotviet-data")
    if not container_name:
        raise ValueError("AZURE_STORAGE_CONTAINER environment variable is required")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if blob_name is None:
        blob_name = file_path.name

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        return blob_client.url

    except Exception as e:
        raise Exception(f"Failed to upload {file_path} to Azure Blob Storage: {e}")