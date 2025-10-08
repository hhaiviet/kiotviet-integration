# base_service.py
"""Base service class with common functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.api.client import KiotVietClient
from src.services.token_service import TokenService
from src.utils.config import config
from src.utils.logger import logger


class BaseService:
    """Base class for KiotViet services with common initialization and utilities."""

    def __init__(
        self,
        client: Optional[KiotVietClient] = None,
        token_service: Optional[TokenService] = None,
    ) -> None:
        # Load configuration sections
        api_cfg = config.get("api", {})
        data_cfg = config.get("data", {})
        credentials_cfg = config.get("credentials", {})

        # Common API client configuration
        base_url = api_cfg.get("base_url", "https://api-man1.kiotviet.vn/api")
        timeout = int(api_cfg.get("timeout", 30))
        max_retries = int(api_cfg.get("max_retries", 3))

        # Initialize API client
        self.client = client or KiotVietClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=0.5,  # Default retry delay
        )

        # Initialize token service
        token_path = credentials_cfg.get("token_file", "data/credentials/token.json")
        self.token_service = token_service or TokenService(token_path)

        # Common directories
        self.output_dir = Path(data_cfg.get("output_dir", "data/output"))
        self.checkpoint_dir = Path(data_cfg.get("checkpoint_dir", "data/checkpoints"))

        # Logger
        self._logger = logger.getChild(self.__class__.__name__)

    def get_credentials_and_headers(self):
        """Load credentials and build headers for API requests."""
        credentials = self.token_service.load()
        headers = TokenService.build_headers(credentials)
        return credentials, headers

    def ensure_output_dir(self, path: Path) -> Path:
        """Ensure the output directory exists and return the full path."""
        if not path.is_absolute():
            path = self.output_dir / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def ensure_checkpoint_dir(self, path: Path) -> Path:
        """Ensure the checkpoint directory exists and return the full path."""
        if not path.is_absolute():
            path = self.checkpoint_dir / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path