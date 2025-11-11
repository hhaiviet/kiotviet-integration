#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False)

print("\n[*] Detailed process check on Pi:\n")

# Check all Python processes
stdin, stdout, stderr = ssh.exec_command("ps aux | grep python")
print("Python processes:")
print(stdout.read().decode()[:300])

print("\n[*] Checking browser processes:\n")

# Check for Chromium
stdin, stdout, stderr = ssh.exec_command("pgrep -a chromium")
print("Chromium:")
print(stdout.read().decode()[:200] or "Not running")

# Check logs if any
stdin, stdout, stderr = ssh.exec_command("tail -20 /home/hhaiviet/kiotviet-integration/scripts/*.log 2>/dev/null")
logs = stdout.read().decode().strip()
if logs:
    print("\n[*] Script logs:")
    print(logs[:300])

ssh.close()
print("\n[*] Token generation is running. It may take 2-5 minutes.")
print("[*] Selenium is launching browser and logging into KiotViet...")
print("[*] Please wait...\n")
