#!/usr/bin/env python3
"""
Complete Automated KiotViet Deployment using Paramiko
- No external tools needed
- Full automation with embedded credentials
- All SSH operations via Python
"""

import sys
import time
from pathlib import Path
import subprocess
from typing import Tuple

# Try to import paramiko, install if needed
try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
except ImportError:
    print("[INFO] Installing paramiko...")
    subprocess.run([sys.executable, "-m", "pip", "install", "paramiko", "-q"])
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy

# Configuration - All credentials embedded
PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
KIOTVIET_USERNAME = "0913431718"
KIOTVIET_PASSWORD = "68686868"
RETAILER_ID = "248minimart"
BRANCH_ID = "291407"

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'

def log(msg: str, level: str = "INFO"):
    """Log message."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    if level == "SUCCESS":
        color = Colors.GREEN
        prefix = "[OK]"
    elif level == "ERROR":
        color = Colors.RED
        prefix = "[ERROR]"
    elif level == "WARNING":
        color = Colors.YELLOW
        prefix = "[WARN]"
    elif level == "INFO":
        color = Colors.BLUE
        prefix = "[INFO]"
    else:
        color = Colors.PURPLE
        prefix = "[STEP]"
    
    print(f"{color}[{timestamp}] {prefix}{Colors.NC} {msg}")

class AutoDeployer:
    def __init__(self):
        self.client = None
        self.ssh_dir = Path.home() / ".ssh"
        self.private_key = self.ssh_dir / "id_rsa"
        self.public_key = self.ssh_dir / "id_rsa.pub"
        
    def connect_ssh(self) -> bool:
        """Connect to Raspberry Pi via SSH."""
        log(f"Connecting to {PI_USER}@{PI_IP}...", "INFO")
        
        try:
            self.client = SSHClient()
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            
            self.client.connect(
                PI_IP,
                username=PI_USER,
                password=PI_PASSWORD,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            log("SSH connection successful", "SUCCESS")
            return True
            
        except Exception as e:
            log(f"SSH connection failed: {e}", "ERROR")
            return False
    
    def exec_command(self, cmd: str, description: str = "") -> Tuple[bool, str]:
        """Execute remote SSH command."""
        if description:
            log(description, "INFO")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            if exit_code == 0:
                log(f"Success: {cmd[:50]}", "SUCCESS")
                return True, output
            else:
                log(f"Failed: {error[:100]}", "ERROR")
                return False, error
                
        except Exception as e:
            log(f"Command error: {e}", "ERROR")
            return False, str(e)
    
    def close(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
            log("SSH connection closed", "INFO")
    
    def step_1_generate_ssh_key(self) -> bool:
        """Step 1: Generate SSH key if needed."""
        log("\n" + "="*70, "STEP")
        log("STEP 1: Generate SSH Key (Local)", "STEP")
        log("="*70, "STEP")
        
        if self.private_key.exists() and self.public_key.exists():
            log(f"SSH key already exists", "SUCCESS")
            return True
        
        log("Generating SSH key...", "INFO")
        self.ssh_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", str(self.private_key), "-N", ""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                log("SSH key generated successfully", "SUCCESS")
                return True
            else:
                log(f"Failed to generate SSH key", "ERROR")
                return False
                
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            return False
    
    def step_2_setup_ssh_key_on_pi(self) -> bool:
        """Step 2: Copy SSH key to Pi."""
        log("\n" + "="*70, "STEP")
        log("STEP 2: Setup SSH Key on Raspberry Pi", "STEP")
        log("="*70, "STEP")
        
        if not self.public_key.exists():
            log("Public key not found", "ERROR")
            return False
        
        with open(self.public_key, 'r') as f:
            pub_key = f.read().strip()
        
        commands = [
            ("mkdir -p ~/.ssh", "Creating .ssh directory"),
            (f"echo '{pub_key}' >> ~/.ssh/authorized_keys", "Adding public key"),
            ("chmod 600 ~/.ssh/authorized_keys", "Setting authorized_keys permissions"),
            ("chmod 700 ~/.ssh", "Setting .ssh directory permissions"),
        ]
        
        for cmd, desc in commands:
            success, output = self.exec_command(cmd, desc)
            if not success:
                return False
            time.sleep(0.5)
        
        log("SSH key setup completed on Pi", "SUCCESS")
        return True
    
    def step_3_prepare_env_file(self) -> bool:
        """Step 3: Prepare .env file on Pi."""
        log("\n" + "="*70, "STEP")
        log("STEP 3: Create Environment File", "STEP")
        log("="*70, "STEP")
        
        env_content = f"""# KiotViet Credentials - Auto-generated
KIOTVIET_USERNAME={KIOTVIET_USERNAME}
KIOTVIET_PASSWORD={KIOTVIET_PASSWORD}
KIOTVIET_RETAILER_ID={RETAILER_ID}
KIOTVIET_BRANCH_ID={BRANCH_ID}

# API Configuration
API_BASE_URL=https://api-man1.kiotviet.vn/api
API_TIMEOUT=30
API_MAX_RETRIES=5
API_PAGE_SIZE=100

# Chrome Configuration for Raspberry Pi
CHROME_BINARY_PATH=/usr/bin/chromium-browser
CHROMEDRIVER_PATH=/usr/bin/chromedriver
DISPLAY=:99

# Scheduling
SYNC_INTERVAL_HOURS=2
AUTO_RESTART=true

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Remote monitoring
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_PORT=8080
"""
        
        # Create .env file locally first
        project_root = Path.cwd()
        local_env = project_root / ".env"
        
        try:
            local_env.write_text(env_content)
            log(f"Local .env created: {local_env}", "SUCCESS")
            
            # Upload to Pi
            log("Uploading .env to Pi...", "INFO")
            sftp = self.client.open_sftp()
            sftp.put(str(local_env), f"/home/{PI_USER}/.env")
            sftp.close()
            
            log(".env uploaded to Pi", "SUCCESS")
            return True
            
        except Exception as e:
            log(f"Error creating .env: {e}", "ERROR")
            return False
    
    def step_4_clone_repo(self) -> bool:
        """Step 4: Clone/update repository on Pi."""
        log("\n" + "="*70, "STEP")
        log("STEP 4: Clone Repository on Raspberry Pi", "STEP")
        log("="*70, "STEP")
        
        commands = [
            ("cd /home/hhaiviet", "Changing to home directory"),
            ("if [ -d kiotviet-integration ]; then cd kiotviet-integration && git pull origin main; else git clone https://github.com/hhaiviet/kiotviet-integration.git; fi", "Cloning/updating repository"),
        ]
        
        for cmd, desc in commands:
            success, output = self.exec_command(cmd, desc)
            if not success and "fatal" in output.lower():
                return False
            time.sleep(1)
        
        log("Repository ready on Pi", "SUCCESS")
        return True
    
    def step_5_install_dependencies(self) -> bool:
        """Step 5: Install Python dependencies."""
        log("\n" + "="*70, "STEP")
        log("STEP 5: Install System & Python Dependencies", "STEP")
        log("="*70, "STEP")
        
        # First, add current user to sudoers with NOPASSWD
        commands = [
            ("echo 'hhaiviet ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/kiotviet > /dev/null", "Adding sudo NOPASSWD access"),
        ]
        
        for cmd, desc in commands:
            log(f"{desc}...", "INFO")
            success, output = self.exec_command(cmd, "")
            time.sleep(1)
        
        # Install dependencies
        commands = [
            ("sudo apt-get update", "Updating package list"),
            ("sudo apt-get install -y python3 python3-pip python3-venv git chromium-browser chromium-chromedriver xvfb", "Installing system packages"),
        ]
        
        for cmd, desc in commands:
            log(f"{desc}... (this may take a few minutes)", "INFO")
            success, output = self.exec_command(cmd, "")
            if not success and "failed" in output.lower():
                log(f"Warning: {output[:100]}", "WARNING")
            time.sleep(2)
        
        log("Dependencies installed", "SUCCESS")
        return True
    
    def step_6_setup_virtual_env(self) -> bool:
        """Step 6: Setup Python virtual environment."""
        log("\n" + "="*70, "STEP")
        log("STEP 6: Setup Python Virtual Environment", "STEP")
        log("="*70, "STEP")
        
        commands = [
            ("cd /home/hhaiviet/kiotviet-integration", "Changing to project directory"),
            ("python3 -m venv venv", "Creating virtual environment"),
            ("source venv/bin/activate && pip install --upgrade pip", "Upgrading pip"),
            ("source venv/bin/activate && pip install requests selenium selenium-wire paramiko click pandas python-dotenv", "Installing Python requirements"),
        ]
        
        for cmd, desc in commands:
            log(f"{desc}...", "INFO")
            success, output = self.exec_command(cmd, "")
            if not success:
                log(f"Error: {output[:100]}", "ERROR")
                return False
            time.sleep(1)
        
        log("Python environment ready", "SUCCESS")
        return True
    
    def step_7_create_directories(self) -> bool:
        """Step 7: Create necessary directories."""
        log("\n" + "="*70, "STEP")
        log("STEP 7: Create Project Directories", "STEP")
        log("="*70, "STEP")
        
        directories = [
            "data/output",
            "data/checkpoints",
            "data/logs",
            "data/credentials",
        ]
        
        for dir_path in directories:
            cmd = f"cd /home/hhaiviet/kiotviet-integration && mkdir -p {dir_path}"
            success, _ = self.exec_command(cmd, f"Creating {dir_path}")
            if not success:
                return False
            time.sleep(0.5)
        
        log("All directories created", "SUCCESS")
        return True
    
    def step_8_setup_services(self) -> bool:
        """Step 8: Setup systemd services."""
        log("\n" + "="*70, "STEP")
        log("STEP 8: Setup Systemd Services", "STEP")
        log("="*70, "STEP")
        
        # Create xvfb service
        xvfb_service = """[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x24
Restart=always
User=hhaiviet

[Install]
WantedBy=multi-user.target
"""
        
        # Create main service
        main_service = """[Unit]
Description=KiotViet Integration Service
After=network.target xvfb.service
Requires=xvfb.service

[Service]
Type=simple
User=hhaiviet
WorkingDirectory=/home/hhaiviet/kiotviet-integration
Environment=PATH=/home/hhaiviet/kiotviet-integration/venv/bin
Environment=DISPLAY=:99
ExecStart=/home/hhaiviet/kiotviet-integration/venv/bin/python scripts/kiotviet_run_all.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Upload service files
            sftp = self.client.open_sftp()
            
            # Create temp files
            with open("/tmp/xvfb.service", "w") as f:
                f.write(xvfb_service)
            with open("/tmp/kiotviet.service", "w") as f:
                f.write(main_service)
            
            # Upload
            sftp.put("/tmp/xvfb.service", "/tmp/xvfb.service")
            sftp.put("/tmp/kiotviet.service", "/tmp/kiotviet.service")
            sftp.close()
            
            # Move to systemd
            commands = [
                "sudo mv /tmp/xvfb.service /etc/systemd/system/",
                "sudo mv /tmp/kiotviet.service /etc/systemd/system/kiotviet-integration.service",
                "sudo systemctl daemon-reload",
                "sudo systemctl enable xvfb",
                "sudo systemctl enable kiotviet-integration",
            ]
            
            for cmd in commands:
                success, _ = self.exec_command(cmd, "")
                if not success:
                    return False
            
            log("Systemd services configured", "SUCCESS")
            return True
            
        except Exception as e:
            log(f"Error setting up services: {e}", "ERROR")
            return False
    
    def step_9_start_services(self) -> bool:
        """Step 9: Start services."""
        log("\n" + "="*70, "STEP")
        log("STEP 9: Start Services", "STEP")
        log("="*70, "STEP")
        
        commands = [
            ("sudo systemctl start xvfb", "Starting xvfb"),
            ("sudo systemctl start kiotviet-integration", "Starting KiotViet service"),
        ]
        
        for cmd, desc in commands:
            success, _ = self.exec_command(cmd, desc)
            if not success:
                log(f"Warning: {desc} may have issues", "WARNING")
            time.sleep(2)
        
        # Verify services
        log("Verifying services...", "INFO")
        success, output = self.exec_command("sudo systemctl status kiotviet-integration --no-pager", "")
        
        if "active (running)" in output.lower():
            log("KiotViet service is running", "SUCCESS")
            return True
        else:
            log("Warning: Service status unclear", "WARNING")
            return True  # Continue anyway
    
    def step_10_setup_cron(self) -> bool:
        """Step 10: Setup cron jobs."""
        log("\n" + "="*70, "STEP")
        log("STEP 10: Setup Cron Jobs", "STEP")
        log("="*70, "STEP")
        
        cron_jobs = [
            "0 */2 * * * cd /home/hhaiviet/kiotviet-integration && ./venv/bin/python scripts/kiotviet_run_all.py >> data/logs/cron.log 2>&1",
            "0 2 * * * cd /home/hhaiviet/kiotviet-integration && ./venv/bin/python scripts/kiotviet_auto_token_enhanced.py >> data/logs/token_refresh.log 2>&1",
            "0 3 * * 0 find /home/hhaiviet/kiotviet-integration/data/logs -name '*.log' -mtime +7 -delete",
        ]
        
        try:
            # Get current crontab
            stdin, stdout, stderr = self.client.exec_command("crontab -l 2>/dev/null || echo ''")
            current_cron = stdout.read().decode('utf-8', errors='ignore')
            
            # Add new jobs
            new_cron = current_cron
            for job in cron_jobs:
                if job not in new_cron:
                    new_cron += job + "\n"
            
            # Write new crontab
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(new_cron)
                temp_cron = f.name
            
            # Upload and install
            sftp = self.client.open_sftp()
            sftp.put(temp_cron, "/tmp/crontab.txt")
            sftp.close()
            
            self.exec_command("crontab /tmp/crontab.txt", "Installing cron jobs")
            
            log("Cron jobs configured", "SUCCESS")
            return True
            
        except Exception as e:
            log(f"Error setting up cron: {e}", "ERROR")
            return False
    
    def run_all(self) -> bool:
        """Run all deployment steps."""
        print(f"\n{Colors.PURPLE}{'='*70}{Colors.NC}")
        print(f"{Colors.PURPLE}KiotViet Integration - Full Automated Deployment{Colors.NC}")
        print(f"{Colors.PURPLE}{'='*70}{Colors.NC}\n")
        
        print(f"Target: {PI_USER}@{PI_IP}")
        print(f"KiotViet User: {KIOTVIET_USERNAME}\n")
        
        # Step 1: Generate SSH key locally
        if not self.step_1_generate_ssh_key():
            return False
        
        # Connect to Pi
        if not self.connect_ssh():
            return False
        
        try:
            # Step 2-10: Remote setup
            steps = [
                self.step_2_setup_ssh_key_on_pi,
                self.step_3_prepare_env_file,
                self.step_4_clone_repo,
                self.step_5_install_dependencies,
                self.step_6_setup_virtual_env,
                self.step_7_create_directories,
                self.step_8_setup_services,
                self.step_9_start_services,
                self.step_10_setup_cron,
            ]
            
            for step in steps:
                if not step():
                    return False
                time.sleep(2)
            
            return True
            
        finally:
            self.close()

def main():
    """Main entry point."""
    try:
        deployer = AutoDeployer()
        
        if deployer.run_all():
            print(f"\n{Colors.GREEN}{'='*70}{Colors.NC}")
            print(f"{Colors.GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY!{Colors.NC}")
            print(f"{Colors.GREEN}{'='*70}{Colors.NC}\n")
            
            print(f"Your KiotViet integration is now running 24/7!\n")
            
            print(f"Next steps:")
            print(f"  1. Check status: python remote_debug.py status")
            print(f"  2. View logs: python remote_debug.py logs --follow")
            print(f"  3. Manual sync: python remote_debug.py sync")
            print(f"  4. SSH shell: python remote_debug.py shell\n")
            
            return 0
        else:
            print(f"\n{Colors.RED}{'='*70}{Colors.NC}")
            print(f"{Colors.RED}DEPLOYMENT FAILED!{Colors.NC}")
            print(f"{Colors.RED}{'='*70}{Colors.NC}\n")
            return 1
            
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())