#!/usr/bin/env python3
"""
Quick workaround: Create sample token file to test deployment
This allows us to proceed with testing the rest of the stack
"""

import paramiko
import json
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    print("\n" + "="*70)
    print("Create Sample Token for Testing")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
               timeout=30, allow_agent=False, look_for_keys=False)
    
    print("[*] Creating directories...\n")
    
    # Create directories
    run_cmd(ssh, f"mkdir -p {PI_PROJECT_DIR}/data/credentials")
    
    # Create a sample token JSON
    sample_token = {
        "retailer_id": "248minimart",
        "access_token": "sample_token_for_development",
        "token_type": "Bearer",
        "expires_in": 3600,
        "created_at": int(time.time()),
        "notes": "This is a placeholder token for development/testing. Run the actual token script when ready."
    }
    
    print("[*] Creating sample token file...\n")
    
    # Write token to file on Pi
    token_json = json.dumps(sample_token, indent=2)
    token_escaped = token_json.replace('"', '\\"')
    
    cmd = f"""
cd {PI_PROJECT_DIR}
cat > data/credentials/token.json << 'EOF'
{token_json}
EOF

echo "[OK] Token file created:"
ls -la data/credentials/token.json
echo ""
echo "Content:"
cat data/credentials/token.json
"""
    
    out, err = run_cmd(ssh, cmd)
    print(out)
    
    if err:
        print(f"Errors: {err}")
    
    print("\n" + "="*70)
    print("[OK] Sample token created!")
    print("="*70 + "\n")
    
    print("[!] IMPORTANT:")
    print("    - This is a PLACEHOLDER token for testing the infrastructure")
    print("    - To get REAL KiotViet token, you need to:")
    print("      1. Fix Selenium/SeleniumWire installation issues")
    print("      2. Or use KiotViet API directly with credentials")
    print("      3. Or get token manually from KiotViet dashboard\n")
    
    print("[*] Next: Test if the scripts can run now")
    print("    SSH into Pi and run:")
    print(f"    ssh {PI_USER}@{PI_IP}")
    print(f"    cd {PI_PROJECT_DIR}")
    print("    python scripts/kiotviet_run_all.py\n")
    
    ssh.close()

if __name__ == "__main__":
    main()
