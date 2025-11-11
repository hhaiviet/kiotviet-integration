#!/usr/bin/env python3
"""
Install dependencies and run token script on Pi
Skip sudo commands that need password
"""

import paramiko
import sys
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120):
    """Run command and return output."""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    
    output = []
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
        output.append(line)
    
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    
    return exit_code == 0, err

def main():
    print("\n" + "="*70)
    print("Install Deps and Run Token Script on Pi")
    print("="*70 + "\n")
    
    try:
        print("[*] Connecting to Pi...")
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
        print("[OK] Connected!\n")
        
        time.sleep(1)
        
        # Install Python deps only (skip system sudo)
        print("[*] Installing Python dependencies...\n")
        
        install_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "=== Python Dependencies ==="
pip install --no-cache-dir \\
    selenium \\
    selenium-wire \\
    requests \\
    Pillow \\
    webdriver-manager \\
    pyvirtualdisplay

echo ""
echo "=== Verify Dependencies ==="
python3 << 'PYEOF'
try:
    import selenium
    print(f"[OK] Selenium {{selenium.__version__}}")
except:
    print("[XX] Selenium failed")

try:
    import seleniumwire
    print("[OK] SeleniumWire OK")
except:
    print("[XX] SeleniumWire failed")

try:
    import requests
    print("[OK] Requests OK")
except:
    print("[XX] Requests failed")

try:
    from PIL import Image
    print("[OK] Pillow OK")
except:
    print("[XX] Pillow failed")
PYEOF
"""
        
        print("Installing packages (this may take a few minutes)...\n")
        success, err = run_cmd(ssh, install_cmd, timeout=600)
        
        print()
        
        if err:
            print(f"[!] Errors:\n{err[:300]}\n")
        
        time.sleep(2)
        
        # Run token script
        print("\n[*] Running token generation...\n")
        print("="*70 + "\n")
        
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "Environment:"
python3 -c "import sys; print(f'  Python: {{sys.version}}')"
echo "  CWD: $(pwd)"
echo "  DISPLAY: ${{DISPLAY}}"
echo ""

echo "Running token script..."
python3 scripts/kiotviet_auto_token_seleniumwire.py 2>&1 | head -100
"""
        
        success, err = run_cmd(ssh, token_cmd, timeout=300)
        
        print("\n" + "="*70)
        print("\n[OK] Token script executed!\n")
        
        # Check if token was saved
        print("[*] Checking for saved token...\n")
        
        check_cmd = f"""
cd {PI_PROJECT_DIR}
find . -name "*token*" -type f 2>/dev/null | head -10
ls -la .env 2>/dev/null || echo "No .env file"
grep -i "token\\|api" .env 2>/dev/null | head -5 || echo "No token in .env"
"""
        
        success, err = run_cmd(ssh, check_cmd, timeout=60)
        
        ssh.close()
        print("\n[OK] Done!\n")
        return 0
        
    except KeyboardInterrupt:
        print("\n[!] Interrupted\n")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
