#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False)

print("[*] Quick status check:\n")

# Check token file
stdin, stdout, stderr = ssh.exec_command("ls -la /home/hhaiviet/kiotviet-integration/data/credentials/token.json")
result = stdout.read().decode()
print(f"Token file status:\n{result}\n")

# Check for running python processes
stdin, stdout, stderr = ssh.exec_command("pgrep python3 | wc -l")
count = stdout.read().decode().strip()
print(f"Running Python processes: {count}\n")

# Check logs
stdin, stdout, stderr = ssh.exec_command("tail -10 /home/hhaiviet/kiotviet-integration/data/logs/kiotviet.log")
logs = stdout.read().decode()
if logs:
    print(f"Recent logs:\n{logs}\n")

ssh.close()
