#!/usr/bin/env python3
"""
Clone KiotViet Project to Raspberry Pi and Setup Environment
Then user can SSH in to debug and fix issues
"""

import subprocess
import sys
from pathlib import Path
import time

# Configuration
PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PROJECT_URL = "https://github.com/hhaiviet/kiotviet-integration.git"
PROJECT_NAME = "kiotviet-integration"
PI_PROJECT_DIR = f"/home/{PI_USER}/{PROJECT_NAME}"

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log(msg: str, level: str = "INFO"):
    """Log with color."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    
    levels = {
        "SUCCESS": (Colors.GREEN, "[OK]"),
        "ERROR": (Colors.RED, "[ERROR]"),
        "WARNING": (Colors.YELLOW, "[WARN]"),
        "INFO": (Colors.BLUE, "[INFO]"),
        "STEP": (Colors.PURPLE, "[>>>]"),
    }
    
    color, prefix = levels.get(level, (Colors.BLUE, "[?]"))
    print(f"{color}[{ts}] {prefix}{Colors.NC} {msg}")

def ssh_exec(cmd: str) -> bool:
    """Execute SSH command with password."""
    try:
        # Use sshpass if available, otherwise try echo method
        full_cmd = f"sshpass -p {PI_PASSWORD} ssh -o StrictHostKeyChecking=no {PI_USER}@{PI_IP} '{cmd}'"
        
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True
        else:
            log(f"SSH Error: {result.stderr[:100]}", "ERROR")
            return False
    except Exception as e:
        log(f"SSH Exception: {e}", "ERROR")
        return False

def ssh_exec_output(cmd: str) -> tuple:
    """Execute SSH command and return output."""
    try:
        full_cmd = f"sshpass -p {PI_PASSWORD} ssh -o StrictHostKeyChecking=no {PI_USER}@{PI_IP} '{cmd}'"
        
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def check_sshpass() -> bool:
    """Check if sshpass is available."""
    result = subprocess.run(
        "sshpass -h",
        shell=True,
        capture_output=True,
        timeout=5
    )
    return result.returncode == 0

def install_sshpass() -> bool:
    """Try to install sshpass."""
    log("Installing sshpass for automated SSH...", "STEP")
    
    # Try different package managers
    commands = [
        "choco install sshpass -y",  # Windows with Chocolatey
        "brew install sshpass",  # macOS
        "apt-get install -y sshpass",  # Ubuntu/Debian
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
            if result.returncode == 0:
                log("sshpass installed successfully", "SUCCESS")
                return True
        except:
            continue
    
    return False

def step_1_setup_sshpass() -> bool:
    """Step 1: Ensure sshpass is available."""
    log("\n" + "="*70, "STEP")
    log("STEP 1: Check SSH Password Tool", "STEP")
    log("="*70, "STEP")
    
    if check_sshpass():
        log("sshpass is already installed", "SUCCESS")
        return True
    
    log("sshpass not found, attempting install...", "WARNING")
    
    if install_sshpass():
        return True
    else:
        log("Could not install sshpass, will continue anyway", "WARNING")
        return True  # Don't fail - we'll try alternative methods

def step_2_setup_directories() -> bool:
    """Step 2: Create directories on Pi."""
    log("\n" + "="*70, "STEP")
    log("STEP 2: Setup Directories on Raspberry Pi", "STEP")
    log("="*70, "STEP")
    
    log(f"Connecting to {PI_USER}@{PI_IP}...", "INFO")
    
    commands = [
        "mkdir -p /home/hhaiviet",
        f"cd /home/{PI_USER} && pwd"
    ]
    
    for cmd in commands:
        log(f"Executing: {cmd}", "INFO")
        if not ssh_exec(cmd):
            log(f"Failed: {cmd}", "ERROR")
            return False
        time.sleep(1)
    
    log("Directories setup complete", "SUCCESS")
    return True

def step_3_clone_project() -> bool:
    """Step 3: Clone project from GitHub."""
    log("\n" + "="*70, "STEP")
    log("STEP 3: Clone Project Repository", "STEP")
    log("="*70, "STEP")
    
    # Check if project exists
    success, output = ssh_exec_output(f"test -d {PI_PROJECT_DIR} && echo 'exists' || echo 'not_exists'")
    
    if success and "exists" in output:
        log(f"Project already exists at {PI_PROJECT_DIR}, updating...", "WARNING")
        cmd = f"cd {PI_PROJECT_DIR} && git pull origin main"
    else:
        log(f"Cloning project to {PI_PROJECT_DIR}...", "INFO")
        cmd = f"cd /home/{PI_USER} && git clone {PROJECT_URL}"
    
    if not ssh_exec(cmd):
        log("Failed to clone/update project", "ERROR")
        return False
    
    log("Project cloned/updated successfully", "SUCCESS")
    return True

def step_4_setup_python_env() -> bool:
    """Step 4: Setup Python virtual environment."""
    log("\n" + "="*70, "STEP")
    log("STEP 4: Setup Python Environment", "STEP")
    log("="*70, "STEP")
    
    commands = [
        f"cd {PI_PROJECT_DIR} && python3 -m venv venv",
        f"cd {PI_PROJECT_DIR} && source venv/bin/activate && pip install --upgrade pip",
        f"cd {PI_PROJECT_DIR} && source venv/bin/activate && pip install -r requirements.txt"
    ]
    
    for cmd in commands:
        log(f"Executing: {cmd[:60]}...", "INFO")
        if not ssh_exec(cmd):
            log(f"Failed: {cmd[:60]}", "ERROR")
            return False
        time.sleep(2)
    
    log("Python environment setup complete", "SUCCESS")
    return True

def step_5_create_env_file() -> bool:
    """Step 5: Create .env file on Pi."""
    log("\n" + "="*70, "STEP")
    log("STEP 5: Create Environment Configuration", "STEP")
    log("="*70, "STEP")
    
    env_content = f"""KIOTVIET_USERNAME=0913431718
KIOTVIET_PASSWORD=68686868
KIOTVIET_RETAILER_ID=248minimart
KIOTVIET_BRANCH_ID=291407

API_BASE_URL=https://api-man1.kiotviet.vn/api
API_TIMEOUT=30
API_MAX_RETRIES=5
API_PAGE_SIZE=100

CHROME_BINARY_PATH=/usr/bin/chromium-browser
CHROMEDRIVER_PATH=/usr/bin/chromedriver
DISPLAY=:99

LOG_LEVEL=INFO
"""
    
    # Create .env file via SSH
    # Escape for shell
    env_escaped = env_content.replace("'", "'\\''")
    cmd = f"cat > {PI_PROJECT_DIR}/.env << 'EOF'\n{env_content}\nEOF"
    
    log("Creating .env file...", "INFO")
    
    # Use a different approach - write to temp file first
    temp_env = "/tmp/env_temp.txt"
    write_cmd = f"echo '{env_escaped}' > {temp_env} && cat {temp_env} > {PI_PROJECT_DIR}/.env"
    
    if not ssh_exec(write_cmd):
        log("Failed to create .env file", "ERROR")
        return False
    
    log(".env file created successfully", "SUCCESS")
    return True

def step_6_create_setup_script() -> bool:
    """Step 6: Create a setup script for debugging on Pi."""
    log("\n" + "="*70, "STEP")
    log("STEP 6: Create Setup Script", "STEP")
    log("="*70, "STEP")
    
    setup_script = f"""#!/bin/bash
cd {PI_PROJECT_DIR}

echo "=== KiotViet Integration Setup on Raspberry Pi ==="
echo ""
echo "Environment: $PWD"
echo "Python: $(python3 --version)"
echo "Git: $(git --version)"
echo ""

echo "Activating virtual environment..."
source venv/bin/activate

echo "Current directory: $(pwd)"
echo "Project files:"
ls -la | head -20

echo ""
echo "Ready for development!"
echo ""
echo "Useful commands:"
echo "  python scripts/kiotviet_run_all.py"
echo "  python scripts/kiotviet_auto_token_enhanced.py"
echo "  python -m pytest tests/ -v"
echo ""
"""
    
    script_escaped = setup_script.replace("'", "'\\''")
    cmd = f"cat > {PI_PROJECT_DIR}/setup.sh << 'SCRIPT'\n{setup_script}\nSCRIPT\nchmod +x {PI_PROJECT_DIR}/setup.sh"
    
    log("Creating setup script...", "INFO")
    if not ssh_exec(cmd):
        log("Failed to create setup script", "WARNING")
        return True  # Don't fail - not critical
    
    log("Setup script created", "SUCCESS")
    return True

def step_7_show_access_info() -> bool:
    """Step 7: Show how to SSH and debug."""
    log("\n" + "="*70, "STEP")
    log("STEP 7: Display Access Information", "STEP")
    log("="*70, "STEP")
    
    # Get Pi uptime/info
    success, uptime = ssh_exec_output("uptime")
    success, free = ssh_exec_output("free -h | head -2")
    
    log("Raspberry Pi Status:", "INFO")
    if uptime:
        log(f"  Uptime: {uptime.strip()}", "INFO")
    if free:
        for line in free.split('\n')[:2]:
            if line.strip():
                log(f"  {line}", "INFO")
    
    return True

def main():
    """Main entry point."""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
    print(f"{Colors.PURPLE}Clone KiotViet Project to Raspberry Pi{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
    
    print(f"Target: {PI_USER}@{PI_IP}")
    print(f"Project: {PROJECT_NAME}")
    print(f"Destination: {PI_PROJECT_DIR}\n")
    
    steps = [
        ("Setup SSH Tool", step_1_setup_sshpass),
        ("Setup Directories", step_2_setup_directories),
        ("Clone Project", step_3_clone_project),
        ("Setup Python", step_4_setup_python_env),
        ("Create .env", step_5_create_env_file),
        ("Create Scripts", step_6_create_setup_script),
        ("Show Info", step_7_show_access_info),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        try:
            if not func():
                log(f"Step {i} failed: {name}", "ERROR")
                print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
                print(f"{Colors.RED}SETUP FAILED AT STEP {i}!{Colors.NC}")
                print(f"{Colors.RED}{'='*70}{Colors.NC}\n")
                return 1
        except Exception as e:
            log(f"Step {i} exception: {e}", "ERROR")
            return 1
        
        time.sleep(1)
    
    print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
    print(f"{Colors.GREEN}PROJECT CLONED AND SETUP COMPLETE!{Colors.NC}")
    print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")
    
    print(f"{Colors.CYAN}Next Steps - SSH into Raspberry Pi:{Colors.NC}\n")
    print(f"  ssh {PI_USER}@{PI_IP}\n")
    
    print(f"{Colors.CYAN}Then run:{Colors.NC}\n")
    print(f"  cd {PI_PROJECT_DIR}")
    print(f"  source venv/bin/activate")
    print(f"  ./setup.sh  # Optional setup script\n")
    
    print(f"{Colors.CYAN}Or directly run:{Colors.NC}\n")
    print(f"  python scripts/kiotviet_run_all.py")
    print(f"  python scripts/kiotviet_auto_token_enhanced.py")
    print(f"  pytest tests/ -v\n")
    
    print(f"{Colors.CYAN}Quick SSH Command:{Colors.NC}\n")
    print(f"  ssh {PI_USER}@{PI_IP} 'cd {PI_PROJECT_DIR} && source venv/bin/activate && bash'\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())