#!/usr/bin/env python3
"""
Clone KiotViet Project to Raspberry Pi using Paramiko SSH
Better than sshpass - pure Python SSH library
"""

import sys
import time
import paramiko
from pathlib import Path

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
        "SUCCESS": (Colors.GREEN, "[✓]"),
        "ERROR": (Colors.RED, "[✗]"),
        "WARNING": (Colors.YELLOW, "[!]"),
        "INFO": (Colors.BLUE, "[•]"),
        "STEP": (Colors.PURPLE, "[>>>]"),
    }
    
    color, prefix = levels.get(level, (Colors.BLUE, "[?]"))
    print(f"{color}[{ts}] {prefix}{Colors.NC} {msg}")

class SSHClient:
    """SSH client wrapper."""
    
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.client = None
    
    def connect(self) -> bool:
        """Connect to SSH server."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            log(f"Connecting to {self.user}@{self.host}...", "INFO")
            
            self.client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            log("SSH connection established", "SUCCESS")
            return True
        except Exception as e:
            log(f"SSH Connection failed: {e}", "ERROR")
            return False
    
    def execute(self, cmd: str, timeout: int = 60) -> tuple:
        """Execute command and return (success, stdout, stderr)."""
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            
            exit_code = stdout.channel.recv_exit_status()
            
            return exit_code == 0, out, err
        except Exception as e:
            log(f"Execute error: {e}", "ERROR")
            return False, "", str(e)
    
    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()

def step_1_connect() -> SSHClient:
    """Step 1: Connect to Pi."""
    log("\n" + "="*70, "STEP")
    log("STEP 1: SSH Connection to Raspberry Pi", "STEP")
    log("="*70, "STEP")
    
    ssh = SSHClient(PI_IP, PI_USER, PI_PASSWORD)
    if ssh.connect():
        return ssh
    else:
        return None

def step_2_setup_directories(ssh: SSHClient) -> bool:
    """Step 2: Create directories."""
    log("\n" + "="*70, "STEP")
    log("STEP 2: Setup Directories", "STEP")
    log("="*70, "STEP")
    
    cmd = f"mkdir -p /home/{PI_USER} && pwd"
    success, out, err = ssh.execute(cmd)
    
    if success:
        log(f"Directory ready: {out.strip()}", "SUCCESS")
        return True
    else:
        log(f"Failed to setup directories: {err}", "ERROR")
        return False

def step_3_clone_project(ssh: SSHClient) -> bool:
    """Step 3: Clone or update project."""
    log("\n" + "="*70, "STEP")
    log("STEP 3: Clone/Update Project Repository", "STEP")
    log("="*70, "STEP")
    
    # Check if exists
    success, out, err = ssh.execute(f"test -d {PI_PROJECT_DIR} && echo 'EXISTS' || echo 'NOT_EXISTS'")
    
    if success and "EXISTS" in out:
        log(f"Project exists, updating...", "WARNING")
        cmd = f"cd {PI_PROJECT_DIR} && git pull origin main"
    else:
        log(f"Cloning project from GitHub...", "INFO")
        cmd = f"cd /home/{PI_USER} && git clone {PROJECT_URL}"
    
    log(f"Running: {cmd[:60]}...", "INFO")
    success, out, err = ssh.execute(cmd, timeout=120)
    
    if success:
        log("Project cloned/updated successfully", "SUCCESS")
        if out:
            for line in out.split('\n')[-5:]:
                if line.strip():
                    log(f"  → {line[:70]}", "INFO")
        return True
    else:
        log(f"Clone failed: {err[:100]}", "ERROR")
        return False

def step_4_setup_python_env(ssh: SSHClient) -> bool:
    """Step 4: Setup Python virtual environment."""
    log("\n" + "="*70, "STEP")
    log("STEP 4: Setup Python Virtual Environment", "STEP")
    log("="*70, "STEP")
    
    steps = [
        (f"cd {PI_PROJECT_DIR} && python3 -m venv venv", "Creating venv"),
        (f"cd {PI_PROJECT_DIR} && source venv/bin/activate && pip install --upgrade pip setuptools wheel", "Upgrading pip"),
        (f"cd {PI_PROJECT_DIR} && source venv/bin/activate && pip install -r requirements.txt", "Installing requirements"),
    ]
    
    for cmd, desc in steps:
        log(f"{desc}...", "INFO")
        success, out, err = ssh.execute(cmd, timeout=180)
        
        if not success:
            log(f"Failed: {err[:100]}", "ERROR")
            return False
        
        log(f"✓ {desc}", "SUCCESS")
        time.sleep(1)
    
    return True

def step_5_create_env_file(ssh: SSHClient) -> bool:
    """Step 5: Create .env file."""
    log("\n" + "="*70, "STEP")
    log("STEP 5: Create Environment Configuration", "STEP")
    log("="*70, "STEP")
    
    env_content = """KIOTVIET_USERNAME=0913431718
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
DEBUG=False
"""
    
    # Use here-doc to create file
    cmd = f"""cat > {PI_PROJECT_DIR}/.env << 'EOF'
{env_content}
EOF"""
    
    log("Creating .env file...", "INFO")
    success, out, err = ssh.execute(cmd)
    
    if success:
        log(".env file created", "SUCCESS")
        return True
    else:
        log(f"Failed: {err[:100]}", "ERROR")
        return False

def step_6_create_convenience_script(ssh: SSHClient) -> bool:
    """Step 6: Create convenient run scripts."""
    log("\n" + "="*70, "STEP")
    log("STEP 6: Create Convenience Scripts", "STEP")
    log("="*70, "STEP")
    
    # Create activate.sh
    activate_script = f"""#!/bin/bash
cd {PI_PROJECT_DIR}
source venv/bin/activate
echo "Environment activated!"
bash
"""
    
    cmd = f"""cat > {PI_PROJECT_DIR}/activate.sh << 'SCRIPT'
{activate_script}
SCRIPT
chmod +x {PI_PROJECT_DIR}/activate.sh
"""
    
    success, out, err = ssh.execute(cmd)
    if success:
        log("Convenience scripts created", "SUCCESS")
    
    return True

def step_7_verify_setup(ssh: SSHClient) -> bool:
    """Step 7: Verify everything is working."""
    log("\n" + "="*70, "STEP")
    log("STEP 7: Verify Setup", "STEP")
    log("="*70, "STEP")
    
    checks = [
        (f"test -d {PI_PROJECT_DIR} && echo 'Project directory exists'", "Project directory"),
        (f"test -f {PI_PROJECT_DIR}/.env && echo '.env file exists'", ".env file"),
        (f"test -d {PI_PROJECT_DIR}/venv && echo 'Virtual environment exists'", "Virtual environment"),
        (f"cd {PI_PROJECT_DIR} && source venv/bin/activate && python --version", "Python version"),
    ]
    
    all_ok = True
    for cmd, desc in checks:
        success, out, err = ssh.execute(cmd)
        
        if success and out.strip():
            log(f"✓ {desc}: {out.strip()[:50]}", "SUCCESS")
        else:
            log(f"✗ {desc}: {err[:50] if err else 'Not found'}", "ERROR")
            all_ok = False
    
    return all_ok

def step_8_show_info(ssh: SSHClient) -> bool:
    """Step 8: Show system info."""
    log("\n" + "="*70, "STEP")
    log("STEP 8: Raspberry Pi System Info", "STEP")
    log("="*70, "STEP")
    
    info_cmds = [
        ("uname -a", "System"),
        ("free -h | head -2", "Memory"),
        ("df -h | head -2", "Disk"),
        ("uptime", "Uptime"),
    ]
    
    for cmd, label in info_cmds:
        success, out, err = ssh.execute(cmd)
        if success:
            lines = out.strip().split('\n')
            for line in lines:
                if line.strip():
                    log(f"{label}: {line[:60]}", "INFO")
        time.sleep(0.5)
    
    return True

def main():
    """Main entry point."""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
    print(f"{Colors.PURPLE}Clone KiotViet Project to Raspberry Pi{Colors.NC}")
    print(f"{Colors.PURPLE}Using Paramiko SSH Library{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
    
    print(f"Target: {Colors.CYAN}{PI_USER}@{PI_IP}{Colors.NC}")
    print(f"Project: {Colors.CYAN}{PROJECT_NAME}{Colors.NC}")
    print(f"Destination: {Colors.CYAN}{PI_PROJECT_DIR}{Colors.NC}\n")
    
    # Step 1: Connect
    ssh = step_1_connect()
    if not ssh:
        print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
        print(f"{Colors.RED}Connection failed!{Colors.NC}")
        print(f"{Colors.RED}{'='*70}{Colors.NC}\n")
        return 1
    
    try:
        steps = [
            ("Setup Directories", step_2_setup_directories),
            ("Clone Project", step_3_clone_project),
            ("Setup Python Env", step_4_setup_python_env),
            ("Create .env", step_5_create_env_file),
            ("Create Scripts", step_6_create_convenience_script),
            ("Verify Setup", step_7_verify_setup),
            ("Show Info", step_8_show_info),
        ]
        
        for i, (name, func) in enumerate(steps, 1):
            try:
                if not func(ssh):
                    log(f"Step {i} failed: {name}", "ERROR")
                    return 1
            except Exception as e:
                log(f"Step {i} exception: {e}", "ERROR")
                return 1
            
            time.sleep(1)
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
        print(f"{Colors.GREEN}PROJECT CLONED AND SETUP COMPLETE!{Colors.NC}")
        print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")
        
        print(f"{Colors.CYAN}SSH Access:{Colors.NC}\n")
        print(f"  Command: ssh {PI_USER}@{PI_IP}\n")
        
        print(f"{Colors.CYAN}After SSH, activate the environment:{Colors.NC}\n")
        print(f"  cd {PI_PROJECT_DIR}")
        print(f"  source venv/bin/activate\n")
        
        print(f"{Colors.CYAN}Or use the convenience script:{Colors.NC}\n")
        print(f"  ssh {PI_USER}@{PI_IP} '{PI_PROJECT_DIR}/activate.sh'\n")
        
        print(f"{Colors.CYAN}Try running the scripts:{Colors.NC}\n")
        print(f"  python scripts/kiotviet_run_all.py")
        print(f"  python scripts/kiotviet_auto_token_enhanced.py")
        print(f"  python -m pytest tests/ -v\n")
        
        return 0
    
    finally:
        ssh.close()
        log("SSH connection closed", "INFO")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.NC}")
        sys.exit(1)
