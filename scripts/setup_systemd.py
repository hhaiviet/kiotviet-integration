#!/usr/bin/env python3
"""Create systemd service for auto sync on Pi"""

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
            allow_agent=False, look_for_keys=False, timeout=10)

print("Creating systemd service for auto sync...\n")

# Create service file
service_content = """[Unit]
Description=KiotViet Auto Sync Service
After=network.target

[Service]
Type=simple
User=hhaiviet
WorkingDirectory=/home/hhaiviet/kiotviet-integration
Environment="PATH=/home/hhaiviet/kiotviet-integration/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/hhaiviet/kiotviet-integration/venv/bin/python pi_auto_sync.py
Restart=always
RestartSec=300
StandardOutput=append:/home/hhaiviet/kiotviet-integration/data/logs/auto-sync.log
StandardError=append:/home/hhaiviet/kiotviet-integration/data/logs/auto-sync-error.log

[Install]
WantedBy=multi-user.target
"""

# Write service file via SSH
cmd = f'''cat > /tmp/kiotviet-auto-sync.service << 'EOF'
{service_content}
EOF
'''

ssh.exec_command(cmd)

# Copy to systemd directory
cmd = "sudo cp /tmp/kiotviet-auto-sync.service /etc/systemd/system/"
_, stdout, stderr = ssh.exec_command(cmd, timeout=10)
err = stderr.read().decode()
if "Permission denied" in err:
    print("[!] Sudo access needed. Create manually with:")
    print("    sudo cp /tmp/kiotviet-auto-sync.service /etc/systemd/system/")
else:
    print("[OK] Service file created at /etc/systemd/system/kiotviet-auto-sync.service")

# Check if file exists
cmd = "ls -la /etc/systemd/system/kiotviet-auto-sync.service 2>/dev/null || echo 'File not found'"
_, stdout, _ = ssh.exec_command(cmd, timeout=10)
print(stdout.read().decode())

ssh.close()

print("\nTo enable the service:")
print("  sudo systemctl daemon-reload")
print("  sudo systemctl enable kiotviet-auto-sync.service")
print("  sudo systemctl start kiotviet-auto-sync.service")
print("  sudo systemctl status kiotviet-auto-sync.service")
