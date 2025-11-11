import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
            allow_agent=False, look_for_keys=False, timeout=10)

# Check if processes are running and output files
cmd = """
echo "=== PROCESSES ==="
ps aux | grep python | grep -v grep || echo "No python processes"

echo ""
echo "=== OUTPUT FILES ==="
ls -lh /home/hhaiviet/kiotviet-integration/data/output/ 2>/dev/null

echo ""
echo "=== LOG FILES (last 5) ==="
ls -lt /home/hhaiviet/kiotviet-integration/data/logs/ 2>/dev/null | head -6

echo ""
echo "=== RECENT LOG CONTENT ==="
tail -20 /home/hhaiviet/kiotviet-integration/data/logs/*.log 2>/dev/null | head -50
"""

_, stdout, _ = ssh.exec_command(cmd, timeout=15)
output = stdout.read(8192).decode()
print(output)

ssh.close()
