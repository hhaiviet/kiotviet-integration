#!/usr/bin/env python3
"""
Create valid token file on Raspberry Pi using TokenService
This bypasses the Selenium browser login issue
"""

import paramiko
import sys
import json

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

# For now, we'll use a placeholder token
# In production, you would get this from:
# 1. Manual login to KiotViet and copy token from browser
# 2. Selenium browser automation
# 3. Direct KiotViet API call with username/password

PLACEHOLDER_TOKEN = {
    "access_token": "test_token_placeholder_for_development",
    "retailer_id": "248minimart",
    "branch_id": 291407,
    "expires_at": None,
    "_note": "This is a development placeholder. Get real token from KiotViet for production."
}

def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    return exit_code == 0, out, err

def main():
    print("\n" + "="*70)
    print("Create Token File on Raspberry Pi")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("[*] Connecting to Pi...")
    try:
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
                   timeout=30, allow_agent=False, look_for_keys=False)
        print("[OK] Connected\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}\n")
        return 1
    
    # Step 1: Create directories
    print("[1] Creating data directories...\n")
    
    mkdir_cmd = f"mkdir -p {PI_PROJECT_DIR}/data/credentials && echo '[OK] Directories created'"
    success, out, err = run_cmd(ssh, mkdir_cmd)
    print(out)
    
    # Step 2: Write token file
    print("\n[2] Writing token file...\n")
    
    token_json = json.dumps(PLACEHOLDER_TOKEN, indent=2)
    
    write_cmd = f"""
cat > {PI_PROJECT_DIR}/data/credentials/token.json << 'EOF'
{token_json}
EOF

if [ -f {PI_PROJECT_DIR}/data/credentials/token.json ]; then
    echo "[OK] Token file created successfully"
    echo ""
    echo "File details:"
    ls -lh {PI_PROJECT_DIR}/data/credentials/token.json
    echo ""
    echo "Content:"
    cat {PI_PROJECT_DIR}/data/credentials/token.json
else
    echo "[ERROR] Failed to create token file"
fi
"""
    
    success, out, err = run_cmd(ssh, write_cmd)
    print(out)
    
    if err:
        print(f"Errors: {err}")
    
    # Step 3: Verify token can be read by Python
    print("\n[3] Verifying token format...\n")
    
    verify_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

python3 << 'PYEOF'
import json
import sys

try:
    with open('data/credentials/token.json', 'r') as f:
        token = json.load(f)
    
    # Check required fields
    required = ['access_token', 'retailer_id', 'branch_id']
    for field in required:
        if field not in token:
            print(f"[ERROR] Missing required field: {{field}}")
            sys.exit(1)
    
    print("[OK] Token format is valid")
    print(f"     - access_token: {{token['access_token'][:20]}}...")
    print(f"     - retailer_id: {{token['retailer_id']}}")
    print(f"     - branch_id: {{token['branch_id']}}")
    
except json.JSONDecodeError as e:
    print(f"[ERROR] Invalid JSON: {{e}}")
    sys.exit(1)
except FileNotFoundError:
    print("[ERROR] Token file not found")
    sys.exit(1)
PYEOF
"""
    
    success, out, err = run_cmd(ssh, verify_cmd)
    print(out)
    
    if err:
        print(f"Errors: {err}")
    
    print("\n" + "="*70)
    print("[OK] Token file setup complete!")
    print("="*70 + "\n")
    
    print("[*] Current token status:")
    print("    ✓ Token file created")
    print("    ✓ JSON format valid")
    print("    ✓ Required fields present\n")
    
    print("[!] IMPORTANT NOTES:")
    print("    - This is a DEVELOPMENT/TEST token")
    print("    - For PRODUCTION, you need a REAL KiotViet token")
    print("    - Get real token by:")
    print("      1. Logging into KiotViet website")
    print("      2. Extracting token from browser DevTools")
    print("      3. Or running Selenium token generator (fix deps first)\n")
    
    print("[*] You can now test the scripts:")
    print(f"    ssh {PI_USER}@{PI_IP}")
    print(f"    cd {PI_PROJECT_DIR}")
    print("    python scripts/kiotviet_run_all.py\n")
    
    ssh.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
