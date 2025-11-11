#!/usr/bin/env python3
"""
Run token script on Pi with detailed output
"""

import paramiko
import sys
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def main():
    print("\n" + "="*70)
    print("KiotViet Token Generation on Raspberry Pi")
    print("="*70 + "\n")
    
    try:
        # Connect SSH
        print(f"[1] Connecting to {PI_USER}@{PI_IP}...")
        
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
        
        # First, check if script exists
        print("[2] Checking for token script...")
        stdin, stdout, stderr = ssh.exec_command(
            f"ls -la {PI_PROJECT_DIR}/scripts/ | grep token"
        )
        output = stdout.read().decode('utf-8')
        print(output)
        
        time.sleep(1)
        
        # Run token generation
        print("\n[3] Running token generation...\n")
        print("="*70)
        
        cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "Working directory: $(pwd)"
echo "Python: $(python --version)"
echo "Available token scripts:"
ls -la scripts/kiotviet_auto_token*.py
echo ""

# Check for dependencies
echo "Checking dependencies..."
python -c "import selenium; print(f'Selenium: OK')" 2>/dev/null || echo "Selenium: MISSING"
python -c "import seleniumwire; print(f'SeleniumWire: OK')" 2>/dev/null || echo "SeleniumWire: MISSING"

echo ""
echo "Running token script..."
python scripts/kiotviet_auto_token_seleniumwire.py 2>&1 | head -50
"""
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
        
        # Print output line by line in real-time
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.rstrip())
        
        # Check for errors
        err_output = stderr.read().decode('utf-8')
        if err_output:
            print("\n[Errors]:")
            print(err_output[:500])
        
        print("="*70)
        
        # Get exit status
        exit_code = stdout.channel.recv_exit_status()
        print(f"\n[✓] Script completed with exit code: {exit_code}\n")
        
        ssh.close()
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
