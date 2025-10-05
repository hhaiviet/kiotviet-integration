"""Credential models"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class AccessCredentials:
    """Container for API access credentials"""
    access_token: str
    retailer_id: str
    branch_id: int
    expires_at: Optional[str] = None
