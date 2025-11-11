#!/usr/bin/env python3
"""Run pi_auto_sync.py on Raspberry Pi"""

import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print("Connecting to Pi at 116.102.136.220...")
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    print("OK Connected\n")
    
    # Upload script
    print("Uploading pi_auto_sync.py...")
    sftp = ssh.open_sftp()
    sftp.put(r"pi_auto_sync.py", "/home/hhaiviet/kiotviet-integration/pi_auto_sync.py")
    sftp.close()
    print("OK Uploaded\n")
    
    # Run script
    print("="*70)
    print("RUNNING AUTO SYNC ON PI")
    print("="*70 + "\n")
    
    cmd = """
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python pi_auto_sync.py
"""
    
    _, stdout, stderr = ssh.exec_command(cmd, timeout=600)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    # Check for errors
    err = stderr.read(4096).decode()
    if err and err.strip():
        print(f"\n[STDERR]:\n{err[:1000]}")
    
    exit_code = stdout.channel.recv_exit_status()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("[OK] SYNC COMPLETED SUCCESSFULLY!")
    else:
        print(f"[!] Exit code: {exit_code}")
    print("="*70 + "\n")
    
    # Check output files
    print("Checking output files on Pi...\n")
    cmd = "ls -lh /home/hhaiviet/kiotviet-integration/data/output/ 2>/dev/null | tail -10"
    _, stdout, _ = ssh.exec_command(cmd, timeout=10)
    print(stdout.read(4096).decode())
    
    ssh.close()
    sys.exit(exit_code)
    
except Exception as e:
    print(f"[ERROR] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
