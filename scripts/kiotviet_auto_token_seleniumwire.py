from __future__ import annotations

"""Retrieve KiotViet access token via Selenium Wire."""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from seleniumwire import webdriver  # type: ignore
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.exceptions import ConfigurationError
from src.models.credentials import AccessCredentials
from src.services import TokenService
from src.utils.config import config

LOGIN_URL = "https://248minimart.kiotviet.vn/man/#/login"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(f"Environment variable {name} is not set")
    return value


USERNAME = _require_env("KIOTVIET_USERNAME")
PASSWORD = _require_env("KIOTVIET_PASSWORD")

TOKEN_PATH = config.get("credentials", {}).get(
    "token_file", "data/credentials/token.json"
)


def _resolve_token_path() -> Path:
    path = Path(TOKEN_PATH)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _extract_token(
    driver: webdriver.Chrome,
) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    for request in driver.requests:
        if request.response is None:
            continue
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            continue
        token = auth_header.replace("Bearer ", "", 1)
        retailer = request.headers.get("Retailer")
        branch = request.headers.get("BranchId")
        return token, retailer, branch
    return None


def login_and_extract_token() -> None:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--headless")  # Run in headless mode
    user_data_dir = f"/tmp/chrome_user_data_{os.getpid()}_{int(time.time())}"
    options.add_argument(f"--user-data-dir={user_data_dir}")

    options.binary_location = "/usr/bin/chromium-browser"
    # Try system chromedriver first, fallback to webdriver-manager
    chromedriver_path = "/usr/lib/bin/chromedriver"  # Common system path
    if not os.path.exists(chromedriver_path):
        chromedriver_path = "/usr/lib/chromium-browser/chromedriver"  # Alternative path
    if not os.path.exists(chromedriver_path):
        # Fallback to webdriver-manager for ARM
        from webdriver_manager.chrome import ChromeDriverManager
        chromedriver_path = ChromeDriverManager().install()
    
    service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    try:
        print("Opening KiotViet login page...")
        driver.get(LOGIN_URL)

        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "UserName"))
        )
        password_input = wait.until(
            EC.presence_of_element_located((By.ID, "Password"))
        )

        username_input.clear()
        username_input.send_keys(USERNAME)
        password_input.clear()
        password_input.send_keys(PASSWORD)
        print("Filled username and password.")

        login_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[text()='Quản lý']/ancestor::button")
            )
        )
        login_button.click()
        print("Submitted login form, waiting for dashboard...")

        wait.until(lambda d: "/DashBoard" in d.current_url)
        time.sleep(5)

        token_info = _extract_token(driver)
        if not token_info:
            raise RuntimeError(
                "Could not find Authorization header in network requests."
            )

        token, retailer_id, branch_id = token_info
        if not retailer_id:
            retailer_id = input("Retailer header missing. Enter retailer id: ").strip()
        if not branch_id:
            branch_id = input("Branch header missing. Enter branch id: ").strip()

        if not branch_id:
            raise ValueError("Branch id is required to store credentials.")

        try:
            branch_value = int(branch_id)
        except ValueError as exc:
            raise ValueError("Branch id must be an integer.") from exc

        credentials = AccessCredentials(
            access_token=token,
            retailer_id=str(retailer_id),
            branch_id=branch_value,
        )

        service = TokenService(_resolve_token_path())
        service.save(credentials)
        print(f"Token saved to {service.token_file}")
        print(
            f"Retailer ID: {credentials.retailer_id} | Branch ID: {credentials.branch_id}"
        )

    finally:
        input("Press Enter to close the browser...")
        driver.quit()


if __name__ == "__main__":
    login_and_extract_token()
