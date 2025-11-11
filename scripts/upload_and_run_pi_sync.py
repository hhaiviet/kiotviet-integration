#!/usr/bin/env python3
"""Upload and run auto sync script on Pi"""

import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
            allow_agent=False, look_for_keys=False, timeout=10)

print("Uploading pi_auto_sync.py to Pi...\n")

# Upload script via SFTP
sftp = ssh.open_sftp()

local_file = r"c:\Users\PeterHoang\OneDrive - Li & Fung\Documents\kiotviet 248minimart project\kiotviet-integration\pi_auto_sync.py"
remote_file = "/home/hhaiviet/kiotviet-integration/pi_auto_sync.py"

sftp.put(local_file, remote_file)
print(f"Uploaded to {remote_file}")

# Make it executable
ssh.exec_command(f"chmod +x {remote_file}")

sftp.close()

# Now run it
print("\n" + "="*70)
print("Running auto sync on Pi...")
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
if err:
    print(f"\n[ERRORS]:\n{err[:1000]}")

exit_code = stdout.channel.recv_exit_status()

print("\n" + "="*70)
if exit_code == 0:
    print("[OK] COMPLETED!")
else:
    print(f"[!] Exit code: {exit_code}")
print("="*70 + "\n")

ssh.close()
