#!/bin/bash

# KiotViet Integration - Raspberry Pi 4 Deployment Script
# Run this script on your Raspberry Pi 4

set -e

echo "🍓 Starting KiotViet Integration deployment on Raspberry Pi 4..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

# Install Chrome and ChromeDriver for Selenium
echo "🌐 Installing Chrome and ChromeDriver..."
sudo apt install -y chromium-browser chromium-chromedriver

# Install additional dependencies for Selenium
sudo apt install -y xvfb

# Create project directory
PROJECT_DIR="/home/$(whoami)/kiotviet-integration"
echo "📁 Creating project directory: $PROJECT_DIR"

# Clone repository if not exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/hhaiviet/kiotviet-integration.git "$PROJECT_DIR"
else
    echo "📥 Updating existing repository..."
    cd "$PROJECT_DIR"
    git pull origin main
fi

cd "$PROJECT_DIR"

# Create Python virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/output
mkdir -p data/checkpoints
mkdir -p data/logs
mkdir -p data/credentials

# Create Chrome profile directory
echo "🌐 Creating Chrome profile directory..."
mkdir -p /home/$(whoami)/chrome-profile

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your credentials:"
    echo "   nano .env"
fi

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/kiotviet-integration.service > /dev/null <<EOF
[Unit]
Description=KiotViet Integration Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python scripts/kiotviet_run_all.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create cron job for scheduled runs
echo "⏰ Setting up cron job..."
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $PROJECT_DIR && ./venv/bin/python scripts/kiotviet_run_all.py >> data/logs/cron.log 2>&1") | crontab -

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kiotviet-integration.service

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit environment file: nano $PROJECT_DIR/.env"
echo "2. Generate token: cd $PROJECT_DIR && source venv/bin/activate && python scripts/kiotviet_auto_token_seleniumwire.py"
echo "3. Start service: sudo systemctl start kiotviet-integration"
echo "4. Check status: sudo systemctl status kiotviet-integration"
echo "5. View logs: journalctl -u kiotviet-integration -f"
echo ""
echo "🔄 The service will run every 6 hours automatically"