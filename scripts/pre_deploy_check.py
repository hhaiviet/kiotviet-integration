#!/usr/bin/env python3
"""
Pre-deployment Check and Preparation Script
Validates all deployment requirements before starting
"""

import os
import sys
import subprocess
from pathlib import Path
import json
from typing import List, Tuple, Dict, Any

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'

def log(message: str, color: str = Colors.BLUE):
    print(f"{color}[CHECK]{Colors.NC} {message}")

def success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def warning(message: str):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.NC}")

def info(message: str):
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.NC}")

class PreDeploymentChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.issues = []
        self.warnings = []
        
    def check_files(self) -> bool:
        """Check if all required files exist."""
        log("Checking required deployment files...")
        
        required_files = [
            "deploy/fully_automated_deploy.sh",
            "deploy/setup_raspberry_pi.sh", 
            "deploy/deploy_to_pi.sh",
            "scripts/kiotviet_auto_token_enhanced.py",
            "scripts/kiotviet_run_all.py",
            "remote_debug.py",
            "requirements.txt",
            "config/default.yml",
            "Dockerfile",
            "docker-compose.yml"
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                success(f"Found: {file_path}")
            else:
                error(f"Missing: {file_path}")
                self.issues.append(f"Missing required file: {file_path}")
                all_exist = False
        
        return all_exist
    
    def check_credentials(self) -> Tuple[bool, Dict[str, str]]:
        """Check and validate credentials."""
        log("Checking credentials...")
        
        credentials = {}
        required_creds = [
            ("KIOTVIET_USERNAME", "KiotViet username"),
            ("KIOTVIET_PASSWORD", "KiotViet password")
        ]
        
        optional_creds = [
            ("KIOTVIET_RETAILER_ID", "Retailer ID (optional)"),
            ("KIOTVIET_BRANCH_ID", "Branch ID (optional)")
        ]
        
        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            success("Found .env file")
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.strip().split('=', 1)
                            credentials[key] = value
            except Exception as e:
                warning(f"Could not read .env file: {e}")
        else:
            info(".env file not found - will create from template")
        
        # Check environment variables
        for var, desc in required_creds + optional_creds:
            env_val = os.environ.get(var)
            if env_val:
                credentials[var] = env_val
                success(f"Found {desc} in environment")
            elif var in credentials:
                success(f"Found {desc} in .env file")
            elif var in [item[0] for item in required_creds]:
                error(f"Missing required credential: {desc}")
                self.issues.append(f"Missing credential: {var}")
        
        return len([item for item in required_creds if item[0] not in credentials]) == 0, credentials
    
    def check_network(self) -> bool:
        """Check network connectivity to Raspberry Pi."""
        log("Checking network connectivity...")
        
        pi_ip = "116.102.136.220"
        
        try:
            # Try ping first
            result = subprocess.run(
                ["ping", "-c" if sys.platform != "win32" else "-n", "1", pi_ip],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                success(f"Pi is reachable at {pi_ip}")
            else:
                warning(f"Could not ping {pi_ip} - may still be reachable via SSH")
                
        except subprocess.TimeoutExpired:
            warning("Ping timeout - network may be slow")
        except Exception as e:
            warning(f"Network check failed: {e}")
        
        # Try SSH connection test (if ssh is available)
        try:
            ssh_result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no", 
                 f"pi@{pi_ip}", "echo", "test"],
                capture_output=True,
                timeout=10
            )
            
            if ssh_result.returncode == 0:
                success("SSH connection successful")
                return True
            else:
                warning("SSH connection failed - may need key setup")
                self.warnings.append("SSH connection not ready")
                return False
                
        except subprocess.TimeoutExpired:
            warning("SSH connection timeout")
            self.warnings.append("SSH connection timeout")
            return False
        except FileNotFoundError:
            warning("SSH client not found")
            self.warnings.append("SSH client not available")
            return False
        except Exception as e:
            warning(f"SSH test failed: {e}")
            self.warnings.append(f"SSH test error: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check local dependencies."""
        log("Checking local dependencies...")
        
        # Check if we're in WSL or Linux for bash scripts
        has_bash = False
        try:
            subprocess.run(["bash", "--version"], capture_output=True, check=True)
            has_bash = True
            success("Bash is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            if sys.platform == "win32":
                warning("Bash not found - you may need WSL or Git Bash for deployment scripts")
                self.warnings.append("No bash shell available")
            else:
                error("Bash not available")
                self.issues.append("Bash shell required")
        
        # Check Python requirements
        try:
            import requests
            success("Python requests library available")
        except ImportError:
            warning("Python requests library not found")
            self.warnings.append("Missing Python dependencies")
        
        return has_bash
    
    def check_deployment_scripts(self) -> bool:
        """Check deployment scripts for executable permissions and syntax."""
        log("Checking deployment scripts...")
        
        scripts = [
            "deploy/fully_automated_deploy.sh",
            "deploy/setup_raspberry_pi.sh", 
            "deploy/deploy_to_pi.sh"
        ]
        
        all_ok = True
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                # Check if executable (Unix-like systems)
                if hasattr(os, 'access') and os.access(script_path, os.X_OK):
                    success(f"Script executable: {script}")
                else:
                    warning(f"Script may need execute permissions: {script}")
                    
                # Basic syntax check for bash scripts
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                        if content.startswith('#!/bin/bash') or content.startswith('#!/usr/bin/bash'):
                            success(f"Valid bash script: {script}")
                        else:
                            warning(f"Script may not be a proper bash script: {script}")
                except Exception as e:
                    warning(f"Could not read script {script}: {e}")
            else:
                error(f"Deployment script missing: {script}")
                all_ok = False
                
        return all_ok
    
    def generate_deployment_command(self, credentials: Dict[str, str]) -> str:
        """Generate the deployment command with credentials."""
        username = credentials.get('KIOTVIET_USERNAME', 'YOUR_USERNAME')
        password = credentials.get('KIOTVIET_PASSWORD', 'YOUR_PASSWORD') 
        retailer_id = credentials.get('KIOTVIET_RETAILER_ID', '')
        branch_id = credentials.get('KIOTVIET_BRANCH_ID', '')
        
        script_path = "deploy/fully_automated_deploy.sh"
        
        if retailer_id and branch_id:
            return f'bash {script_path} "{username}" "{password}" "{retailer_id}" "{branch_id}"'
        else:
            return f'bash {script_path} "{username}" "{password}"'
    
    def create_env_template(self, credentials: Dict[str, str]):
        """Create .env template if not exists."""
        env_file = self.project_root / ".env"
        
        if not env_file.exists():
            info("Creating .env template...")
            
            template = f"""# KiotViet Credentials
KIOTVIET_USERNAME={credentials.get('KIOTVIET_USERNAME', 'your_username')}
KIOTVIET_PASSWORD={credentials.get('KIOTVIET_PASSWORD', 'your_password')}
KIOTVIET_RETAILER_ID={credentials.get('KIOTVIET_RETAILER_ID', 'your_retailer_id')}
KIOTVIET_BRANCH_ID={credentials.get('KIOTVIET_BRANCH_ID', 'your_branch_id')}

# API Configuration
API_BASE_URL=https://api-man1.kiotviet.vn/api
API_TIMEOUT=30
API_MAX_RETRIES=5
API_PAGE_SIZE=100

# Raspberry Pi Configuration
CHROME_BINARY_PATH=/usr/bin/chromium-browser
CHROMEDRIVER_PATH=/usr/bin/chromedriver
DISPLAY=:99

# Azure Storage (Optional)
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
# AZURE_STORAGE_CONTAINER=kiotviet-data
"""
            
            with open(env_file, 'w') as f:
                f.write(template)
            
            success("Created .env template")
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all checks and return results."""
        print(f"\n{Colors.WHITE}🔍 Pre-Deployment Validation{Colors.NC}")
        print("=" * 50)
        
        results = {
            'files_ok': self.check_files(),
            'network_ok': self.check_network(),
            'dependencies_ok': self.check_dependencies(),
            'scripts_ok': self.check_deployment_scripts(),
        }
        
        creds_ok, credentials = self.check_credentials()
        results['creds_ok'] = creds_ok
        results['credentials'] = credentials
        
        # Create .env template if needed
        self.create_env_template(credentials)
        
        # Generate deployment command
        results['deployment_command'] = self.generate_deployment_command(credentials)
        
        return results

def main():
    """Main function."""
    checker = PreDeploymentChecker()
    results = checker.run_all_checks()
    
    print(f"\n{Colors.WHITE}📋 Validation Summary{Colors.NC}")
    print("=" * 50)
    
    # Show results
    checks = [
        ('Files', results['files_ok']),
        ('Network', results['network_ok']),
        ('Dependencies', results['dependencies_ok']),
        ('Scripts', results['scripts_ok']),
        ('Credentials', results['creds_ok'])
    ]
    
    all_good = True
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"  {icon} {check_name}: {color}{status}{Colors.NC}")
        if not status:
            all_good = False
    
    # Show issues
    if checker.issues:
        print(f"\n{Colors.RED}🚨 Issues to Fix:{Colors.NC}")
        for issue in checker.issues:
            print(f"  ❌ {issue}")
    
    if checker.warnings:
        print(f"\n{Colors.YELLOW}⚠️ Warnings:{Colors.NC}")
        for warning in checker.warnings:
            print(f"  ⚠️ {warning}")
    
    # Show deployment instructions
    print(f"\n{Colors.WHITE}🚀 Deployment Instructions{Colors.NC}")
    print("=" * 50)
    
    if all_good:
        success("All checks passed! Ready for deployment.")
        print(f"\n{Colors.CYAN}Run this command to deploy:{Colors.NC}")
        print(f"  {results['deployment_command']}")
        
        print(f"\n{Colors.CYAN}Alternative: Use PowerShell/CMD:{Colors.NC}")
        print(f"  python remote_debug.py status  # Check after deployment")
        
    else:
        error("Some issues need to be fixed before deployment.")
        print(f"\n{Colors.YELLOW}After fixing issues, run:{Colors.NC}")
        print(f"  python {__file__}")
    
    print(f"\n{Colors.WHITE}📚 Next Steps After Deployment:{Colors.NC}")
    print("  1. Monitor deployment: python remote_debug.py status")
    print("  2. Check logs: python remote_debug.py logs")
    print("  3. Test manually: python remote_debug.py sync")
    print("  4. SSH access: python remote_debug.py shell")
    
    print(f"\n{Colors.WHITE}🆘 If Issues Occur:{Colors.NC}")
    print("  1. Check logs: python remote_debug.py logs --follow")
    print("  2. Restart services: python remote_debug.py restart")
    print("  3. Generate token: python remote_debug.py token")
    print("  4. Manual shell: python remote_debug.py shell")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())