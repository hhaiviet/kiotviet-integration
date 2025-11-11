#!/usr/bin/env python3
"""
Fix dependencies and run token generation
"""

import paramiko
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    return exit_code == 0, output, error

def main():
    print("\n" + "="*70)
    print("Fix Dependencies and Generate Token")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
               timeout=30, allow_agent=False, look_for_keys=False)
    
    print("[*] Step 1: Install/upgrade all requirements...\n")
    
    # Install all requirements
    install_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "Installing requirements from requirements.txt..."
pip install --no-cache-dir -r requirements.txt --upgrade

# Fix blinker issue specifically  
pip install --no-cache-dir --upgrade blinker

echo "[OK] Dependencies installed"
"""
    
    success, out, err = run_cmd(ssh, install_cmd, timeout=300)
    
    # Show last 20 lines of output
    lines = out.split('\n')
    for line in lines[-20:]:
        if line.strip():
            print(line)
    
    time.sleep(2)
    
    print("\n[*] Step 2: Run token generation...\n")
    print("="*70)
    
    token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

# Create directories
mkdir -p data/credentials data/logs

# Set environment
export KIOTVIET_USERNAME=0913431718
export KIOTVIET_PASSWORD=68686868

echo "Running token script..."
python scripts/kiotviet_auto_token_seleniumwire.py 2>&1

# Check result
echo ""
echo "Result:"
if [ -f data/credentials/token.json ]; then
    echo "[OK] Token saved successfully!"
    echo "Content: $(head -c 200 data/credentials/token.json)"
else
    echo "[!] Token not found"
fi
"""
    
    success, out, err = run_cmd(ssh, token_cmd, timeout=300)
    
    print(out)
    
    if err:
        print("\n[Errors]:")
        print(err[:300])
    
    print("\n" + "="*70 + "\n")
    
    ssh.close()

if __name__ == "__main__":
    main()
