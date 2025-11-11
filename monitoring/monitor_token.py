#!/usr/bin/env python3
"""
Monitor token generation on Pi
"""

import paramiko
import time
import sys

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
    
    print("\n[*] Monitoring token generation process on Pi...\n")
    print("="*70)
    
    for i in range(60):  # Check for 60 seconds
        # Check if script is still running
        stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python.*token' || echo 'DONE'", timeout=5)
        result = stdout.read().decode('utf-8').strip()
        
        # Get process info
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep -i token | grep -v grep | head -3", timeout=5)
        procs = stdout.read().decode('utf-8').strip()
        
        print(f"[{i}s] Process status: {result}")
        if procs:
            for line in procs.split('\n')[:2]:
                if line.strip():
                    print(f"       {line[:80]}")
        
        # Check for output files
        stdin, stdout, stderr = ssh.exec_command(f"ls -ltr {PI_PROJECT_DIR}/*.json {PI_PROJECT_DIR}/*.txt 2>/dev/null | tail -3", timeout=5)
        files = stdout.read().decode('utf-8').strip()
        
        if "DONE" in result:
            print("\n[OK] Process completed!")
            if files:
                print("\n[*] Output files:")
                for line in files.split('\n'):
                    if line.strip():
                        print(f"       {line}")
            break
        
        time.sleep(1)
    
    print("\n" + "="*70)
    print("\n[*] Checking for saved data...\n")
    
    # Look for token in .env
    stdin, stdout, stderr = ssh.exec_command(f"grep -i 'token\\|api_key' {PI_PROJECT_DIR}/.env 2>/dev/null | head -5", timeout=5)
    tokens = stdout.read().decode('utf-8').strip()
    
    if tokens:
        print("[OK] Found tokens in .env:\n")
        print(tokens[:200])
    else:
        print("[!] No tokens found in .env yet")
    
    # Check for JSON output
    stdin, stdout, stderr = ssh.exec_command(f"find {PI_PROJECT_DIR} -name '*.json' -mmin -5 2>/dev/null", timeout=5)
    json_files = stdout.read().decode('utf-8').strip()
    
    if json_files:
        print("\n[OK] Recent JSON files created:\n")
        for f in json_files.split('\n')[:3]:
            if f.strip():
                print(f"       {f}")
                # Try to read first few lines
                stdin, stdout, stderr = ssh.exec_command(f"head -10 '{f}'", timeout=5)
                content = stdout.read().decode('utf-8').strip()
                print(f"       Content: {content[:100]}...\n")
    
    ssh.close()
    print("\n[OK] Done!\n")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)
