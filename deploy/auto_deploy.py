#!/usr/bin/env python3
"""
Complete Automated KiotViet Deployment - No User Input Required
"""

import subprocess
import sys
import time
from pathlib import Path
import os

# Configuration - All credentials embedded
PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
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
    """Log message."""
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

def ssh_command(cmd: str, description: str = "") -> bool:
    """Execute SSH command with password."""
    if description:
        log(description, "STEP")
    
    try:
        # Use echo to pass password to SSH
        full_cmd = f"echo {PI_PASSWORD} | ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o PubkeyAuthentication=no {PI_USER}@{PI_IP} '{cmd}'"
        
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            log(f"Success: {cmd[:50]}", "SUCCESS")
            return True
        else:
            log(f"Failed: {result.stderr[:100]}", "ERROR")
            return False
            
    except Exception as e:
        log(f"SSH Error: {e}", "ERROR")
        return False

def step_1_setup_ssh_key() -> bool:
    """Step 1: Generate SSH key if needed."""
    log("\n" + "="*70, "STEP")
    log("STEP 1: SSH Key Setup", "STEP")
    log("="*70, "STEP")
    
    ssh_dir = Path.home() / ".ssh"
    private_key = ssh_dir / "id_rsa"
    
    if private_key.exists():
        log(f"SSH key found at {private_key}", "SUCCESS")
        return True
    
    log("Generating SSH key...", "INFO")
    ssh_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(private_key), "-N", ""],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            log("SSH key generated successfully", "SUCCESS")
            return True
        else:
            log(f"Failed to generate SSH key: {result.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Error generating SSH key: {e}", "ERROR")
        return False

def step_2_copy_ssh_key() -> bool:
    """Step 2: Copy SSH public key to Pi."""
    log("\n" + "="*70, "STEP")
    log("STEP 2: Copy SSH Key to Raspberry Pi", "STEP")
    log("="*70, "STEP")
    
    ssh_dir = Path.home() / ".ssh"
    public_key_file = ssh_dir / "id_rsa.pub"
    
    if not public_key_file.exists():
        log("Public key not found", "ERROR")
        return False
    
    with open(public_key_file, 'r') as f:
        pub_key = f.read().strip()
    
    commands = [
        "mkdir -p ~/.ssh",
        f"echo '{pub_key}' >> ~/.ssh/authorized_keys",
        "chmod 600 ~/.ssh/authorized_keys",
        "chmod 700 ~/.ssh"
    ]
    
    log(f"Connecting to {PI_USER}@{PI_IP}...", "INFO")
    
    for cmd in commands:
        if not ssh_command(cmd, f"Executing: {cmd[:50]}..."):
            log(f"Failed to copy SSH key", "ERROR")
            return False
        time.sleep(1)
    
    log("SSH key copied successfully", "SUCCESS")
    return True

def step_3_test_ssh() -> bool:
    """Step 3: Test SSH connection with key."""
    log("\n" + "="*70, "STEP")
    log("STEP 3: Test SSH Key Connection", "STEP")
    log("="*70, "STEP")
    
    log("Testing SSH key connection...", "INFO")
    
    ssh_dir = Path.home() / ".ssh"
    private_key = ssh_dir / "id_rsa"
    
    try:
        cmd = [
            "ssh",
            "-i", str(private_key),
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            f"{PI_USER}@{PI_IP}",
            "echo 'SSH key test successful'"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            log("SSH key connection verified", "SUCCESS")
            return True
        else:
            log(f"SSH key test failed", "ERROR")
            return False
            
    except Exception as e:
        log(f"SSH test error: {e}", "ERROR")
        return False

def step_4_create_env() -> bool:
    """Step 4: Create .env file."""
    log("\n" + "="*70, "STEP")
    log("STEP 4: Create Environment Configuration", "STEP")
    log("="*70, "STEP")
    
    project_root = Path.cwd()
    env_file = project_root / ".env"
    
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

def step_5_run_deployment() -> bool:
    """Step 5: Run deployment script."""
    log("\n" + "="*70, "STEP")
    log("STEP 5: Run Deployment Script", "STEP")
    log("="*70, "STEP")
    
    project_root = Path.cwd()
    deploy_script = project_root / "deploy" / "fully_automated_deploy.sh"
    
    if not deploy_script.exists():
        log(f"Deployment script not found: {deploy_script}", "ERROR")
        return False
    
    log("Starting deployment via bash...", "INFO")
    log(f"Target: {PI_USER}@{PI_IP}", "INFO")
    log(f"KiotViet User: {KIOTVIET_USERNAME}", "INFO")
    
    cmd = [
        "bash",
        str(deploy_script),
        KIOTVIET_USERNAME,
        KIOTVIET_PASSWORD,
        RETAILER_ID,
        BRANCH_ID
    ]
    
    try:
        # Stream output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Print output line by line
        for line in process.stdout:
            print(line.rstrip())
        
        process.wait(timeout=1800)  # 30 minutes
        
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

def main():
    """Main entry point."""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
    print(f"{Colors.PURPLE}KiotViet Integration - Automated Deployment{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
    
    print(f"Target: {PI_USER}@{PI_IP}")
    print(f"KiotViet User: {KIOTVIET_USERNAME}")
    print(f"Retailer ID: {RETAILER_ID}")
    print(f"Branch ID: {BRANCH_ID}\n")
    
    steps = [
        ("SSH Key Setup", step_1_setup_ssh_key),
        ("Copy SSH Key", step_2_copy_ssh_key),
        ("Test SSH Connection", step_3_test_ssh),
        ("Create Environment", step_4_create_env),
        ("Run Deployment", step_5_run_deployment),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        try:
            if not func():
                log(f"Step {i} failed: {name}", "ERROR")
                print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
                print(f"{Colors.RED}DEPLOYMENT FAILED AT STEP {i}!{Colors.NC}")
                print(f"{Colors.RED}{'='*70}{Colors.NC}\n")
                return 1
        except Exception as e:
            log(f"Step {i} exception: {e}", "ERROR")
            return 1
        
        time.sleep(2)
    
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

if __name__ == "__main__":
    sys.exit(main())