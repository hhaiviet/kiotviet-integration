import paramiko
import sys
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    
    print("\n" + "="*70)
    print("RUNNING ALL KIOTVIET SYNC SCRIPTS")
    print("="*70 + "\n")
    
    # List of scripts to run
    scripts = [
        ('Product Export', 'scripts/kiotviet_product_exporter.py'),
        ('Invoice Details', 'scripts/kiotviet_invoice_details.py'),
        ('Full Sync', 'scripts/kiotviet_run_all.py'),
    ]
    
    base_cmd = """
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
"""
    
    for script_name, script_path in scripts:
        print(f"\n[{'='*65}]")
        print(f"[RUNNING] {script_name}: {script_path}")
        print(f"[{'='*65}]\n")
        
        # Run with timeout
        cmd = f"{base_cmd}python {script_path}"
        
        _, stdout, stderr = ssh.exec_command(cmd, timeout=300)
        
        # Read and stream output
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line.rstrip())
        
        # Check for errors
        err = stderr.read(4096).decode()
        exit_code = stdout.channel.recv_exit_status()
        
        if exit_code == 0:
            print(f"\n[OK] {script_name} completed successfully")
        else:
            print(f"\n[!] {script_name} exit code: {exit_code}")
            if err:
                print(f"[Errors]:\n{err[:500]}")
        
        time.sleep(1)
    
    print("\n" + "="*70)
    print("ALL SCRIPTS COMPLETED")
    print("="*70 + "\n")
    
    # Check output files
    print("[CHECKING OUTPUT FILES]\n")
    
    check_cmd = """
cd /home/hhaiviet/kiotviet-integration
ls -lh data/output/ 2>/dev/null || echo 'No output files yet'
echo ""
ls -lh data/logs/ 2>/dev/null | head -10 || echo 'No log files yet'
"""
    
    _, stdout, _ = ssh.exec_command(check_cmd, timeout=10)
    print(stdout.read(2048).decode())
    
except Exception as e:
    print(f"\n[ERROR] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    ssh.close()

print("\n[OK] Done!")
