#!/usr/bin/env python3
"""
Install core requirements on Pi (skip problematic selenium-wire)
"""

import paramiko
import sys

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120):
    """Run command and return output."""
    print(f"\n>>> {cmd}\n")
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    
    # Read output
    out_lines = []
    for line in stdout:
        print(line.rstrip())
        out_lines.append(line)
    
    err = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    
    return exit_code == 0, err

def main():
    print("\n" + "="*70)
    print("Install Core Requirements on Pi")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("[*] Connecting to Pi...")
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
                   timeout=30, allow_agent=False, look_for_keys=False)
        print("[OK] Connected\n")
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    try:
        # Install core packages (skip selenium-wire which has issues)
        packages = [
            "requests",
            "pyyaml",
            "python-dotenv",
            "pandas",
            "openpyxl",
            "click",
            "rich",
            "tqdm",
            "pydantic",
            "dataclasses-json",
            "tenacity",
            "schedule",
            "azure-storage-blob",
        ]
        
        print("[1] Installing core packages...\n")
        
        for pkg in packages:
            cmd = f"cd {PI_PROJECT_DIR} && source venv/bin/activate && pip install -q {pkg}"
            success, err = run_cmd(ssh, cmd, timeout=60)
            
            status = "[OK]" if success else "[!]"
            print(f"{status} {pkg}")
            
            if err and "error" in err.lower():
                print(f"    Warning: {err[:100]}")
        
        # Verify key modules
        print("\n[2] Verifying installations...\n")
        
        verify_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate
python3 -c "
import yaml
import requests
import pandas
import pydantic
import click
print('[OK] All key modules imported successfully!')
"
"""
        
        success, err = run_cmd(ssh, verify_cmd, timeout=30)
        
        if success:
            print("\n[OK] Installation successful!\n")
        else:
            print(f"\n[!] Some issues: {err}\n")
        
        # Test token loading
        print("[3] Testing token loading...\n")
        
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate
python3 -c "
import json
with open('data/credentials/token.json') as f:
    token = json.load(f)
print('[OK] Token file loaded')
print(f'    Retailer: {{token.get(\"retailer_id\")}}')
print(f'    Branch: {{token.get(\"branch_id\")}}')
print(f'    Token: {{token.get(\"access_token\")[:30]}}...')
"
"""
        
        success, err = run_cmd(ssh, token_cmd, timeout=30)
        
        if not success and err:
            print(f"[!] {err}")
        
        print("\n" + "="*70)
        print("[OK] Setup complete!")
        print("="*70 + "\n")
        
        print("Next steps:")
        print(f"  1. SSH to Pi: ssh {PI_USER}@{PI_IP}")
        print(f"  2. CD: cd {PI_PROJECT_DIR}")
        print(f"  3. Activate venv: source venv/bin/activate")
        print(f"  4. Run full sync: python scripts/kiotviet_run_all.py")
        print()
        
        ssh.close()
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        ssh.close()
        return 1

if __name__ == "__main__":
    sys.exit(main())
