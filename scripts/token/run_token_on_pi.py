#!/usr/bin/env python3
"""
SSH vào Raspberry Pi và chạy script lấy token
"""

import paramiko
import sys
import time

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

def log(msg: str, level: str = "INFO"):
    """Log with color."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    
    levels = {
        "SUCCESS": (Colors.GREEN, "[✓]"),
        "ERROR": (Colors.RED, "[✗]"),
        "WARNING": (Colors.YELLOW, "[!]"),
        "INFO": (Colors.BLUE, "[•]"),
        "STEP": (Colors.PURPLE, "[>>>]"),
    }
    
    color, prefix = levels.get(level, (Colors.BLUE, "[?]"))
    print(f"{color}[{ts}] {prefix}{Colors.NC} {msg}")

class SSHClient:
    """SSH client wrapper."""
    
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.client = None
    
    def connect(self) -> bool:
        """Connect to SSH server."""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            log(f"Kết nối tới {self.user}@{self.host}...", "INFO")
            
            self.client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            log("Kết nối SSH thành công", "SUCCESS")
            return True
        except Exception as e:
            log(f"Kết nối SSH thất bại: {e}", "ERROR")
            return False
    
    def execute_interactive(self, cmd: str, timeout: int = 300) -> bool:
        """Execute command with real-time output."""
        try:
            transport = self.client.get_transport()
            channel = transport.open_session()
            channel.set_combine_stderr(True)
            channel.exec_command(cmd)
            
            # Read output in real-time
            while True:
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8', errors='ignore')
                    if data:
                        print(data, end='', flush=True)
                
                if channel.recv_exit_status() >= 0:
                    break
                
                time.sleep(0.1)
            
            return True
        except Exception as e:
            log(f"Execute error: {e}", "ERROR")
            return False
    
    def execute(self, cmd: str, timeout: int = 60) -> tuple:
        """Execute command and return output."""
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            
            exit_code = stdout.channel.recv_exit_status()
            return exit_code == 0, out, err
        except Exception as e:
            return False, "", str(e)
    
    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()

def main():
    """Main entry point."""
    print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
    print(f"{Colors.PURPLE}Lấy Token KiotViet trên Raspberry Pi{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
    
    # Connect
    ssh = SSHClient(PI_IP, PI_USER, PI_PASSWORD)
    if not ssh.connect():
        return 1
    
    try:
        # Step 1: Kiểm tra files
        log("Kiểm tra files trên Pi...", "STEP")
        success, out, err = ssh.execute(f"ls -la {PI_PROJECT_DIR}/scripts/kiotviet_auto_token*.py")
        
        if success:
            log("Tìm thấy token scripts:", "SUCCESS")
            for line in out.strip().split('\n'):
                if line.strip():
                    log(f"  {line}", "INFO")
        else:
            log("Không tìm thấy token scripts", "ERROR")
            return 1
        
        time.sleep(1)
        
        # Step 2: Activate venv và chạy token script
        log("\nKích hoạt environment...", "STEP")
        
        # Build command
        token_cmd = f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate

echo "=== Environment Information ==="
echo "Python: $(python --version)"
echo "Current dir: $(pwd)"
echo "Project files:"
ls -la scripts/kiotviet_auto_token*.py
echo ""

echo "=== Running Token Generation ==="
python scripts/kiotviet_auto_token_enhanced.py
"""
        
        log("Chạy script lấy token...", "INFO")
        log("\n" + "="*70 + "\n", "INFO")
        
        # Execute with real-time output
        success = ssh.execute_interactive(token_cmd, timeout=300)
        
        log("\n" + "="*70, "INFO")
        
        if success:
            log("Token generation completed", "SUCCESS")
        else:
            log("Token generation may have encountered issues", "WARNING")
        
        return 0
    
    finally:
        log("\nĐóng kết nối SSH", "INFO")
        ssh.close()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Bị gián đoạn bởi người dùng{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Lỗi: {e}{Colors.NC}")
        sys.exit(1)
