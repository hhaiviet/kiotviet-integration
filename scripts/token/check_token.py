#!/usr/bin/env python3
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False)

print("\n[*] Token script status:\n")

stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python.*token' | wc -l")
count = stdout.read().decode().strip()
print(f"Running processes: {count}")

if int(count) > 0:
    print("[!] Token script still running...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -i token | grep -v grep")
    print(stdout.read().decode()[:200])
else:
    print("[OK] Token script completed!\n")
    
    # Check for output
    stdin, stdout, stderr = ssh.exec_command("ls -lh /home/hhaiviet/kiotviet-integration/*.json /home/hhaiviet/kiotviet-integration/token* 2>/dev/null | head -5")
    files = stdout.read().decode().strip()
    if files:
        print("Output files:")
        print(files)
    
    # Check .env
    stdin, stdout, stderr = ssh.exec_command("grep -i token /home/hhaiviet/kiotviet-integration/.env | head -3")
    print("\n.env content:")
    print(stdout.read().decode()[:200])

ssh.close()
print("\n[OK] Done!\n")
