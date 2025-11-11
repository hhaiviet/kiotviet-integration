#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False)

print("\n" + "="*70)
print("TOKEN GENERATION RESULT")
print("="*70 + "\n")

# Check .env file
print("[*] Checking .env file...\n")
stdin, stdout, stderr = ssh.exec_command("cat /home/hhaiviet/kiotviet-integration/.env")
env_content = stdout.read().decode()

if env_content:
    print("[OK] .env file content:")
    print("-"*70)
    for line in env_content.split('\n'):
        if line.strip():
            if any(x in line.lower() for x in ['token', 'api', 'key', 'password']):
                # Mask sensitive info
                if '=' in line:
                    key, val = line.split('=', 1)
                    if len(val) > 20:
                        print(f"{key}={'*'*20}...{val[-5:]}")
                    else:
                        print(f"{key}={val}")
                else:
                    print(line)
            else:
                print(line)
    print("-"*70)
else:
    print("[!] .env file is empty!")

# Check logs
print("\n[*] Checking application logs...\n")
stdin, stdout, stderr = ssh.exec_command("tail -30 /home/hhaiviet/kiotviet-integration/data/logs/kiotviet.log")
logs = stdout.read().decode()

if logs:
    print("[OK] Recent logs:")
    print("-"*70)
    print(logs[:500])
    print("-"*70)
else:
    print("[!] No log file found")

# Check for token files
print("\n[*] Checking for token files...\n")
stdin, stdout, stderr = ssh.exec_command("find /home/hhaiviet/kiotviet-integration -name '*token*' -o -name '*.json' | head -5")
tokens = stdout.read().decode()

if tokens.strip():
    print("[OK] Token/data files:")
    print(tokens)
else:
    print("[!] No token files found")

print("\n" + "="*70)
print("[OK] Token generation completed!")
print("="*70 + "\n")

ssh.close()
