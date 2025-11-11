#!/usr/bin/env python3
"""
Test KiotViet scripts on Raspberry Pi
"""

import paramiko
import sys

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120):
    """Run command and print output in real-time."""
    print(f"\n[*] Running: {cmd[:80]}...\n")
    print("="*70)
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    
    # Print output line by line
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    # Check for errors
    err = stderr.read().decode('utf-8')
    exit_code = stdout.channel.recv_exit_status()
    
    print("="*70)
    
    if err:
        print(f"\n[Errors]:\n{err[:500]}")
    
    return exit_code == 0

def main():
    print("\n" + "="*70)
    print("Test KiotViet Scripts on Raspberry Pi")
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
        # Test 1: Check project structure
        print("[1] Checking project structure...\n")
        
        check_cmd = f"""
cd {PI_PROJECT_DIR}
echo "Project files:"
ls -la scripts/kiotviet_*.py | head -5
echo ""
echo "Token file:"
ls -la data/credentials/token.json
echo ""
echo "Python environment:"
source venv/bin/activate
python --version
pip list | grep -i kiotviet || echo "No kiotviet in pip list"
"""
        
        run_cmd(ssh, check_cmd)
        
        # Test 2: Run token verification
        print("\n[2] Verifying token...\n")
        
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

python3 << 'PYEOF'
import json
with open('data/credentials/token.json', 'r') as f:
    token = json.load(f)

print("[OK] Token loaded successfully")
print(f"     - access_token: {{token['access_token'][:50]}}...")
print(f"     - retailer_id: {{token['retailer_id']}}")
print(f"     - branch_id: {{token['branch_id']}}")
PYEOF
"""
        
        run_cmd(ssh, token_cmd)
        
        # Test 3: Check API connectivity
        print("\n[3] Testing API connectivity...\n")
        
        api_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from src.api.client import KiotVietClient
from src.services.token_service import TokenService

# Load token
token_service = TokenService('data/credentials/token.json')
creds = token_service.load()

# Create client
client = KiotVietClient(creds)

# Try to get current branch
try:
    result = client.get("/branch/current")
    if result:
        print("[OK] API connection successful!")
        print(f"     Response: {{str(result)[:100]}}...")
    else:
        print("[!] API returned empty response")
except Exception as e:
    print(f"[ERROR] API call failed: {{e}}")
    sys.exit(1)
PYEOF
"""
        
        success = run_cmd(ssh, api_cmd, timeout=30)
        
        print("\n" + "="*70)
        if success:
            print("[OK] All tests passed!")
            print("="*70 + "\n")
            print("[*] Scripts are ready. You can:")
            print(f"    ssh {PI_USER}@{PI_IP}")
            print(f"    cd {PI_PROJECT_DIR}")
            print("    python scripts/kiotviet_run_all.py")
            print()
        else:
            print("[!] Some tests had issues")
            print("="*70 + "\n")
        
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
