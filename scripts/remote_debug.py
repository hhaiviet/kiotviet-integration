#!/usr/bin/env python3
"""
Remote Management and Debugging Tool for KiotViet Raspberry Pi Deployment
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
from datetime import datetime

# Configuration
PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def log(message: str, color: str = Colors.BLUE):
    """Print colored log message."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{color}[{timestamp}]{Colors.NC} {message}")

def error(message: str):
    """Print error message."""
    log(f"❌ {message}", Colors.RED)

def success(message: str):
    """Print success message."""
    log(f"✅ {message}", Colors.GREEN)

def warning(message: str):
    """Print warning message."""
    log(f"⚠️ {message}", Colors.YELLOW)

def info(message: str):
    """Print info message."""
    log(f"ℹ️ {message}", Colors.CYAN)

def run_ssh_command(command: str, capture_output: bool = True) -> str:
    """Execute SSH command on Raspberry Pi."""
    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"{PI_USER}@{PI_IP}", command]
    
    try:
        if capture_output:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                error(f"Command failed: {command}")
                error(f"Error: {result.stderr}")
                return ""
            return result.stdout.strip()
        else:
            subprocess.run(ssh_cmd)
            return ""
    except subprocess.TimeoutExpired:
        error(f"Command timed out: {command}")
        return ""
    except Exception as e:
        error(f"SSH command failed: {e}")
        return ""

def check_connection():
    """Test SSH connection to Raspberry Pi."""
    info("Testing SSH connection...")
    result = run_ssh_command("echo 'Connection OK'")
    if result:
        success("SSH connection successful")
        return True
    else:
        error("Cannot connect to Raspberry Pi")
        return False

def get_service_status() -> Dict[str, Any]:
    """Get status of all services."""
    services = {
        'kiotviet-integration': 'Main application service',
        'kiotviet-monitor': 'Health monitoring service',
        'xvfb': 'Virtual display service'
    }
    
    status = {}
    for service, description in services.items():
        result = run_ssh_command(f"systemctl is-active {service}")
        status[service] = {
            'active': result == 'active',
            'description': description,
            'status': result
        }
    
    return status

def show_status():
    """Show comprehensive system status."""
    info("Getting system status...")
    
    # Service status
    print(f"\n{Colors.WHITE}📊 Service Status:{Colors.NC}")
    services = get_service_status()
    for service, data in services.items():
        status_color = Colors.GREEN if data['active'] else Colors.RED
        status_icon = "✅" if data['active'] else "❌"
        print(f"  {status_icon} {service}: {status_color}{data['status']}{Colors.NC} - {data['description']}")
    
    # System resources
    print(f"\n{Colors.WHITE}💻 System Resources:{Colors.NC}")
    uptime = run_ssh_command("uptime")
    if uptime:
        print(f"  🕐 Uptime: {uptime}")
    
    memory = run_ssh_command("free -h | grep Mem")
    if memory:
        print(f"  🧠 Memory: {memory}")
    
    disk = run_ssh_command("df -h / | tail -1")
    if disk:
        print(f"  💾 Disk: {disk}")
    
    # Temperature (Raspberry Pi specific)
    temp = run_ssh_command("vcgencmd measure_temp 2>/dev/null || echo 'N/A'")
    if temp and temp != 'N/A':
        print(f"  🌡️ Temperature: {temp}")
    
    # Last successful run
    print(f"\n{Colors.WHITE}📝 Application Status:{Colors.NC}")
    last_run = run_ssh_command(f"ls -la {PROJECT_DIR}/data/output/ 2>/dev/null | tail -3 || echo 'No output files found'")
    if last_run:
        print(f"  📁 Recent output files:")
        for line in last_run.split('\n')[-3:]:
            if line.strip():
                print(f"    {line}")
    
    # Token status
    token_status = run_ssh_command(f"test -f {PROJECT_DIR}/data/credentials/token.json && echo 'exists' || echo 'missing'")
    token_icon = "✅" if token_status == "exists" else "❌"
    print(f"  {token_icon} Token file: {token_status}")
    
    if token_status == "exists":
        token_age = run_ssh_command(f"stat -c %Y {PROJECT_DIR}/data/credentials/token.json")
        if token_age:
            try:
                age_seconds = int(time.time()) - int(token_age)
                age_hours = age_seconds // 3600
                print(f"    🕐 Token age: {age_hours} hours")
            except:
                pass

def show_logs(lines: int = 50, follow: bool = False):
    """Show application logs."""
    info(f"Showing last {lines} log entries...")
    
    if follow:
        info("Following logs (Ctrl+C to stop)...")
        command = f"sudo journalctl -u kiotviet-integration -n {lines} -f"
    else:
        command = f"sudo journalctl -u kiotviet-integration -n {lines} --no-pager"
    
    run_ssh_command(command, capture_output=False)

def restart_services():
    """Restart all services."""
    services = ['kiotviet-integration', 'kiotviet-monitor']
    
    for service in services:
        info(f"Restarting {service}...")
        result = run_ssh_command(f"sudo systemctl restart {service}")
        if result is not None:  # Empty string is success
            success(f"{service} restarted successfully")
        else:
            error(f"Failed to restart {service}")
        time.sleep(2)
    
    # Check status after restart
    time.sleep(5)
    info("Checking services after restart...")
    show_status()

def update_application():
    """Update application from Git repository."""
    info("Updating application...")
    
    commands = [
        f"cd {PROJECT_DIR}",
        "git fetch origin",
        "git reset --hard origin/main",
        "source venv/bin/activate && pip install -r requirements.txt",
        "sudo systemctl restart kiotviet-integration"
    ]
    
    for cmd in commands:
        info(f"Running: {cmd}")
        result = run_ssh_command(f"cd {PROJECT_DIR} && {cmd}")
        if result is None and "git" not in cmd:  # Git commands might not return output
            error(f"Command failed: {cmd}")
            return
    
    success("Application updated successfully")
    time.sleep(3)
    show_status()

def generate_token():
    """Generate new KiotViet token."""
    info("Generating new token...")
    
    command = f"cd {PROJECT_DIR} && source venv/bin/activate && python scripts/kiotviet_auto_token_enhanced.py"
    run_ssh_command(command, capture_output=False)
    
    # Check if token was created
    token_status = run_ssh_command(f"test -f {PROJECT_DIR}/data/credentials/token.json && echo 'success' || echo 'failed'")
    if token_status == "success":
        success("Token generation completed")
    else:
        error("Token generation failed")

def run_manual_sync():
    """Run manual data synchronization."""
    info("Running manual data synchronization...")
    
    command = f"cd {PROJECT_DIR} && source venv/bin/activate && python scripts/kiotviet_run_all.py"
    run_ssh_command(command, capture_output=False)
    
    success("Manual sync completed")

def show_configuration():
    """Show current configuration."""
    info("Current configuration:")
    
    # Environment variables
    print(f"\n{Colors.WHITE}🔧 Environment Configuration:{Colors.NC}")
    env_vars = [
        "KIOTVIET_USERNAME",
        "KIOTVIET_RETAILER_ID", 
        "KIOTVIET_BRANCH_ID",
        "API_BASE_URL",
        "DISPLAY"
    ]
    
    for var in env_vars:
        value = run_ssh_command(f"cd {PROJECT_DIR} && source .env && echo ${var}")
        masked_value = value if var not in ["KIOTVIET_PASSWORD"] else "*" * 10
        print(f"  {var}: {masked_value}")
    
    # Cron jobs
    print(f"\n{Colors.WHITE}⏰ Scheduled Tasks:{Colors.NC}")
    cron_jobs = run_ssh_command("crontab -l | grep kiotviet || echo 'No cron jobs found'")
    if cron_jobs:
        for job in cron_jobs.split('\n'):
            if job.strip():
                print(f"  {job}")

def interactive_shell():
    """Open interactive SSH shell."""
    info("Opening interactive SSH session...")
    subprocess.run(["ssh", "-t", f"{PI_USER}@{PI_IP}"])

def show_monitoring_dashboard():
    """Show monitoring information."""
    info("Monitoring Dashboard")
    
    # Get status file
    status_data = run_ssh_command(f"cat {PROJECT_DIR}/data/logs/status.json 2>/dev/null || echo '{{}}'")
    
    try:
        status = json.loads(status_data) if status_data.strip() != '{}' else {}
        
        print(f"\n{Colors.WHITE}📊 Monitoring Dashboard:{Colors.NC}")
        if status:
            print(f"  Last Check: {status.get('last_check', 'Unknown')}")
            print(f"  Service Active: {status.get('service_active', 'Unknown')}")
        else:
            print("  No monitoring data available")
        
        # Recent log summary
        print(f"\n{Colors.WHITE}📋 Recent Activity:{Colors.NC}")
        recent_logs = run_ssh_command(f"sudo journalctl -u kiotviet-integration --since '1 hour ago' | tail -10")
        if recent_logs:
            for line in recent_logs.split('\n')[-5:]:
                if line.strip():
                    print(f"  {line}")
        
    except json.JSONDecodeError:
        warning("Could not parse monitoring data")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="KiotViet Raspberry Pi Remote Management")
    parser.add_argument('command', choices=[
        'status', 'logs', 'restart', 'update', 'shell', 
        'monitor', 'token', 'sync', 'config', 'help'
    ], help='Command to execute')
    parser.add_argument('--lines', type=int, default=50, help='Number of log lines to show')
    parser.add_argument('--follow', action='store_true', help='Follow logs in real-time')
    
    args = parser.parse_args()
    
    if args.command == 'help':
        print(f"""
{Colors.WHITE}KiotViet Raspberry Pi Remote Management Tool{Colors.NC}

Available commands:
  {Colors.GREEN}status{Colors.NC}   - Show comprehensive system status
  {Colors.GREEN}logs{Colors.NC}     - Show application logs (use --follow for real-time)
  {Colors.GREEN}restart{Colors.NC}  - Restart all services
  {Colors.GREEN}update{Colors.NC}   - Update application from Git
  {Colors.GREEN}shell{Colors.NC}    - Open interactive SSH session
  {Colors.GREEN}monitor{Colors.NC}  - Show monitoring dashboard
  {Colors.GREEN}token{Colors.NC}    - Generate new KiotViet token
  {Colors.GREEN}sync{Colors.NC}     - Run manual data synchronization
  {Colors.GREEN}config{Colors.NC}   - Show current configuration
  {Colors.GREEN}help{Colors.NC}     - Show this help message

Examples:
  python remote_debug.py status
  python remote_debug.py logs --lines 100 --follow
  python remote_debug.py restart
  python remote_debug.py update

Target: {PI_USER}@{PI_IP}
        """)
        return
    
    # Check connection first
    if not check_connection():
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'status':
            show_status()
        elif args.command == 'logs':
            show_logs(args.lines, args.follow)
        elif args.command == 'restart':
            restart_services()
        elif args.command == 'update':
            update_application()
        elif args.command == 'shell':
            interactive_shell()
        elif args.command == 'monitor':
            show_monitoring_dashboard()
        elif args.command == 'token':
            generate_token()
        elif args.command == 'sync':
            run_manual_sync()
        elif args.command == 'config':
            show_configuration()
            
    except KeyboardInterrupt:
        info("Operation cancelled by user")
    except Exception as e:
        error(f"Operation failed: {e}")

if __name__ == "__main__":
    main()