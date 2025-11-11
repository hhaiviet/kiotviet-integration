#!/usr/bin/env python3
"""
Upload real token to Raspberry Pi
"""

import paramiko
import json
from pathlib import Path
import sys
import os

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

# Token from local file
# Determine project root correctly
SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / "data" / "credentials" / "token.json"

def main():
    print("\n" + "="*70)
    print("Upload Real Token to Raspberry Pi")
    print("="*70 + "\n")
    
    # Read local token
    if not TOKEN_FILE.exists():
        print(f"[ERROR] Token file not found: {TOKEN_FILE}")
        return 1
    
    print(f"[*] Reading token from {TOKEN_FILE}...")
    
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)
    
    print(f"[OK] Token loaded")
    print(f"     - access_token: {token_data.get('access_token', 'N/A')[:50]}...")
    print(f"     - retailer_id: {token_data.get('retailer_id')}")
    print(f"     - branch_id: {token_data.get('branch_id')}")
    
    # Connect to Pi
    print(f"\n[*] Connecting to {PI_USER}@{PI_IP}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
                   timeout=30, allow_agent=False, look_for_keys=False)
        print("[OK] Connected")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return 1
    
    # Upload token
    print(f"\n[*] Uploading token to Pi...")
    
    remote_token_file = f"{PI_PROJECT_DIR}/data/credentials/token.json"
    
    try:
        # Use SFTP to upload
        sftp = ssh.open_sftp()
        
        # Create directories if needed
        try:
            sftp.stat(f"{PI_PROJECT_DIR}/data/credentials")
        except IOError:
            # Directory doesn't exist, create it
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {PI_PROJECT_DIR}/data/credentials")
            stdout.channel.recv_exit_status()
        
        # Upload token file
        token_json = json.dumps(token_data, indent=2)
        
        with sftp.file(remote_token_file, 'w') as f:
            f.write(token_json)
        
        print(f"[OK] Token uploaded to {remote_token_file}")
        
        sftp.close()
    except Exception as e:
        print(f"[ERROR] SFTP upload failed: {e}")
        
        # Fallback: use echo command
        print("\n[*] Trying fallback method with SSH command...")
        
        token_escaped = json.dumps(token_data, indent=2).replace('"', '\\"')
        cmd = f"""
mkdir -p {PI_PROJECT_DIR}/data/credentials
cat > {remote_token_file} << 'EOF'
{json.dumps(token_data, indent=2)}
EOF
"""
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"[OK] Token uploaded via SSH command")
        else:
            print(f"[ERROR] Upload failed")
            print(stderr.read().decode())
            return 1
    
    # Verify token on Pi
    print(f"\n[*] Verifying token on Pi...")
    
    stdin, stdout, stderr = ssh.exec_command(f"cat {remote_token_file}")
    remote_token = stdout.read().decode()
    
    if remote_token:
        remote_data = json.loads(remote_token)
        print("[OK] Token verified on Pi:")
        print(f"     - access_token: {remote_data.get('access_token', 'N/A')[:50]}...")
        print(f"     - retailer_id: {remote_data.get('retailer_id')}")
        print(f"     - branch_id: {remote_data.get('branch_id')}")
    else:
        print("[ERROR] Could not verify token on Pi")
        return 1
    
    ssh.close()
    
    print("\n" + "="*70)
    print("[OK] Real token uploaded to Raspberry Pi!")
    print("="*70 + "\n")
    
    print("[*] You can now test the scripts:")
    print(f"    ssh {PI_USER}@{PI_IP}")
    print(f"    cd {PI_PROJECT_DIR}")
    print("    python scripts/kiotviet_run_all.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
