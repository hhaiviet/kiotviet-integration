#!/bin/bash

# Deploy KiotViet Integration to Raspberry Pi 4
# Run this script from your local machine

set -e

# Configuration
PI_IP="116.102.136.220"
PI_USER="pi"  # Change this to your Raspberry Pi username
PROJECT_NAME="kiotviet-integration"

echo "🚀 Deploying KiotViet Integration to Raspberry Pi 4..."
echo "📡 Target: $PI_USER@$PI_IP"

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "🔑 SSH key not found. Generating new SSH key..."
    ssh-keygen -t rsa -b 4096 -C "deployment@kiotviet"
    echo "📤 Copy this public key to your Raspberry Pi:"
    cat ~/.ssh/id_rsa.pub
    echo ""
    echo "Run this on your Raspberry Pi:"
    echo "mkdir -p ~/.ssh && echo 'YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
    read -p "Press Enter when SSH key is configured..."
fi

# Test SSH connection
echo "🔍 Testing SSH connection..."
ssh -o ConnectTimeout=10 $PI_USER@$PI_IP "echo 'SSH connection successful'"

# Create deployment package
echo "📦 Creating deployment package..."
TEMP_DIR=$(mktemp -d)
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' --exclude='data' . $TEMP_DIR/

# Upload files to Raspberry Pi
echo "📤 Uploading files to Raspberry Pi..."
ssh $PI_USER@$PI_IP "mkdir -p ~/$PROJECT_NAME"
rsync -av --delete $TEMP_DIR/ $PI_USER@$PI_IP:~/$PROJECT_NAME/

# Run deployment script on Raspberry Pi
echo "🔧 Running deployment on Raspberry Pi..."
ssh $PI_USER@$PI_IP "cd ~/$PROJECT_NAME && chmod +x deploy/setup_raspberry_pi.sh && ./deploy/setup_raspberry_pi.sh"

# Copy environment variables (if .env exists locally)
if [ -f ".env" ]; then
    echo "⚙️  Uploading environment configuration..."
    scp .env $PI_USER@$PI_IP:~/$PROJECT_NAME/.env
fi

# Cleanup
rm -rf $TEMP_DIR

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps on Raspberry Pi ($PI_IP):"
echo "1. SSH to Pi: ssh $PI_USER@$PI_IP"
echo "2. Edit config: nano ~/$PROJECT_NAME/.env"
echo "3. Generate token: cd ~/$PROJECT_NAME && source venv/bin/activate && python scripts/kiotviet_auto_token_seleniumwire.py"
echo "4. Start service: sudo systemctl start kiotviet-integration"
echo "5. Check logs: journalctl -u kiotviet-integration -f"
echo ""
echo "🌐 Service will be available and running automatically!"