#!/usr/bin/env python3
"""
Automated SSH Key Setup for Raspberry Pi using Paramiko
No external tools needed - pure Python SSH
"""

import subprocess
import sys
from pathlib import Path
import getpass
import time

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log(msg: str, color: str = Colors.BLUE):
    print(f"{color}[SSH]{Colors.NC} {msg}")

def success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

class AutoSSHSetup:
    def __init__(self):
        self.pi_ip = "116.102.136.220"
        self.pi_user = "hhaiviet"
        self.ssh_dir = Path.home() / ".ssh"
        self.private_key = self.ssh_dir / "id_rsa"
        self.public_key = self.ssh_dir / "id_rsa.pub"
        
    def read_public_key(self) -> str:
        """Read public key content."""
        if not self.public_key.exists():
            error(f"Public key not found at {self.public_key}")
            sys.exit(1)
        
        with open(self.public_key, 'r') as f:
            return f.read().strip()
    
    def copy_key_via_ssh(self, password: str) -> bool:
        """Copy public key using SSH commands."""
        log(f"Copying SSH key to {self.pi_user}@{self.pi_ip}...")
        
        pub_key = self.read_public_key()
        
        # Create commands to run on remote
        commands = [
            "mkdir -p ~/.ssh",
            f"echo '{pub_key}' >> ~/.ssh/authorized_keys",
            "chmod 600 ~/.ssh/authorized_keys",
            "chmod 700 ~/.ssh"
        ]
        
        for cmd in commands:
            try:
                # Build SSH command with password via stdin
                ssh_cmd = f'ssh -o StrictHostKeyChecking=no {self.pi_user}@{self.pi_ip} "{cmd}"'
                
                # Use echo to pipe password to ssh
                full_cmd = f'echo {password} | ssh -o StrictHostKeyChecking=no -o StrictHostKeyChecking=no {self.pi_user}@{self.pi_ip} "{cmd}"'
                
                log(f"Executing: {cmd}")
                
                # Try using subprocess with password via stdin
                proc = subprocess.Popen(
                    ['ssh', '-o', 'StrictHostKeyChecking=no', f'{self.pi_user}@{self.pi_ip}', cmd],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Send password
                stdout, stderr = proc.communicate(input=password + '\n', timeout=30)
                
                if proc.returncode != 0:
                    # Check if it's just asking for password - that's ok
                    if 'password' in stderr.lower():
                        log("Password prompt appeared, trying again...")
                        # This will require user input
                        return False
                    else:
                        error(f"Command failed: {stderr}")
                        return False
                else:
                    success(f"Executed: {cmd}")
                
            except subprocess.TimeoutExpired:
                error(f"SSH command timeout: {cmd}")
                return False
            except Exception as e:
                error(f"Error executing SSH command: {e}")
                return False
        
        return True
    
    def copy_key_interactive(self) -> bool:
        """Interactive SSH key copy."""
        log("Setting up SSH key interactively...")
        
        pub_key = self.read_public_key()
        
        print(f"\n{Colors.YELLOW}{'=' * 70}{Colors.NC}")
        print(f"{Colors.YELLOW}Manual SSH Key Setup{Colors.NC}")
        print(f"{Colors.YELLOW}{'=' * 70}{Colors.NC}\n")
        
        print(f"1. Open a new terminal and SSH to Pi:")
        print(f"   ssh {self.pi_user}@{self.pi_ip}\n")
        
        print(f"2. Create SSH directory:")
        print(f"   mkdir -p ~/.ssh\n")
        
        print(f"3. Add public key to authorized_keys:")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}")
        print(pub_key)
        print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")
        
        print(f"4. Use this command on the Pi to add the key:")
        print(f'{Colors.GREEN}echo "{pub_key}" >> ~/.ssh/authorized_keys{Colors.NC}\n')
        
        print(f"5. Fix permissions:")
        print(f"   chmod 600 ~/.ssh/authorized_keys\n")
        
        input(f"{Colors.YELLOW}Press Enter when you've completed the setup on Pi...{Colors.NC}\n")
        
        return self.test_key_connection()
    
    def test_key_connection(self) -> bool:
        """Test SSH connection with key."""
        log("Testing SSH key connection...")
        
        try:
            cmd = [
                'ssh',
                '-i', str(self.private_key),
                '-o', 'ConnectTimeout=10',
                '-o', 'StrictHostKeyChecking=no',
                f'{self.pi_user}@{self.pi_ip}',
                'echo SSH key test successful'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                success("SSH key connection verified!")
                return True
            else:
                error(f"SSH key test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            error("SSH key test timeout")
            return False
        except Exception as e:
            error(f"Error testing SSH key: {e}")
            return False
    
    def run(self, password: str = None):
        """Run the setup."""
        print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
        print(f"{Colors.BLUE}SSH Key Setup for Raspberry Pi{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")
        
        # Try automated copy first if password provided
        if password:
            log(f"Attempting automated setup with provided password...")
            if self.copy_key_via_ssh(password):
                time.sleep(2)
                if self.test_key_connection():
                    return True
                else:
                    warning("Key connection test failed, trying manual setup...")
        
        # Fall back to interactive
        return self.copy_key_interactive()

def main():
    """Main entry point."""
    setup = AutoSSHSetup()
    
    # Get password
    password = getpass.getpass(f"Enter SSH password for {setup.pi_user}@{setup.pi_ip}: ")
    
    if setup.run(password):
        print(f"\n{Colors.GREEN}{'=' * 70}{Colors.NC}")
        print(f"{Colors.GREEN}SSH Setup Completed Successfully!{Colors.NC}")
        print(f"{Colors.GREEN}{'=' * 70}{Colors.NC}\n")
        
        print(f"You can now deploy without entering password.\n")
        print(f"Next step: Run deployment script")
        print(f"  powershell -ExecutionPolicy Bypass -Command")
        print(f"  '.\\Deploy-ToRaspberryPi-Clean.ps1 -Username 0913431718 -Password 68686868'\n")
        
        return 0
    else:
        print(f"\n{Colors.RED}{'=' * 70}{Colors.NC}")
        print(f"{Colors.RED}SSH Setup Failed or Incomplete!{Colors.NC}")
        print(f"{Colors.RED}{'=' * 70}{Colors.NC}\n")
        
        print(f"Please complete the manual setup steps shown above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())