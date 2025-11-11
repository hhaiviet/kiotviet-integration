#!/usr/bin/env python3
"""
Enhanced KiotViet Auto Token Generator for Raspberry Pi
- Better error handling and retry logic
- Raspberry Pi optimized Chrome options
- Automatic credential detection from .env
"""

import json
import os
import time
from pathlib import Path
import sys
from typing import Optional, Dict, Any
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from seleniumwire import webdriver as wire_webdriver
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Run: pip install selenium selenium-wire")
    sys.exit(1)

from src.utils.logger import logger
from src.utils.config import config


class EnhancedTokenGenerator:
    """Enhanced token generator for Raspberry Pi deployment."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username or os.getenv('KIOTVIET_USERNAME')
        self.password = password or os.getenv('KIOTVIET_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Username and password required. Set KIOTVIET_USERNAME and KIOTVIET_PASSWORD environment variables.")
        
        self.login_url = "https://man1.kiotviet.vn/login"
        self.token_file = PROJECT_ROOT / "data" / "credentials" / "token.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logger.getChild(self.__class__.__name__)
        
    def get_chrome_options(self) -> Options:
        """Get optimized Chrome options for Raspberry Pi."""
        options = Options()
        
        # Raspberry Pi optimized settings
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        # Memory optimization
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        
        # Performance settings
        options.add_argument('--window-size=1024,768')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Binary location for Raspberry Pi
        chrome_binary = os.getenv('CHROME_BINARY_PATH', '/usr/bin/chromium-browser')
        if os.path.exists(chrome_binary):
            options.binary_location = chrome_binary
        
        # Chrome profile for consistency
        profile_dir = os.path.expanduser('~/chrome-profile')
        os.makedirs(profile_dir, exist_ok=True)
        options.add_argument(f'--user-data-dir={profile_dir}')
        
        return options
    
    def create_driver(self) -> webdriver.Chrome:
        """Create Chrome driver with error handling."""
        options = self.get_chrome_options()
        
        # Try different ChromeDriver paths
        driver_paths = [
            os.getenv('CHROMEDRIVER_PATH'),
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            'chromedriver'
        ]
        
        for driver_path in driver_paths:
            if not driver_path:
                continue
                
            try:
                if os.path.exists(driver_path):
                    self.logger.info(f"Using ChromeDriver at: {driver_path}")
                    return wire_webdriver.Chrome(
                        executable_path=driver_path,
                        options=options,
                        service_log_path='/tmp/chromedriver.log'
                    )
            except Exception as e:
                self.logger.warning(f"Failed to create driver with {driver_path}: {e}")
                continue
        
        # Fallback to default
        try:
            return wire_webdriver.Chrome(options=options)
        except Exception as e:
            self.logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    def wait_for_network_idle(self, driver: webdriver.Chrome, timeout: int = 30) -> None:
        """Wait for network activity to settle."""
        start_time = time.time()
        last_request_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for new requests
            current_requests = len(driver.requests)
            if current_requests > 0:
                last_request_time = time.time()
            
            # If no new requests for 3 seconds, consider idle
            if time.time() - last_request_time > 3:
                break
                
            time.sleep(0.5)
    
    def extract_token_from_requests(self, driver: webdriver.Chrome) -> Optional[Dict[str, Any]]:
        """Extract token and IDs from network requests."""
        self.logger.info("Analyzing network requests for token...")
        
        token_data = {}
        
        for request in driver.requests:
            try:
                # Look for API calls with Authorization headers
                if hasattr(request, 'headers') and 'authorization' in str(request.headers).lower():
                    auth_header = request.headers.get('Authorization', '')
                    if auth_header.startswith('Bearer '):
                        token_data['access_token'] = auth_header.replace('Bearer ', '')
                        self.logger.info("✅ Found access token in request headers")
                
                # Look for responses containing retailer/branch info
                if hasattr(request, 'response') and request.response:
                    try:
                        content_type = request.response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            response_text = request.response.body.decode('utf-8')
                            response_data = json.loads(response_text)
                            
                            # Extract retailer and branch IDs from various API responses
                            if isinstance(response_data, dict):
                                if 'retailer' in response_data:
                                    if isinstance(response_data['retailer'], dict):
                                        token_data['retailer_id'] = response_data['retailer'].get('id')
                                    else:
                                        token_data['retailer_id'] = response_data['retailer']
                                
                                if 'branch' in response_data:
                                    if isinstance(response_data['branch'], dict):
                                        token_data['branch_id'] = response_data['branch'].get('id')
                                    else:
                                        token_data['branch_id'] = response_data['branch']
                                
                                # Look in data arrays
                                if 'data' in response_data and isinstance(response_data['data'], list):
                                    for item in response_data['data']:
                                        if isinstance(item, dict):
                                            if 'retailerId' in item:
                                                token_data['retailer_id'] = item['retailerId']
                                            if 'branchId' in item:
                                                token_data['branch_id'] = item['branchId']
                    except:
                        continue
            except Exception as e:
                continue
        
        return token_data if token_data else None
    
    def login_and_extract_token(self, max_retries: int = 3) -> Dict[str, Any]:
        """Login and extract token with retry logic."""
        for attempt in range(max_retries):
            driver = None
            try:
                self.logger.info(f"🔑 Login attempt {attempt + 1}/{max_retries}")
                
                # Create driver
                driver = self.create_driver()
                self.logger.info("✅ Chrome driver created successfully")
                
                # Navigate to login page
                self.logger.info("📱 Navigating to KiotViet login page...")
                driver.get(self.login_url)
                
                # Wait for page to load
                wait = WebDriverWait(driver, 20)
                
                # Find and fill username
                self.logger.info("👤 Entering username...")
                username_field = wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(self.username)
                
                # Find and fill password
                self.logger.info("🔒 Entering password...")
                password_field = driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(self.password)
                
                # Submit login form
                self.logger.info("🚀 Submitting login form...")
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                login_button.click()
                
                # Wait for login to complete and redirect
                self.logger.info("⏳ Waiting for login to complete...")
                time.sleep(5)
                
                # Check if login was successful (look for dashboard or redirect)
                current_url = driver.current_url
                if "login" not in current_url.lower():
                    self.logger.info("✅ Login successful, extracting token...")
                    
                    # Wait for additional requests
                    self.wait_for_network_idle(driver, timeout=30)
                    
                    # Extract token data
                    token_data = self.extract_token_from_requests(driver)
                    
                    if token_data and token_data.get('access_token'):
                        self.logger.info("✅ Token extraction successful!")
                        return token_data
                    else:
                        self.logger.warning("⚠️ Token not found in requests, retrying...")
                else:
                    self.logger.warning("❌ Login failed - still on login page")
                
            except Exception as e:
                self.logger.error(f"❌ Login attempt {attempt + 1} failed: {e}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
            
            if attempt < max_retries - 1:
                sleep_time = (attempt + 1) * 10
                self.logger.info(f"⏳ Waiting {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
        
        raise Exception("Failed to extract token after all retry attempts")
    
    def save_token(self, token_data: Dict[str, Any]) -> None:
        """Save token data to file."""
        # Add environment variables if not in token data
        if 'retailer_id' not in token_data and os.getenv('KIOTVIET_RETAILER_ID'):
            token_data['retailer_id'] = os.getenv('KIOTVIET_RETAILER_ID')
        
        if 'branch_id' not in token_data and os.getenv('KIOTVIET_BRANCH_ID'):
            token_data['branch_id'] = os.getenv('KIOTVIET_BRANCH_ID')
        
        # Add timestamp
        token_data['generated_at'] = time.time()
        token_data['generated_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        self.logger.info(f"💾 Token saved to {self.token_file}")
        
        # Log what we have
        for key, value in token_data.items():
            if key != 'access_token':
                self.logger.info(f"  {key}: {value}")
            else:
                self.logger.info(f"  {key}: {'*' * 20}...{str(value)[-10:] if value else 'None'}")
    
    def generate_token(self) -> None:
        """Main method to generate and save token."""
        try:
            self.logger.info("🚀 Starting KiotViet token generation...")
            token_data = self.login_and_extract_token()
            self.save_token(token_data)
            self.logger.info("✅ Token generation completed successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Token generation failed: {e}")
            raise


def main():
    """Main entry point."""
    # Setup environment
    os.environ.setdefault('DISPLAY', ':99')
    
    # Load environment variables from .env file
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    
    try:
        generator = EnhancedTokenGenerator()
        generator.generate_token()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()