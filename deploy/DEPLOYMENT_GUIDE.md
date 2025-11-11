# 🍓 KiotViet Integration - Raspberry Pi 4 Deployment

## 🚀 Automated Deployment Guide

### Prerequisites
- Raspberry Pi 4 with SSH access enabled
- Network connectivity to `116.102.136.220`
- KiotViet account credentials

### Option 1: Fully Automated Deployment (Recommended)

Run the complete automation script with your credentials:

```bash
# Make script executable
chmod +x deploy/fully_automated_deploy.sh

# Deploy with credentials
./deploy/fully_automated_deploy.sh "your_username" "your_password" "retailer_id" "branch_id"

# Example:
./deploy/fully_automated_deploy.sh "john@example.com" "mypassword" "12345" "67890"
```

This script will:
- ✅ Test SSH connectivity
- ✅ Upload all project files
- ✅ Install system dependencies (Python, Chrome, etc.)
- ✅ Setup virtual environment
- ✅ Configure services (systemd + monitoring)
- ✅ Generate KiotViet access token automatically
- ✅ Setup scheduled tasks (cron)
- ✅ Start all services
- ✅ Create remote management tools

### Option 2: Manual Step-by-Step

If you prefer manual control:

```bash
# 1. Deploy files only
bash deploy/deploy_to_pi.sh

# 2. SSH to Pi and run setup
ssh pi@116.102.136.220
cd kiotviet-integration
./deploy/setup_raspberry_pi.sh

# 3. Configure credentials
nano .env

# 4. Generate token
source venv/bin/activate
python scripts/kiotviet_auto_token_enhanced.py

# 5. Start services
sudo systemctl start kiotviet-integration
```

## 🛠️ Remote Management

After deployment, use these tools for remote management:

### Quick Management Script
```bash
# Check status
./remote_manage.sh status

# View logs
./remote_manage.sh logs

# Restart service
./remote_manage.sh restart

# Update application
./remote_manage.sh update

# Open SSH shell
./remote_manage.sh shell
```

### Advanced Debugging Tool
```bash
# Comprehensive status
python remote_debug.py status

# Follow logs in real-time
python remote_debug.py logs --follow

# Run manual sync
python remote_debug.py sync

# Generate new token
python remote_debug.py token

# Show configuration
python remote_debug.py config

# Interactive shell
python remote_debug.py shell
```

## 📊 Services Overview

### Main Services
- **kiotviet-integration**: Main application service
- **kiotviet-monitor**: Health monitoring and auto-restart
- **xvfb**: Virtual display for headless Selenium

### Scheduled Tasks
- **Data sync**: Every 2 hours
- **Token refresh**: Daily at 2 AM
- **Log cleanup**: Weekly

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. SSH Connection Failed
```bash
# Test connectivity
ping 116.102.136.220

# Generate SSH key if needed
ssh-keygen -t rsa -b 4096
ssh-copy-id pi@116.102.136.220
```

#### 2. Service Not Starting
```bash
# Check service status
python remote_debug.py status

# View detailed logs
python remote_debug.py logs --lines 100

# Restart services
python remote_debug.py restart
```

#### 3. Token Generation Failed
```bash
# Manual token generation
python remote_debug.py token

# Check Chrome installation
ssh pi@116.102.136.220 "chromium-browser --version"
```

#### 4. Selenium Issues
```bash
# Check display service
ssh pi@116.102.136.220 "systemctl status xvfb"

# Test Chrome headless
ssh pi@116.102.136.220 "DISPLAY=:99 chromium-browser --headless --dump-dom https://google.com"
```

#### 5. Memory Issues
```bash
# Check memory usage
python remote_debug.py status

# Restart to clear memory
python remote_debug.py restart
```

## 📋 Manual Commands

### On Raspberry Pi (via SSH)

```bash
# SSH to Pi
ssh pi@116.102.136.220

# Service management
sudo systemctl status kiotviet-integration
sudo systemctl start kiotviet-integration
sudo systemctl stop kiotviet-integration
sudo systemctl restart kiotviet-integration

# View logs
sudo journalctl -u kiotviet-integration -f
sudo journalctl -u kiotviet-integration -n 100

# Manual execution
cd /home/pi/kiotviet-integration
source venv/bin/activate
python scripts/kiotviet_run_all.py

# Token generation
python scripts/kiotviet_auto_token_enhanced.py

# Check cron jobs
crontab -l

# System resources
htop
df -h
free -h
vcgencmd measure_temp
```

## 🔧 Configuration Files

### Environment Variables (.env)
```env
KIOTVIET_USERNAME=your_username
KIOTVIET_PASSWORD=your_password
KIOTVIET_RETAILER_ID=your_retailer_id
KIOTVIET_BRANCH_ID=your_branch_id
API_BASE_URL=https://api-man1.kiotviet.vn/api
DISPLAY=:99
```

### Service Configuration (/etc/systemd/system/kiotviet-integration.service)
```ini
[Unit]
Description=KiotViet Integration Service
After=network.target xvfb.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/kiotviet-integration
Environment=PATH=/home/pi/kiotviet-integration/venv/bin
Environment=DISPLAY=:99
ExecStart=/home/pi/kiotviet-integration/venv/bin/python scripts/kiotviet_run_all.py
Restart=always
RestartSec=30
```

## 📈 Monitoring & Maintenance

### Automated Monitoring
- Service health checks every 5 minutes
- Auto-restart on failures
- Log rotation and cleanup
- Status reporting in JSON format

### Manual Monitoring
```bash
# Real-time status
python remote_debug.py monitor

# Check recent activity
python remote_debug.py logs --lines 50

# System health
python remote_debug.py status
```

### Maintenance Tasks
- **Daily**: Token refresh (automated)
- **Weekly**: Log cleanup (automated)
- **Monthly**: System updates (manual)
- **As needed**: Application updates via Git

## 🚨 Emergency Procedures

### If Service Fails
1. Check status: `python remote_debug.py status`
2. View logs: `python remote_debug.py logs --follow`
3. Restart: `python remote_debug.py restart`
4. If still failing: `python remote_debug.py shell` for manual debugging

### If Token Expires
1. Generate new token: `python remote_debug.py token`
2. Check token file: `ssh pi@116.102.136.220 "cat /home/pi/kiotviet-integration/data/credentials/token.json"`
3. Restart service: `python remote_debug.py restart`

### If Pi Becomes Unresponsive
1. Physical reboot of Raspberry Pi
2. Wait 2-3 minutes for boot
3. Check services: `python remote_debug.py status`
4. Services should auto-start, if not: `python remote_debug.py restart`

## 📞 Support

For issues:
1. Check logs first: `python remote_debug.py logs`
2. Review this troubleshooting guide
3. Check GitHub issues: https://github.com/hhaiviet/kiotviet-integration/issues

---

**Target System**: Raspberry Pi 4 at `116.102.136.220`  
**Project Path**: `/home/pi/kiotviet-integration`  
**Services**: kiotviet-integration, kiotviet-monitor, xvfb  
**Schedule**: Every 2 hours, 24/7 operation