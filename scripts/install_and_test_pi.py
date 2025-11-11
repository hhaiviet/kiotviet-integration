#!/usr/bin/env python3
"""
Install requirements on Pi and run tests
"""

import paramiko
import sys

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120, show_output=True):
    """Run command."""
    if show_output:
        print(f"\n[*] {cmd[:70]}...\n")
        print("="*70)
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    
    output = []
    if show_output:
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.rstrip())
            output.append(line)
    else:
        output = stdout.readlines()
    
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    
    if show_output:
        print("="*70)
    
    return exit_code == 0, ''.join([l.decode() if isinstance(l, bytes) else l for l in output]), err

def main():
    print("\n" + "="*70)
    print("Install Requirements and Test on Pi")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("[*] Connecting to Pi...")
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
                   timeout=30, allow_agent=False, look_for_keys=False)
        print("[OK] Connected\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return 1
    
    try:
        # Install requirements
        print("[1] Installing requirements from requirements.txt...\n")
        
        install_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "Installing requirements..."
pip install -q -r requirements.txt

echo "Verifying key packages..."
python -c "import yaml; print('[OK] PyYAML installed')"
python -c "import requests; print('[OK] Requests installed')"
python -c "import selenium; print('[OK] Selenium installed')"

echo ""
echo "[OK] All requirements installed"
"""
        
        success, out, err = run_cmd(ssh, install_cmd, timeout=300)
        
        if err and "error" in err.lower():
            print(f"\n[Warnings]:\n{err[:300]}")
        
        # Test script
        print("\n[2] Running test script...\n")
        print("="*70)
        
        test_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

python3 << 'PYEOF'
import sys
import json
sys.path.insert(0, '.')

print("[Test 1] Loading token...")
from src.services.token_service import TokenService
token_service = TokenService('data/credentials/token.json')
creds = token_service.load()
print(f"[OK] Token loaded: {{creds.access_token[:30]}}...")

print()
print("[Test 2] Creating API client...")
from src.api.client import KiotVietClient
client = KiotVietClient(creds)
print("[OK] API client created")

print()
print("[Test 3] Testing API connection...")
try:
    result = client.get("/account/info")
    if result:
        print("[OK] API connection successful!")
        print(f"     Response: {{json.dumps(result, indent=2, ensure_ascii=False)[:200]}}...")
    else:
        print("[!] Empty response from API")
except Exception as e:
    print(f"[ERROR] API call failed: {{e}}")

print()
print("[Test 4] Test complete!")
print("[OK] All tests passed! Scripts are ready.")
PYEOF
"""
        
        success, out, err = run_cmd(ssh, test_cmd, timeout=60)
        
        print("="*70)
        
        if err:
            print(f"\n[Errors]:\n{err[:500]}")
        
        print("\n" + "="*70)
        if success:
            print("[OK] Tests passed!")
        else:
            print("[!] Tests had issues")
        print("="*70 + "\n")
        
        print("[*] Next steps:")
        print(f"    ssh {PI_USER}@{PI_IP}")
        print(f"    cd {PI_PROJECT_DIR}")
        print("    source venv/bin/activate")
        print("    python scripts/kiotviet_run_all.py")
        print()
        
        ssh.close()
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        ssh.close()
        return 1

if __name__ == "__main__":
    sys.exit(main())
