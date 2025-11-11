#!/usr/bin/env python3
"""
Setup token directories and run token generation on Pi
"""

import paramiko
import sys

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

def run_cmd(ssh, cmd, timeout=60):
    """Run command on Pi."""
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()
        return exit_code == 0, output, error
    except Exception as e:
        return False, "", str(e)

def main():
    print("\n" + "="*70)
    print("Setup and Generate KiotViet Token on Pi")
    print("="*70 + "\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("[*] Connecting to Pi...")
        ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, 
                   timeout=30, allow_agent=False, look_for_keys=False)
        print("[OK] Connected\n")
        
        # Step 1: Create credentials directory
        print("[1] Creating data directories...\n")
        
        dirs_cmd = f"mkdir -p {PI_PROJECT_DIR}/data/credentials {PI_PROJECT_DIR}/data/logs"
        success, out, err = run_cmd(ssh, dirs_cmd)
        
        if success:
            print("[OK] Directories created")
        else:
            print(f"[!] Warning: {err[:100]}")
        
        # Step 2: Setup environment
        print("\n[2] Setting up environment...\n")
        
        env_cmd = f"""
cd {PI_PROJECT_DIR}
cat > setup_env.sh << 'SETUP'
export KIOTVIET_USERNAME=0913431718
export KIOTVIET_PASSWORD=68686868
export KIOTVIET_RETAILER_ID=248minimart
export KIOTVIET_BRANCH_ID=291407
export DISPLAY=:99
export LOG_LEVEL=INFO
SETUP

chmod +x setup_env.sh
echo "[OK] Environment setup done"
"""
        
        success, out, err = run_cmd(ssh, env_cmd)
        if success:
            print(out)
        
        # Step 3: Check Chromium
        print("\n[3] Checking Chromium browser...\n")
        
        chromium_cmd = "which chromium-browser || which chromium || echo 'NOT FOUND'"
        success, out, err = run_cmd(ssh, chromium_cmd)
        
        chromium_path = out.strip() if out.strip() != 'NOT FOUND' else None
        
        if chromium_path:
            print(f"[OK] Chromium found: {chromium_path}")
        else:
            print("[!] Chromium not found - browser launch may fail")
            print("    Token generation needs a browser to login")
        
        # Step 4: Run token generation with output
        print("\n[4] Running token generation...\n")
        print("="*70)
        print("(This may take 2-5 minutes as it launches browser and logs in)\n")
        
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate
source setup_env.sh

echo "Environment check:"
echo "  CWD: $(pwd)"
echo "  Python: $(python --version)"
echo "  KIOTVIET_USERNAME: $KIOTVIET_USERNAME"
echo "  Chromium: ${{CHROMIUM_PATH:=$(which chromium-browser 2>/dev/null || which chromium 2>/dev/null || echo 'NOT FOUND')}}"
echo ""

# Run token script with error handling
python scripts/kiotviet_auto_token_seleniumwire.py 2>&1

# Check if token was created
echo ""
echo "Token file check:"
ls -la data/credentials/token.json 2>/dev/null && echo "[OK] Token saved successfully!" || echo "[!] Token file not found"

# Show token content (first few chars)
if [ -f data/credentials/token.json ]; then
    echo ""
    echo "Token content (first 100 chars):"
    head -c 100 data/credentials/token.json
    echo "..."
fi
"""
        
        success, out, err = run_cmd(ssh, token_cmd, timeout=300)
        
        print(out)
        
        if err and len(err) > 50:
            print("\n[Errors/Warnings]:")
            print(err[:300])
        
        print("\n" + "="*70)
        
        # Step 5: Final verification
        print("\n[5] Verifying token...\n")
        
        verify_cmd = f"[ -f {PI_PROJECT_DIR}/data/credentials/token.json ] && echo '[OK] Token exists' || echo '[!] Token not found'"
        success, out, err = run_cmd(ssh, verify_cmd)
        
        print(out)
        
        if success and 'exists' in out:
            print("\n[OK] TOKEN GENERATION SUCCESSFUL!")
            print("[*] Next steps:")
            print("    - SSH into Pi: ssh hhaiviet@116.102.136.220")
            print("    - Test script: python scripts/kiotviet_run_all.py")
            print("    - Check logs: tail -f data/logs/kiotviet.log")
        else:
            print("\n[!] Token generation incomplete or failed")
            print("[*] Possible issues:")
            print("    - Chromium not installed on Raspberry Pi")
            print("    - Browser display issue (DISPLAY not set)")
            print("    - Network connectivity to KiotViet website")
            print("    - Username/password incorrect")
            print("\n[*] To debug, SSH into Pi and run:")
            print(f"    cd {PI_PROJECT_DIR}")
            print("    source venv/bin/activate")
            print("    export KIOTVIET_USERNAME=0913431718")
            print("    export KIOTVIET_PASSWORD=68686868")
            print("    python scripts/kiotviet_auto_token_seleniumwire.py")
        
        print("\n" + "="*70 + "\n")
        
        ssh.close()
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
