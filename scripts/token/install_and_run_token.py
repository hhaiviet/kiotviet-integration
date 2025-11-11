#!/usr/bin/env python3
"""
Install missing dependencies on Pi and run token script
"""

import paramiko
import sys
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120, show_output=True):
    """Run command and optionally show output."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    
    if show_output:
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.rstrip())
    
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    
    return exit_code == 0, err

def main():
    print("\n" + "="*70)
    print("Setup Dependencies and Run Token Script")
    print("="*70 + "\n")
    
    try:
        print("[1] Connecting to Pi...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=PI_IP,
            username=PI_USER,
            password=PI_PASSWORD,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        print("[✓] Connected!\n")
        
        # Step 1: Install system dependencies
        print("[2] Installing system dependencies for browser...\n")
        
        system_deps = [
            "sudo apt-get update",
            "sudo apt-get install -y chromium-browser chromium-browser-l10n xvfb",
        ]
        
        for cmd in system_deps:
            print(f"Running: {cmd[:60]}...")
            success, err = run_cmd(ssh, cmd, timeout=180, show_output=False)
            if success:
                print("[✓] Done\n")
            else:
                print(f"[!] Error: {err[:100]}\n")
        
        # Step 2: Install Python dependencies
        print("[3] Installing Python dependencies...\n")
        
        python_deps_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "Installing from requirements.txt..."
pip install --upgrade pip setuptools wheel

# Install specific packages
pip install selenium>=4.0
pip install selenium-wire>=5.0
pip install requests
pip install pillow
pip install webdriver-manager
pip install pyvirtualdisplay
"""
        
        success, err = run_cmd(ssh, python_deps_cmd, timeout=300, show_output=True)
        print()
        
        if not success and err:
            print(f"[!] Errors: {err[:200]}\n")
        
        # Step 3: Verify dependencies
        print("\n[4] Verifying dependencies...\n")
        
        verify_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

python -c "import selenium; print(f'✓ Selenium: {{selenium.__version__}}')" 
python -c "import seleniumwire; print(f'✓ SeleniumWire: OK')"
python -c "import requests; print(f'✓ Requests: OK')"
python -c "import PIL; print(f'✓ Pillow: OK')"
"""
        
        success, err = run_cmd(ssh, verify_cmd, timeout=60, show_output=True)
        print()
        
        # Step 4: Run token script
        print("[5] Running token generation script...\n")
        print("="*70 + "\n")
        
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

# Check environment
echo "Environment:"
echo "  Python: $(python --version)"
echo "  CWD: $(pwd)"
echo "  DISPLAY: ${{DISPLAY}}"
echo ""

# Try running token script
python scripts/kiotviet_auto_token_seleniumwire.py
"""
        
        success, err = run_cmd(ssh, token_cmd, timeout=300, show_output=True)
        
        print("\n" + "="*70)
        
        if err:
            print(f"\nErrors/Warnings:\n{err[:500]}")
        
        print(f"\n[✓] Token generation script completed!\n")
        
        ssh.close()
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
