#!/usr/bin/env python3
"""
SSH Setup Automation for Raspberry Pi
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def log(msg: str, color: str = Colors.BLUE):
    print(f"{color}[SSH Setup]{Colors.NC} {msg}")

def success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

class SSHSetup:
    def __init__(self):
        self.pi_ip = "116.102.136.220"
        self.pi_user = "hhaiviet"
        self.ssh_dir = Path.home() / ".ssh"
        self.private_key = self.ssh_dir / "id_rsa"
        self.public_key = self.ssh_dir / "id_rsa.pub"
        
    def check_ssh_key(self) -> bool:
        """Check if SSH key exists."""
        log("Checking SSH key...")
        if self.private_key.exists() and self.public_key.exists():
            success(f"SSH key found at {self.private_key}")
            return True
        else:
            warning("SSH key not found")
            return False
    
    def generate_ssh_key(self) -> bool:
        """Generate SSH key."""
        log("Generating SSH key...")
        try:
            # Create .ssh directory if it doesn't exist
            self.ssh_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate key
            cmd = [
                "ssh-keygen",
                "-t", "rsa",
                "-b", "4096",
                "-f", str(self.private_key),
                "-N", ""
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                success(f"SSH key generated at {self.private_key}")
                return True
            else:
                error(f"Failed to generate SSH key: {result.stderr}")
                return False
        except Exception as e:
            error(f"Error generating SSH key: {e}")
            return False
    
    def test_ssh_connection(self) -> bool:
        """Test SSH connection without key."""
        log("Testing SSH connection (you'll be prompted for password)...")
        try:
            cmd = [
                "ssh",
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{self.pi_user}@{self.pi_ip}",
                "echo", "SSH test successful"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                success("SSH connection test successful")
                return True
            else:
                error(f"SSH connection failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            error("SSH connection timeout")
            return False
        except Exception as e:
            error(f"Error testing SSH: {e}")
            return False
    
    def copy_public_key(self, pi_password: str) -> bool:
        """Copy public key to Raspberry Pi."""
        log("Copying public key to Raspberry Pi...")
        
        try:
            # Read public key
            if not self.public_key.exists():
                error(f"Public key not found at {self.public_key}")
                return False
            
            with open(self.public_key, 'r') as f:
                pub_key_content = f.read()
            
            # Create authorized_keys command
            cmd = f"mkdir -p ~/.ssh && echo '{pub_key_content}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
            
            # Run ssh command with password
            ssh_cmd = [
                "sshpass",
                "-p", pi_password,
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                f"{self.pi_user}@{self.pi_ip}",
                cmd
            ]
            
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                success("Public key copied to Raspberry Pi")
                return True
            else:
                # Try alternative method if sshpass not available
                warning("sshpass not available, trying manual method...")
                return self.copy_public_key_manual(pi_password)
        except Exception as e:
            error(f"Error copying public key: {e}")
            return False
    
    def copy_public_key_manual(self, pi_password: str) -> bool:
        """Manual method to copy public key using echo."""
        log("Using manual method to copy public key...")
        
        try:
            with open(self.public_key, 'r') as f:
                pub_key_content = f.read().strip()
            
            # This requires user interaction, so we'll show instructions
            print(f"\n{Colors.YELLOW}Manual Setup Instructions:{Colors.NC}")
            print("=" * 60)
            print(f"1. SSH to your Raspberry Pi:")
            print(f"   ssh {self.pi_user}@{self.pi_ip}")
            print(f"\n2. Create authorized_keys directory:")
            print(f"   mkdir -p ~/.ssh")
            print(f"\n3. Add this public key:")
            print("-" * 60)
            print(pub_key_content)
            print("-" * 60)
            print(f"\n4. Save it to ~/.ssh/authorized_keys")
            print(f"   Or use: echo 'YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys")
            print(f"\n5. Set permissions:")
            print(f"   chmod 600 ~/.ssh/authorized_keys")
            print("=" * 60)
            
            input(f"\n{Colors.YELLOW}Press Enter after you've completed the manual setup...{Colors.NC}")
            
            # Test connection after manual setup
            return self.test_key_connection()
            
        except Exception as e:
            error(f"Error in manual setup: {e}")
            return False
    
    def test_key_connection(self) -> bool:
        """Test SSH connection with key."""
        log("Testing SSH connection with key...")
        try:
            cmd = [
                "ssh",
                "-i", str(self.private_key),
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=10",
                f"{self.pi_user}@{self.pi_ip}",
                "echo", "Key connection test successful"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                success("SSH key connection test successful")
                return True
            else:
                error(f"SSH key connection failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            error("SSH connection timeout")
            return False
        except Exception as e:
            error(f"Error testing SSH key: {e}")
            return False
    
    def setup_complete(self) -> bool:
        """Setup SSH and test connection."""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}SSH Setup for Raspberry Pi{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")
        
        # Check if key exists
        if not self.check_ssh_key():
            log("Generating new SSH key...")
            if not self.generate_ssh_key():
                return False
        
        # Get Pi password
        print(f"\n{Colors.YELLOW}Raspberry Pi SSH Password:{Colors.NC}")
        print(f"Default is usually: raspberry (or your custom password)")
        print(f"Target: {self.pi_user}@{self.pi_ip}\n")
        
        # Try to use sshpass if available
        try:
            subprocess.run(["sshpass", "-h"], capture_output=True, timeout=5)
            pi_password = input(f"Enter Raspberry Pi password for {self.pi_user}: ")
            
            if self.copy_public_key(pi_password):
                print("")
                return self.test_key_connection()
        except Exception:
            # sshpass not available, show manual instructions
            return self.copy_public_key_manual("")
        
        return False

def main():
    """Main entry point."""
    setup = SSHSetup()
    
    if setup.setup_complete():
        print(f"\n{Colors.GREEN}{'=' * 60}{Colors.NC}")
        print(f"{Colors.GREEN}SSH Setup Completed Successfully!{Colors.NC}")
        print(f"{Colors.GREEN}{'=' * 60}{Colors.NC}")
        print(f"\nYou can now deploy without entering password:")
        print(f"  python remote_debug.py status")
        print(f"  ./Deploy-ToRaspberryPi-Clean.ps1 -Username '...' -Password '...'")
        return 0
    else:
        print(f"\n{Colors.RED}{'=' * 60}{Colors.NC}")
        print(f"{Colors.RED}SSH Setup Failed!{Colors.NC}")
        print(f"{Colors.RED}{'=' * 60}{Colors.NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())