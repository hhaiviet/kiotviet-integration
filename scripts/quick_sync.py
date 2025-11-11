#!/usr/bin/env python3
import paramiko, sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    
    # Upload file
    sftp = ssh.open_sftp()
    sftp.put(r"pi_auto_sync.py", "/home/hhaiviet/kiotviet-integration/pi_auto_sync.py")
    sftp.close()
    print("Uploaded")
    
    # Run it
    cmd = "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python pi_auto_sync.py"
    _, stdout, _ = ssh.exec_command(cmd, timeout=600)
    
    for line in stdout:
        print(line.rstrip())
    
    ssh.close()
    print("Done")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
