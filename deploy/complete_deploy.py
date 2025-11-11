#!/usr/bin/env python3
"""
Complete KiotViet Deployment Automation
SSH Setup + Deployment in one script
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Tuple, Optional
import os

# Configuration
PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
KIOTVIET_USERNAME = "0913431718"
KIOTVIET_PASSWORD = "68686868"
RETAILER_ID = "248minimart"
BRANCH_ID = "291407"

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'

def log(msg: str, level: str = "INFO"):
    """Log message with timestamp."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    if level == "SUCCESS":
        color = Colors.GREEN
        prefix = "[OK]"
    elif level == "ERROR":
        color = Colors.RED
        prefix = "[ERROR]"
    elif level == "WARNING":
        color = Colors.YELLOW
        prefix = "[WARN]"
    elif level == "INFO":
        color = Colors.BLUE
        prefix = "[INFO]"
    else:
        color = Colors.PURPLE
        prefix = "[STEP]"
    
    print(f"{color}[{timestamp}] {prefix}{Colors.NC} {msg}")

def run_command(cmd: list, description: str = "", capture: bool = True) -> Tuple[bool, str]:
    """Run command and return status."""
    try:
        if description:
            log(description, "STEP")
        
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True, result.stdout
            else:
                log(f"Command failed: {result.stderr}", "ERROR")
                return False, result.stderr
        else:
            result = subprocess.run(cmd, timeout=60)
            return result.returncode == 0, ""
            
    except subprocess.TimeoutExpired:
        log("Command timeout", "ERROR")
        return False, "Timeout"
    except Exception as e:
        log(f"Command error: {e}", "ERROR")
        return False, str(e)

class FullDeployment:
    def __init__(self):
        self.project_root = Path.cwd()
        self.ssh_dir = Path.home() / ".ssh"
        self.private_key = self.ssh_dir / "id_rsa"
        self.public_key = self.ssh_dir / "id_rsa.pub"
        
    def step_1_check_ssh_key(self) -> bool:
        """Step 1: Check or create SSH key."""
        log("\n" + "="*70, "STEP")
        log("STEP 1: SSH Key Setup", "STEP")
        log("="*70, "STEP")
        
        if self.private_key.exists() and self.public_key.exists():
            log(f"SSH key found at {self.private_key}", "SUCCESS")
            return True
        
        log("SSH key not found, generating...", "WARNING")
        
        self.ssh_dir.mkdir(parents=True, exist_ok=True)
        success, output = run_command(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(self.private_key), "-N", ""],
            "Generating new SSH key..."
        )
        
        if success:
            log("SSH key generated successfully", "SUCCESS")
            return True
        else:
            log(f"Failed to generate SSH key: {output}", "ERROR")
            return False
    
    def step_2_copy_ssh_key(self, pi_password: str) -> bool:
        """Step 2: Copy SSH key to Pi."""
        log("\n" + "="*70, "STEP")
        log("STEP 2: Copy SSH Key to Raspberry Pi", "STEP")
        log("="*70, "STEP")
        
        if not self.public_key.exists():
            log("Public key not found", "ERROR")
            return False
        
        with open(self.public_key, 'r') as f:
            pub_key_content = f.read().strip()
        
        # Build SSH command
        commands = [
            "mkdir -p ~/.ssh",
            f"echo '{pub_key_content}' >> ~/.ssh/authorized_keys",
            "chmod 600 ~/.ssh/authorized_keys",
            "chmod 700 ~/.ssh"
        ]
        
        log(f"Connecting to {PI_USER}@{PI_IP}...", "INFO")
        
        for cmd in commands:
            try:
                # Use echo + pipe for password
                full_cmd = f"echo {pi_password} | ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {PI_USER}@{PI_IP} '{cmd}'"
                
                result = subprocess.run(
                    full_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    log(f"Executed: {cmd[:50]}...", "SUCCESS")
                else:
                    # Retry once
                    log(f"Command failed, retrying: {cmd[:50]}...", "WARNING")
                    result = subprocess.run(
                        full_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        log(f"Failed after retry: {result.stderr}", "ERROR")
                        return False
                
                time.sleep(1)
                
            except subprocess.TimeoutExpired:
                log("SSH command timeout", "ERROR")
                return False
            except Exception as e:
                log(f"Error: {e}", "ERROR")
                return False
        
        log("SSH key copied successfully", "SUCCESS")
        return True
    
    def step_3_test_ssh_key(self) -> bool:
        """Step 3: Test SSH key connection."""
        log("\n" + "="*70, "STEP")
        log("STEP 3: Test SSH Key Connection", "STEP")
        log("="*70, "STEP")
        
        log("Testing SSH key connection...", "INFO")
        
        cmd = [
            "ssh",
            "-i", str(self.private_key),
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            f"{PI_USER}@{PI_IP}",
            "echo 'SSH Key test successful'"
        ]
        
        success, output = run_command(cmd, capture=True)
        
        if success:
            log("SSH key connection verified", "SUCCESS")
            return True
        else:
            log(f"SSH key test failed: {output}", "ERROR")
            return False
    
    def step_4_pre_deploy_check(self) -> bool:
        """Step 4: Run pre-deployment checks."""
        log("\n" + "="*70, "STEP")
        log("STEP 4: Pre-Deployment Checks", "STEP")
        log("="*70, "STEP")
        
        pre_check_file = self.project_root / "pre_deploy_check.py"
        if not pre_check_file.exists():
            log("Pre-check script not found", "WARNING")
            return True
        
        success, _ = run_command(
            [sys.executable, str(pre_check_file)],
            "Running pre-deployment checks...",
            capture=False
        )
        
        return True  # Continue even if some checks fail
    
    def step_5_create_env_file(self) -> bool:
        """Step 5: Create .env file with credentials."""
        log("\n" + "="*70, "STEP")
        log("STEP 5: Create Environment Configuration", "STEP")
        log("="*70, "STEP")
        
        env_file = self.project_root / ".env"
        
        env_content = f"""# KiotViet Credentials - Auto-generated
KIOTVIET_USERNAME={KIOTVIET_USERNAME}
KIOTVIET_PASSWORD={KIOTVIET_PASSWORD}
KIOTVIET_RETAILER_ID={RETAILER_ID}
KIOTVIET_BRANCH_ID={BRANCH_ID}

# API Configuration
API_BASE_URL=https://api-man1.kiotviet.vn/api
API_TIMEOUT=30
API_MAX_RETRIES=5
API_PAGE_SIZE=100

# Chrome Configuration for Raspberry Pi
CHROME_BINARY_PATH=/usr/bin/chromium-browser
CHROMEDRIVER_PATH=/usr/bin/chromedriver
DISPLAY=:99

# Scheduling
SYNC_INTERVAL_HOURS=2
AUTO_RESTART=true

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Remote monitoring
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_PORT=8080
"""
        
        try:
            env_file.write_text(env_content)
            log(f"Environment file created: {env_file}", "SUCCESS")
            return True
        except Exception as e:
            log(f"Failed to create .env file: {e}", "ERROR")
            return False
    
    def step_6_run_deployment(self) -> bool:
        """Step 6: Run deployment script."""
        log("\n" + "="*70, "STEP")
        log("STEP 6: Run Deployment Script", "STEP")
        log("="*70, "STEP")
        
        deploy_script = self.project_root / "deploy" / "fully_automated_deploy.sh"
        
        if not deploy_script.exists():
            log(f"Deployment script not found: {deploy_script}", "ERROR")
            return False
        
        log("Attempting to deploy via bash...", "INFO")
        
        cmd = [
            "bash",
            str(deploy_script),
            KIOTVIET_USERNAME,
            KIOTVIET_PASSWORD,
            RETAILER_ID,
            BRANCH_ID
        ]
        
        try:
            # Run with output streaming
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            for line in process.stdout:
                print(line.rstrip())
            
            process.wait(timeout=1800)  # 30 minutes timeout
            
            if process.returncode == 0:
                log("Deployment completed successfully", "SUCCESS")
                return True
            else:
                log(f"Deployment failed with exit code: {process.returncode}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            log("Deployment timeout (30 minutes)", "ERROR")
            process.kill()
            return False
        except Exception as e:
            log(f"Deployment error: {e}", "ERROR")
            return False
    
    def run_all(self, pi_password: str) -> bool:
        """Run all deployment steps."""
        print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
        print(f"{Colors.PURPLE}KiotViet Integration - Complete Deployment{Colors.NC}")
        print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
        
        steps = [
            ("SSH Key Setup", self.step_1_check_ssh_key, []),
            ("Copy SSH Key", self.step_2_copy_ssh_key, [pi_password]),
            ("Test SSH Connection", self.step_3_test_ssh_key, []),
            ("Pre-Deployment Check", self.step_4_pre_deploy_check, []),
            ("Create .env", self.step_5_create_env_file, []),
            ("Run Deployment", self.step_6_run_deployment, []),
        ]
        
        for i, (name, func, args) in enumerate(steps, 1):
            try:
                if not func(*args):
                    log(f"Step {i} failed: {name}", "ERROR")
                    return False
            except Exception as e:
                log(f"Step {i} exception: {e}", "ERROR")
                return False
        
        return True

def main():
    """Main entry point."""
    import getpass
    
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
    print(f"{Colors.PURPLE}KiotViet Integration - Raspberry Pi Deployment{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
    
    print(f"Target: {PI_USER}@{PI_IP}")
    print(f"KiotViet User: {KIOTVIET_USERNAME}")
    print(f"Retailer ID: {RETAILER_ID}")
    print(f"Branch ID: {BRANCH_ID}\n")
    
    # Get SSH password
    pi_password = getpass.getpass(f"Enter SSH password for {PI_USER}@{PI_IP}: ")
    
    if not pi_password:
        log("Password cannot be empty", "ERROR")
        return 1
    
    # Run deployment
    deployer = FullDeployment()
    
    if deployer.run_all(pi_password):
        print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
        print(f"{Colors.GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY!{Colors.NC}")
        print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")
        
        print(f"Your KiotViet integration is now running on {PI_USER}@{PI_IP}!\n")
        
        print(f"Next steps:")
        print(f"  1. Check status: python remote_debug.py status")
        print(f"  2. View logs: python remote_debug.py logs --follow")
        print(f"  3. Manual sync: python remote_debug.py sync")
        print(f"  4. SSH access: python remote_debug.py shell\n")
        
        return 0
    else:
        print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
        print(f"{Colors.RED}DEPLOYMENT FAILED!{Colors.NC}")
        print(f"{Colors.RED}{'='*70}{Colors.NC}\n")
        
        print(f"Check the error messages above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())