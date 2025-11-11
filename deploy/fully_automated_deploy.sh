#!/bin/bash

# KiotViet Integration - Fully Automated Raspberry Pi 4 Deployment
# This script handles complete automation with credentials and remote modifications

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PI_IP="116.102.136.220"
PI_USER="hhaiviet"
PROJECT_NAME="kiotviet-integration"
PROJECT_DIR="/home/hhaiviet/$PROJECT_NAME"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if credentials are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <kiotviet_username> <kiotviet_password> [retailer_id] [branch_id]"
    echo "Example: $0 myusername mypassword 12345 67890"
    exit 1
fi

KIOTVIET_USERNAME="$1"
KIOTVIET_PASSWORD="$2"
KIOTVIET_RETAILER_ID="${3:-}"
KIOTVIET_BRANCH_ID="${4:-}"

log "🚀 Starting fully automated deployment to Raspberry Pi 4..."
log "📡 Target: $PI_USER@$PI_IP"
log "👤 KiotViet User: $KIOTVIET_USERNAME"

# Function to execute remote commands with error handling
remote_exec() {
    local command="$1"
    local description="$2"
    
    log "$description"
    if ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no $PI_USER@$PI_IP "$command"; then
        success "$description completed"
    else
        error "$description failed"
    fi
}

# Function to upload file with retry
upload_file() {
    local source="$1"
    local dest="$2"
    local description="$3"
    
    log "$description"
    for i in {1..3}; do
        if scp -o StrictHostKeyChecking=no "$source" "$PI_USER@$PI_IP:$dest"; then
            success "$description completed"
            return 0
        else
            warning "Upload attempt $i failed, retrying..."
            sleep 5
        fi
    done
    error "$description failed after 3 attempts"
}

# Check SSH connection
log "🔍 Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $PI_USER@$PI_IP "echo 'SSH OK'"; then
    error "Cannot connect to $PI_IP. Please check network and SSH access."
fi

# Create deployment package
log "📦 Creating deployment package..."
TEMP_DIR=$(mktemp -d)
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' --exclude='data' --exclude='node_modules' . "$TEMP_DIR/"

# Create automated .env file
log "⚙️  Creating environment configuration..."
cat > "$TEMP_DIR/.env" <<EOF
# KiotViet Credentials - Auto-generated $(date)
KIOTVIET_USERNAME=$KIOTVIET_USERNAME
KIOTVIET_PASSWORD=$KIOTVIET_PASSWORD
KIOTVIET_RETAILER_ID=$KIOTVIET_RETAILER_ID
KIOTVIET_BRANCH_ID=$KIOTVIET_BRANCH_ID

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

# Azure Storage (Optional - uncomment and configure if needed)
# AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
# AZURE_STORAGE_CONTAINER=kiotviet-data

# Remote monitoring
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_PORT=8080
EOF

# Upload files to Raspberry Pi
log "📤 Uploading files to Raspberry Pi..."
remote_exec "sudo mkdir -p $PROJECT_DIR && sudo chown $PI_USER:$PI_USER $PROJECT_DIR" "Creating project directory"

rsync -av --delete --progress "$TEMP_DIR/" "$PI_USER@$PI_IP:$PROJECT_DIR/"

# Execute complete setup on Raspberry Pi
log "🔧 Running automated setup on Raspberry Pi..."
ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'REMOTE_SETUP'
set -e

PROJECT_DIR="/home/pi/kiotviet-integration"
cd "$PROJECT_DIR"

# Color codes for remote output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[REMOTE]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

log "🍓 Starting Raspberry Pi setup..."

# Update system
log "📦 Updating system packages..."
sudo apt update -qq && sudo apt upgrade -y -qq

# Install required packages
log "🐍 Installing system dependencies..."
sudo apt install -y -qq \
    python3 python3-pip python3-venv git curl wget \
    chromium-browser chromium-chromedriver \
    xvfb x11vnc fluxbox \
    htop tree nano unzip \
    cron systemd

# Setup virtual display for headless Selenium
log "🖥️ Setting up virtual display..."
sudo systemctl enable xvfb || true
cat > /tmp/xvfb.service << 'EOF'
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1024x768x24
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/xvfb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xvfb
sudo systemctl start xvfb

# Create Python virtual environment
log "🔧 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies with retry
log "📦 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create necessary directories
log "📁 Creating data structure..."
mkdir -p data/{output,checkpoints,logs,credentials}
mkdir -p /home/pi/chrome-profile
chmod 755 data data/*

# Test Selenium setup
log "🧪 Testing Selenium setup..."
export DISPLAY=:99
python3 << 'PYTHON_TEST'
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = '/usr/bin/chromium-browser'
    
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.google.com')
    print("✅ Selenium test successful")
    driver.quit()
except Exception as e:
    print(f"❌ Selenium test failed: {e}")
    exit(1)
PYTHON_TEST

success "Selenium setup verified!"

REMOTE_SETUP

# Create enhanced systemd service
log "🔧 Creating systemd service..."
ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'SERVICE_SETUP'
sudo tee /etc/systemd/system/kiotviet-integration.service > /dev/null << 'EOF'
[Unit]
Description=KiotViet Integration Service
After=network.target xvfb.service
Requires=xvfb.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/kiotviet-integration
Environment=PATH=/home/pi/kiotviet-integration/venv/bin
Environment=DISPLAY=:99
ExecStartPre=/bin/sleep 10
ExecStart=/home/pi/kiotviet-integration/venv/bin/python scripts/kiotviet_run_all.py
Restart=always
RestartSec=30
StartLimitInterval=350
StartLimitBurst=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=kiotviet-integration

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
cat > /home/pi/kiotviet-integration/monitor_service.py << 'EOF'
#!/usr/bin/env python3
"""Service monitoring and auto-recovery script."""

import subprocess
import time
import logging
from datetime import datetime
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/kiotviet-integration/data/logs/monitor.log'),
        logging.StreamHandler()
    ]
)

def check_service_status():
    """Check if the service is running."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'kiotviet-integration'],
            capture_output=True, text=True
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        logging.error(f"Error checking service: {e}")
        return False

def restart_service():
    """Restart the service."""
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'kiotviet-integration'], check=True)
        logging.info("Service restarted successfully")
        return True
    except Exception as e:
        logging.error(f"Error restarting service: {e}")
        return False

def log_status():
    """Log current status."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'service_active': check_service_status(),
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    status_file = Path('/home/pi/kiotviet-integration/data/logs/status.json')
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)

if __name__ == '__main__':
    while True:
        if not check_service_status():
            logging.warning("Service is not running, attempting restart...")
            if restart_service():
                logging.info("Service restart successful")
            else:
                logging.error("Service restart failed")
        
        log_status()
        time.sleep(300)  # Check every 5 minutes
EOF

chmod +x /home/pi/kiotviet-integration/monitor_service.py

# Create monitor service
sudo tee /etc/systemd/system/kiotviet-monitor.service > /dev/null << 'EOF'
[Unit]
Description=KiotViet Integration Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/kiotviet-integration
ExecStart=/home/pi/kiotviet-integration/venv/bin/python monitor_service.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable kiotviet-integration
sudo systemctl enable kiotviet-monitor

SERVICE_SETUP

# Generate token automatically
log "🔑 Generating KiotViet access token..."
ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'TOKEN_SETUP'
cd /home/pi/kiotviet-integration
source venv/bin/activate
export DISPLAY=:99

# Run token generation with error handling
python scripts/kiotviet_auto_token_seleniumwire.py || {
    echo "❌ Token generation failed, but continuing with deployment..."
    echo "You can generate token manually later with:"
    echo "cd /home/pi/kiotviet-integration && source venv/bin/activate && python scripts/kiotviet_auto_token_seleniumwire.py"
}
TOKEN_SETUP

# Setup scheduled execution
log "⏰ Setting up automated scheduling..."
ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'CRON_SETUP'
# Create cron job for regular execution
(crontab -l 2>/dev/null; echo "0 */2 * * * cd /home/pi/kiotviet-integration && ./venv/bin/python scripts/kiotviet_run_all.py >> data/logs/cron.log 2>&1") | crontab -

# Create cron job for daily token refresh
(crontab -l 2>/dev/null; echo "0 2 * * * cd /home/pi/kiotviet-integration && ./venv/bin/python scripts/kiotviet_auto_token_seleniumwire.py >> data/logs/token_refresh.log 2>&1") | crontab -

# Create cron job for log cleanup
(crontab -l 2>/dev/null; echo "0 3 * * 0 find /home/pi/kiotviet-integration/data/logs -name '*.log' -mtime +7 -delete") | crontab -

CRON_SETUP

# Start services
log "🚀 Starting services..."
remote_exec "sudo systemctl start kiotviet-integration" "Starting main service"
remote_exec "sudo systemctl start kiotviet-monitor" "Starting monitor service"

# Create remote management script
log "🛠️ Creating remote management tools..."
cat > "$TEMP_DIR/remote_manage.sh" << 'EOF'
#!/bin/bash

PI_IP="116.102.136.220"
PI_USER="pi"

case "$1" in
    status)
        echo "🔍 Checking service status..."
        ssh $PI_USER@$PI_IP "sudo systemctl status kiotviet-integration"
        ;;
    logs)
        echo "📋 Showing recent logs..."
        ssh $PI_USER@$PI_IP "sudo journalctl -u kiotviet-integration -n 50 -f"
        ;;
    restart)
        echo "🔄 Restarting service..."
        ssh $PI_USER@$PI_IP "sudo systemctl restart kiotviet-integration"
        ;;
    update)
        echo "📥 Updating application..."
        ssh $PI_USER@$PI_IP "cd /home/pi/kiotviet-integration && git pull origin main && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart kiotviet-integration"
        ;;
    shell)
        echo "💻 Opening remote shell..."
        ssh -t $PI_USER@$PI_IP
        ;;
    monitor)
        echo "📊 Opening monitoring dashboard..."
        ssh $PI_USER@$PI_IP "cd /home/pi/kiotviet-integration && source venv/bin/activate && python -c \"
import json
from pathlib import Path
status_file = Path('data/logs/status.json')
if status_file.exists():
    with open(status_file) as f:
        status = json.load(f)
    print(f'Last check: {status[\"last_check\"]}')
    print(f'Service active: {status[\"service_active\"]}')
else:
    print('No status file found')
\""
        ;;
    *)
        echo "Usage: $0 {status|logs|restart|update|shell|monitor}"
        exit 1
        ;;
esac
EOF

chmod +x "$TEMP_DIR/remote_manage.sh"
cp "$TEMP_DIR/remote_manage.sh" ./remote_manage.sh

# Cleanup temp directory
rm -rf "$TEMP_DIR"

# Final verification
log "🔍 Performing final verification..."
sleep 10
ssh -o StrictHostKeyChecking=no $PI_USER@$PI_IP << 'VERIFY'
cd /home/pi/kiotviet-integration

echo "📊 Service Status:"
sudo systemctl is-active kiotviet-integration || echo "❌ Main service not active"
sudo systemctl is-active kiotviet-monitor || echo "❌ Monitor service not active"
sudo systemctl is-active xvfb || echo "❌ Display service not active"

echo ""
echo "📁 Directory Structure:"
ls -la data/

echo ""
echo "🔧 Configuration:"
if [ -f .env ]; then
    echo "✅ Environment file exists"
else
    echo "❌ Environment file missing"
fi

if [ -f data/credentials/token.json ]; then
    echo "✅ Token file exists"
else
    echo "⚠️ Token file not found (may need manual generation)"
fi

echo ""
echo "💾 Disk Usage:"
df -h /home

echo ""
echo "🔄 Recent Log Entries:"
sudo journalctl -u kiotviet-integration -n 5 --no-pager || echo "No logs yet"
VERIFY

success "🎉 Deployment completed successfully!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📋 DEPLOYMENT SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo "🎯 Target: $PI_USER@$PI_IP"
echo "👤 KiotViet User: $KIOTVIET_USERNAME"
echo "📁 Project Path: $PROJECT_DIR"
echo ""
echo "🔧 Services Status:"
echo "  • kiotviet-integration: Main application service"
echo "  • kiotviet-monitor: Health monitoring service"
echo "  • xvfb: Virtual display for Selenium"
echo ""
echo "⏰ Scheduled Tasks:"
echo "  • Data sync: Every 2 hours"
echo "  • Token refresh: Daily at 2 AM"
echo "  • Log cleanup: Weekly"
echo ""
echo "🛠️ Remote Management:"
echo "  • Check status: ./remote_manage.sh status"
echo "  • View logs: ./remote_manage.sh logs"
echo "  • Restart: ./remote_manage.sh restart"
echo "  • Update: ./remote_manage.sh update"
echo "  • SSH shell: ./remote_manage.sh shell"
echo "  • Monitor: ./remote_manage.sh monitor"
echo ""
echo "📚 Manual Commands:"
echo "  • SSH: ssh $PI_USER@$PI_IP"
echo "  • Check status: sudo systemctl status kiotviet-integration"
echo "  • View logs: sudo journalctl -u kiotviet-integration -f"
echo "  • Restart: sudo systemctl restart kiotviet-integration"
echo ""
echo "═══════════════════════════════════════════════════════════"
warning "If there are any errors, use ./remote_manage.sh logs to diagnose"
success "Your KiotViet integration is now running automatically! 🚀"