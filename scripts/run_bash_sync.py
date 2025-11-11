#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
            allow_agent=False, look_for_keys=False, timeout=10)

print("Uploading auto_sync.sh...\n")

# Upload
sftp = ssh.open_sftp()
sftp.put(r"auto_sync.sh", "/home/hhaiviet/kiotviet-integration/auto_sync.sh")
sftp.close()

# Make executable
ssh.exec_command("chmod +x /home/hhaiviet/kiotviet-integration/auto_sync.sh")

# Run it
print("="*70)
print("Running auto sync on Pi\n")

cmd = "cd /home/hhaiviet/kiotviet-integration && bash auto_sync.sh"
_, stdout, _ = ssh.exec_command(cmd, timeout=600)

for line in stdout:
    print(line.rstrip())

ssh.close()
print("\nDone!")
