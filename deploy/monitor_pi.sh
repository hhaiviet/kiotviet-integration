#!/bin/bash

# KiotViet Integration - Monitoring Script for Raspberry Pi
# This script monitors the service and provides status information

PI_IP="116.102.136.220"
PI_USER="pi"

echo "🍓 KiotViet Integration - Raspberry Pi Monitor"
echo "=============================================="

# Function to run command on Pi
run_on_pi() {
    ssh $PI_USER@$PI_IP "$1"
}

# Check if we can connect
echo "🔍 Testing connection to $PI_IP..."
if ! run_on_pi "echo 'Connected'" > /dev/null 2>&1; then
    echo "❌ Cannot connect to Raspberry Pi"
    echo "💡 Make sure:"
    echo "   - Raspberry Pi is powered on"
    echo "   - Network connection is working"
    echo "   - SSH is enabled on the Pi"
    exit 1
fi
echo "✅ Connected to Raspberry Pi"

echo ""
echo "📊 System Status:"
echo "================"
run_on_pi "uptime"
run_on_pi "free -h"
run_on_pi "df -h | grep -E 'Filesystem|/$'"

echo ""
echo "🔧 KiotViet Service Status:"
echo "=========================="
run_on_pi "sudo systemctl status kiotviet-integration --no-pager" || echo "Service not found"

echo ""
echo "📝 Recent Logs (last 20 lines):"
echo "================================"
run_on_pi "sudo journalctl -u kiotviet-integration --no-pager -n 20" || echo "No logs found"

echo ""
echo "📁 Data Directory:"
echo "=================="
run_on_pi "ls -la ~/kiotviet-integration/data/" || echo "Data directory not found"

echo ""
echo "⏰ Cron Jobs:"
echo "============"
run_on_pi "crontab -l" || echo "No cron jobs found"

echo ""
echo "🌐 Network Status:"
echo "=================="
run_on_pi "curl -s -o /dev/null -w '%{http_code}' https://api-man1.kiotviet.vn/api/health || echo 'API not reachable'"

echo ""
echo "💾 Last Token Update:"
echo "===================="
run_on_pi "ls -la ~/kiotviet-integration/data/credentials/token.json" || echo "Token file not found"

echo ""
echo "📋 Available Commands:"
echo "====================="
echo "🔄 Restart service: ssh $PI_USER@$PI_IP 'sudo systemctl restart kiotviet-integration'"
echo "📊 View logs: ssh $PI_USER@$PI_IP 'sudo journalctl -u kiotviet-integration -f'"
echo "🔧 Edit config: ssh $PI_USER@$PI_IP 'nano ~/kiotviet-integration/.env'"
echo "🏃 Manual run: ssh $PI_USER@$PI_IP 'cd ~/kiotviet-integration && source venv/bin/activate && python scripts/kiotviet_run_all.py'"