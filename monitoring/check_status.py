import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
            allow_agent=False, look_for_keys=False, timeout=10)

# Check output and logs
cmd = """
echo "=== RUNNING PROCESSES ==="
ps aux | grep python | grep -v grep

echo ""
echo "=== OUTPUT FILES ==="
ls -lh /home/hhaiviet/kiotviet-integration/data/output/ 2>/dev/null

echo ""
echo "=== RECENT LOGS ==="
tail -5 /home/hhaiviet/kiotviet-integration/data/logs/*.log 2>/dev/null
"""

_, stdout, _ = ssh.exec_command(cmd, timeout=15)
print(stdout.read(8192).decode())

ssh.close()
