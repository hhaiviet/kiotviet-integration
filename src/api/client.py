"""HTTP client utilities for KiotViet API."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import requests

from src.api.exceptions import (
    AuthenticationError,
    KiotVietAPIError,
    RateLimitError,
)
from src.utils.logger import logger


class KiotVietClient:
    """Simple HTTP client that wraps KiotViet API calls with retry logic."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = session or requests.Session()
        self._logger = logger.getChild(self.__class__.__name__)

    def get(
        self,
        endpoint: str,
        *,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform a GET request and return the JSON payload."""
        return self._request(
            "GET",
            endpoint,
            headers=headers,
            params=params,
            timeout=timeout,
        )

    def post(
        self,
        endpoint: str,
        *,
        headers: Dict[str, str],
        json_payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform a POST request and return the JSON payload."""
        return self._request(
            "POST",
            endpoint,
            headers=headers,
            params=params,
            json_payload=json_payload,
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        timeout_value = timeout or self.timeout
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_payload,
                    timeout=timeout_value,
                )
            except requests.Timeout as exc:
                last_error = exc
                self._logger.warning(
                    "Request timeout (%s %s), attempt %s/%s",
                    method,
                    endpoint,
                    attempt + 1,
                    self.max_retries + 1,
                )
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise KiotVietAPIError(
                    f"Request timeout after {timeout_value}s"
                ) from exc
            except requests.RequestException as exc:
                last_error = exc
                self._logger.warning(
                    "Request error (%s %s): %s",
                    method,
                    endpoint,
                    exc,
                )
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise KiotVietAPIError("Request failed") from exc

            if response.status_code == 401:
                raise AuthenticationError("Authentication failed with status 401")

            if response.status_code == 429:
                self._logger.warning("Rate limit hit for %s %s", method, endpoint)
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise RateLimitError("Rate limit exceeded")

            if 500 <= response.status_code < 600:
                last_error = KiotVietAPIError(
                    f"Server error {response.status_code}: {response.text}"
                )
                self._logger.warning(
                    "Server error %s on %s %s",
                    response.status_code,
                    method,
                    endpoint,
                )
                if attempt < self.max_retries:
                    self._sleep(attempt)
                    continue
                raise last_error

            if not response.ok:
                raise KiotVietAPIError(
                    f"API request failed: {response.status_code} {response.text}"
                )

            if not response.content:
                return {}

            try:
                return response.json()
            except json.JSONDecodeError as exc:
                raise KiotVietAPIError("Invalid JSON response") from exc

        raise KiotVietAPIError(
            f"API request failed after {self.max_retries + 1} attempts"
        ) from last_error

    def _sleep(self, attempt: int) -> None:
        delay = self.retry_delay * (2 ** attempt)
        time.sleep(delay)

    def _build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self.base_url}{endpoint}"
