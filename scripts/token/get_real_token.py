#!/usr/bin/env python3
"""
Get Real KiotViet Token using API (from browser fetch request)
Based on actual API endpoint and headers from browser
"""

import requests
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent  # This is the integration directory, not parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Color codes
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log(msg: str, level: str = "INFO"):
    """Log with color."""
    levels = {
        "SUCCESS": (Colors.GREEN, "[OK]"),
        "ERROR": (Colors.RED, "[ERROR]"),
        "INFO": (Colors.BLUE, "[*]"),
        "WARN": (Colors.YELLOW, "[!]"),
    }
    color, prefix = levels.get(level, (Colors.BLUE, "[?]"))
    print(f"{color}{prefix}{Colors.NC} {msg}")

class KiotVietTokenFetcher:
    """Fetch real token from KiotViet API."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.api_url = "https://api-man1.kiotviet.vn/api/account/login"
        self.retailer_code = "248minimart"
        self.branch_id = 291407
        self.token = None
        
    def get_headers(self) -> Dict[str, str]:
        """Build headers for API request."""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json;charset=utf-8",
            "Retailer": self.retailer_code,
            "BranchId": str(self.branch_id),
            "LatestBranchId": str(self.branch_id),
            "X-Retailer-Code": self.retailer_code,
            "X-Group-Id": "5",
            "X-Language": "vi-VN",
            "IsUseKVClient": "1",
            "Priority": "u=1, i",
            "Sec-CH-UA": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    
    def get_payload(self) -> Dict[str, Any]:
        """Build request payload."""
        return {
            "model": {
                "RememberMe": True,
                "ShowCaptcha": False,
                "UserName": self.username,
                "Password": self.password,
                "Language": "vi-VN",
                "LatestBranchId": self.branch_id
            },
            "IsManageSide": True,
            "FingerPrintKey": "b61321168917802b9fcab91fcfeec1c2_Chrome_Desktop"
        }
    
    def login(self) -> bool:
        """Login to KiotViet and get token."""
        try:
            log(f"Logging in as {self.username}...", "INFO")
            
            headers = self.get_headers()
            payload = self.get_payload()
            
            params = {
                "quan-ly": "true"
            }
            
            log(f"Sending request to {self.api_url}", "INFO")
            
            response = self.session.post(
                self.api_url,
                json=payload,
                headers=headers,
                params=params,
                timeout=30,
                verify=True
            )
            
            log(f"Response status: {response.status_code}", "INFO")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    log(f"Response data keys: {list(data.keys())}", "INFO")
                    
                    # Check if login was successful
                    if not data.get("isSuccess"):
                        log(f"Login failed: isSuccess=False", "ERROR")
                        return False
                    
                    # Token is directly in response as "token" field
                    if "token" in data:
                        self.token = data["token"]
                        log("Token extracted from response", "SUCCESS")
                        log(f"Token preview: {self.token[:80]}...", "SUCCESS")
                        return True
                    
                    # Fallback: check other possible locations
                    if "data" in data and isinstance(data["data"], dict):
                        self.token = data["data"].get("access_token")
                        if self.token:
                            log("Token extracted from response.data", "SUCCESS")
                            return True
                    
                    # Check response headers for Set-Cookie with auth token
                    cookies = self.session.cookies.get_dict()
                    log(f"Cookies received: {list(cookies.keys())}", "INFO")
                    
                    # Token might be in Authorization header response
                    if "Authorization" in data:
                        self.token = data["Authorization"]
                        log("Token extracted from Authorization field", "SUCCESS")
                        return True
                    
                    # Print full response for debugging
                    log(f"Full response: {json.dumps(data, indent=2)[:500]}", "INFO")
                    
                    return False
                    
                except json.JSONDecodeError:
                    log(f"Invalid JSON response: {response.text[:200]}", "ERROR")
                    return False
            else:
                log(f"Login failed with status {response.status_code}", "ERROR")
                log(f"Response: {response.text[:200]}", "ERROR")
                return False
                
        except Exception as e:
            log(f"Login error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def save_token(self, filepath: Path) -> bool:
        """Save token to file."""
        if not self.token:
            log("No token to save", "ERROR")
            return False
        
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            token_data = {
                "access_token": self.token,
                "retailer_id": self.retailer_code,
                "branch_id": self.branch_id,
                "expires_at": None
            }
            
            with open(filepath, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            log(f"Token saved to {filepath}", "SUCCESS")
            return True
            
        except Exception as e:
            log(f"Failed to save token: {e}", "ERROR")
            return False

def main():
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}KiotViet Real Token Fetcher{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")
    
    # Get credentials
    username = os.getenv("KIOTVIET_USERNAME") or "0913431718"
    password = os.getenv("KIOTVIET_PASSWORD") or "68686868"
    
    log(f"Username: {username}", "INFO")
    log(f"Password: {'*' * len(password)}", "INFO")
    
    # Create fetcher
    fetcher = KiotVietTokenFetcher(username, password)
    
    # Login and get token
    if not fetcher.login():
        log("Failed to fetch token", "ERROR")
        return 1
    
    if not fetcher.token:
        log("No token received from API", "ERROR")
        return 1
    
    log(f"Token: {fetcher.token[:50]}...", "SUCCESS")
    
    # Save token
    token_file = PROJECT_ROOT / "data" / "credentials" / "token.json"
    
    print(f"\n[*] Token file path: {token_file}")
    print(f"[*] Project root: {PROJECT_ROOT}")
    
    if fetcher.save_token(token_file):
        log(f"Token saved successfully!", "SUCCESS")
        
        # Verify file was created
        if os.path.exists(token_file):
            log(f"Token file exists: {token_file}", "SUCCESS")
        else:
            log(f"Token file not found after save: {token_file}", "ERROR")
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
        print(f"{Colors.GREEN}TOKEN FETCHED SUCCESSFULLY!{Colors.NC}")
        print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
