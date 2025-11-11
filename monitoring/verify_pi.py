import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False, timeout=10)
    print('[OK] Connected to Pi')
    
    # Test yaml import
    cmd = "source /home/hhaiviet/kiotviet-integration/venv/bin/activate && python -c 'import yaml; print(\"YAML OK\")'"
    _, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    print(stdout.read(256).decode().strip())
    
    # Show installed
    cmd = "source /home/hhaiviet/kiotviet-integration/venv/bin/activate && pip list | grep -i 'yaml\\|requests\\|pandas'"
    _, stdout, _ = ssh.exec_command(cmd, timeout=15)
    print('\nInstalled:')
    print(stdout.read(256).decode().strip())
    
    print('\n[OK] Setup verified!')
    
except Exception as e:
    print(f'[ERROR] {e}')
    sys.exit(1)
finally:
    ssh.close()
