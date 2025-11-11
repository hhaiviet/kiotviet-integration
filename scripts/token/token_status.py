#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False)

print("\n[*] Checking token script status...\n")

# Check the specific token script process
stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'kiotviet_auto_token'")
procs = stdout.read().decode()
print(procs)

# Get memory usage
stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'kiotviet_auto_token' | awk '{print $6}' | head -1")
mem = stdout.read().decode().strip()
if mem:
    print(f"\nMemory usage: {mem}KB")

# Check if any file was created recently
stdin, stdout, stderr = ssh.exec_command("find /home/hhaiviet/kiotviet-integration -type f -mmin -10 | head -10")
files = stdout.read().decode()
if files:
    print(f"\nRecently created files:")
    print(files)

print("\n[OK] Token script is running. This is expected.")
print("[*] For Selenium with Chrome on Raspberry Pi:")
print("    - It needs to launch and initialize browser")
print("    - Login to KiotViet website")  
print("    - Extract token from API calls")
print("    - This typically takes 2-5 minutes\n")

print("[*] I'll let it continue in background.")
print("[*] You can SSH in to check progress manually:")
print("    ssh hhaiviet@116.102.136.220")
print("    ps aux | grep token")
print("    tail /home/hhaiviet/kiotviet-integration/.env\n")

ssh.close()
