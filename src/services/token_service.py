"""Token storage helpers."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional, Union

from src.api.exceptions import ConfigurationError
from src.models.credentials import AccessCredentials
from src.utils.logger import logger


class TokenService:
    """Load and persist KiotViet access credentials."""

    def __init__(self, token_file: Union[str, Path]) -> None:
        self.token_file = Path(token_file)
        self._logger = logger.getChild(self.__class__.__name__)

    def token_exists(self) -> bool:
        """Return True if the token file exists."""
        return self.token_file.exists()

    def load(self) -> AccessCredentials:
        """Read credentials from disk and validate them."""
        if not self.token_file.exists():
            raise ConfigurationError(f"Token file not found: {self.token_file}")

        try:
            with self.token_file.open("r", encoding="utf-8") as handler:
                data = json.load(handler)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Invalid JSON in token file {self.token_file}: {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot read token file {self.token_file}: {exc}"
            ) from exc

        return self._parse_credentials(data)

    def save(self, credentials: AccessCredentials) -> None:
        """Persist credentials to disk."""
        payload = asdict(credentials)
        # Drop None values to keep file clean
        payload = {key: value for key, value in payload.items() if value is not None}

        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.token_file.open("w", encoding="utf-8") as handler:
                json.dump(payload, handler, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot write token file {self.token_file}: {exc}"
            ) from exc
        self._logger.info("Access token saved to %s", self.token_file)

    @staticmethod
    def build_headers(credentials: AccessCredentials) -> Dict[str, str]:
        """Create HTTP headers for KiotViet API requests."""
        return {
            "Authorization": f"Bearer {credentials.access_token}",
            "Retailer": str(credentials.retailer_id),
            "Content-Type": "application/json",
        }

    @staticmethod
    def _parse_credentials(data: Dict[str, object]) -> AccessCredentials:
        required = ["access_token", "retailer_id", "branch_id"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ConfigurationError(
                f"Token file missing required fields: {', '.join(missing)}"
            )

        access_token = data.get("access_token")
        retailer_id = data.get("retailer_id")
        branch_id = data.get("branch_id")

        if not isinstance(access_token, str) or not access_token:
            raise ConfigurationError("access_token must be a non-empty string")

        if isinstance(branch_id, str) and branch_id.isdigit():
            branch_id = int(branch_id)

        if not isinstance(branch_id, int):
            raise ConfigurationError("branch_id must be an integer")

        if branch_id <= 0:
            raise ConfigurationError("branch_id must be positive")

        expires_at: Optional[str] = None
        if "expires_at" in data:
            expires_at_value = data.get("expires_at")
            if expires_at_value is not None and not isinstance(expires_at_value, str):
                raise ConfigurationError("expires_at must be a string if provided")
            expires_at = expires_at_value  # type: ignore[assignment]

        return AccessCredentials(
            access_token=access_token,
            retailer_id=retailer_id,  # type: ignore[arg-type]
            branch_id=branch_id,
            expires_at=expires_at,
        )
