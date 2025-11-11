#!/usr/bin/env python3
import paramiko
import sys

print("Connecting to Pi...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    print("OK Connected")
    
    # Quick test
    cmd = "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python -c 'print(\"Python OK\")'"
    _, stdout, _ = ssh.exec_command(cmd, timeout=10)
    result = stdout.read(100).decode().strip()
    print(f"Result: {result}")
    
    ssh.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
