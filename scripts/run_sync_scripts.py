#!/usr/bin/env python3
"""
Run sync scripts on Pi using existing token
"""

import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    
    print("\n" + "="*70)
    print("RUNNING ALL SYNC SCRIPTS ON PI")
    print("="*70 + "\n")
    
    # Run all scripts
    cmd = """
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate

echo "[1] Product Export..."
python scripts/kiotviet_product_exporter.py

echo ""
echo "[2] Invoice Details..."
python scripts/kiotviet_invoice_details.py

echo ""
echo "[3] Full Sync..."
python scripts/kiotviet_run_all.py

echo ""
echo "[OK] All scripts completed!"
echo ""
echo "Output files:"
ls -lh data/output/
"""
    
    _, stdout, stderr = ssh.exec_command(cmd, timeout=600)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    # Check errors
    err = stderr.read(4096).decode()
    if err:
        print(f"\n[ERRORS]:\n{err[:1000]}")
    
    exit_code = stdout.channel.recv_exit_status()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("[OK] ALL SCRIPTS COMPLETED!")
    else:
        print(f"[!] Exit code: {exit_code}")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n[ERROR] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    ssh.close()
