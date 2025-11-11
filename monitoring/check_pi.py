#!/usr/bin/env python3
"""Quick check of Pi setup"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("116.102.136.220", username="hhaiviet", password="Hoangviet12", allow_agent=False, look_for_keys=False)

# Check Python version
_, stdout, _ = ssh.exec_command("cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python --version")
print("Python version:", stdout.read().decode())

# Check if yaml is installed
_, stdout, _ = ssh.exec_command("cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && pip list | grep -i yaml")
print("PyYAML status:", stdout.read().decode() or "[not installed]")

# Check installed packages
_, stdout, stderr = ssh.exec_command("cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && pip list")
print("\nInstalled packages:")
print(stdout.read().decode()[:500])

# Try to import yaml
_, stdout, stderr = ssh.exec_command("cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python -c 'import yaml; print(yaml.__version__)'")
out = stdout.read().decode()
err = stderr.read().decode()
print("\nYAML import test:")
print("Output:", out or "[empty]")
print("Error:", err or "[no error]")

ssh.close()
