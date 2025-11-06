# 🍓 Raspberry Pi 4 Deployment Guide

Deploy KiotViet Integration to your Raspberry Pi 4 with IP `116.102.136.220`

## 🚀 Quick Deployment

### Option 1: Automated SSH Deployment (Recommended)

1. **From your Windows machine, run:**
```bash
bash deploy/deploy_to_pi.sh
```

2. **Follow the prompts to:**
   - Set up SSH keys
   - Upload files to Raspberry Pi
   - Install dependencies automatically

### Option 2: Manual SSH Deployment

1. **SSH to your Raspberry Pi:**
```bash
ssh pi@116.102.136.220
```

2. **Run the setup script:**
```bash
wget https://raw.githubusercontent.com/hhaiviet/kiotviet-integration/main/deploy/setup_raspberry_pi.sh
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

### Option 3: Docker Deployment

1. **SSH to your Raspberry Pi:**
```bash
ssh pi@116.102.136.220
```

2. **Clone and deploy with Docker:**
```bash
git clone https://github.com/hhaiviet/kiotviet-integration.git
cd kiotviet-integration
cp .env.example .env
# Edit .env with your credentials
nano .env
# Build and run
docker-compose up -d
```

## ⚙️ Configuration

### 1. Edit Environment Variables
```bash
ssh pi@116.102.136.220
cd ~/kiotviet-integration
nano .env
```

Fill in your KiotViet credentials:
```env
KIOTVIET_USERNAME=your_username
KIOTVIET_PASSWORD=your_password
KIOTVIET_RETAILER_ID=your_retailer_id
KIOTVIET_BRANCH_ID=your_branch_id
```

### 2. Generate Access Token
```bash
ssh pi@116.102.136.220
cd ~/kiotviet-integration
source venv/bin/activate
python scripts/kiotviet_auto_token_seleniumwire.py
```

## 🔧 Service Management

### Start/Stop Service
```bash
# Start service
sudo systemctl start kiotviet-integration

# Stop service
sudo systemctl stop kiotviet-integration

# Restart service
sudo systemctl restart kiotviet-integration

# Check status
sudo systemctl status kiotviet-integration
```

### View Logs
```bash
# Live logs
sudo journalctl -u kiotviet-integration -f

# Recent logs
sudo journalctl -u kiotviet-integration --no-pager -n 50
```

## 📊 Monitoring

### From Your Local Machine
```bash
# Monitor Pi status
bash deploy/monitor_pi.sh
```

### On Raspberry Pi
```bash
# Check service status
sudo systemctl status kiotviet-integration

# Check data files
ls -la ~/kiotviet-integration/data/

# Manual run
cd ~/kiotviet-integration
source venv/bin/activate
python scripts/kiotviet_run_all.py
```

## ⏰ Scheduled Execution

The service is configured to run every 6 hours automatically via cron:
```
0 */6 * * * cd /home/pi/kiotviet-integration && ./venv/bin/python scripts/kiotviet_run_all.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Chrome/Chromium not found:**
```bash
sudo apt install chromium-browser chromium-chromedriver
```

2. **Permission issues:**
```bash
sudo chown -R pi:pi ~/kiotviet-integration
chmod +x ~/kiotviet-integration/scripts/*.py
```

3. **Network connectivity:**
```bash
ping google.com
curl -I https://api-man1.kiotviet.vn/api
```

4. **Service not starting:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable kiotviet-integration
sudo systemctl start kiotviet-integration
```

### Debug Mode
```bash
cd ~/kiotviet-integration
source venv/bin/activate
python scripts/kiotviet_run_all.py --debug
```

## 📁 File Structure on Pi

```
/home/pi/kiotviet-integration/
├── scripts/                 # Python scripts
├── src/                     # Source code
├── data/
│   ├── output/             # Generated CSV files
│   ├── checkpoints/        # Sync checkpoints
│   ├── logs/               # Application logs
│   └── credentials/        # Token file
├── config/                 # Configuration files
├── .env                    # Environment variables
└── venv/                   # Python virtual environment
```

## 🌐 Network Requirements

- **Outbound HTTPS (443)** to:
  - `api-man1.kiotviet.vn`
  - `248minimart.kiotviet.vn`
  - `github.com` (for updates)
  
- **SSH (22)** for remote management

## 🔄 Updates

### Update Code
```bash
ssh pi@116.102.136.220
cd ~/kiotviet-integration
git pull origin main
sudo systemctl restart kiotviet-integration
```

### Update Dependencies
```bash
ssh pi@116.102.136.220
cd ~/kiotviet-integration
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart kiotviet-integration
```

## 📞 Support

For issues or questions:
1. Check logs: `sudo journalctl -u kiotviet-integration -f`
2. Run monitor script: `bash deploy/monitor_pi.sh`
3. Manual test: Run scripts individually to isolate issues