# 🍓 KiotViet Integration - Raspberry Pi 4 Deployment

## 🚀 Quick Deploy (Windows PowerShell)

**Bước 1: Mở PowerShell trong thư mục project**
```powershell
cd "path\to\kiotviet-integration"
```

**Bước 2: Chạy deployment với credentials của bạn**
```powershell
# Cú pháp cơ bản
.\Deploy-ToRaspberryPi.ps1 -Username "your_username" -Password "your_password"

# Với RetailerId và BranchId (nếu có)
.\Deploy-ToRaspberryPi.ps1 -Username "your_username" -Password "your_password" -RetailerId "12345" -BranchId "67890"
```

**Ví dụ thực tế:**
```powershell
.\Deploy-ToRaspberryPi.ps1 -Username "john@248minimart.com" -Password "mypassword123" -RetailerId "248MM" -BranchId "MAIN"
```

## 🛠️ Remote Management (Sau khi deploy)

```powershell
# Kiểm tra trạng thái
python remote_debug.py status

# Xem logs real-time
python remote_debug.py logs --follow

# Restart service nếu có lỗi
python remote_debug.py restart

# Chạy sync thủ công
python remote_debug.py sync

# Generate token mới
python remote_debug.py token

# SSH vào Pi
python remote_debug.py shell
```

## 📋 Yêu cầu

### Trên máy tính Windows:
- ✅ Python 3.9+ (đã có)
- ✅ WSL hoặc Git Bash (sẽ tự check)
- ✅ SSH client (Windows 10+ có sẵn)
- ✅ Network access to 116.102.136.220

### Trên Raspberry Pi:
- ✅ SSH enabled (cần setup trước)
- ✅ Internet connection
- ✅ Đủ dung lượng ổ cứng (~2GB)

## 🔧 SSH Setup (Nếu chưa có)

**Trên Windows:**
```powershell
# Generate SSH key (nếu chưa có)
ssh-keygen -t rsa -b 4096

# Copy key to Pi
ssh-copy-id pi@116.102.136.220
# Hoặc thủ công:
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh pi@116.102.136.220 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

## ⚡ Deployment Process

Script sẽ tự động:

1. **✅ Validation** - Kiểm tra requirements
2. **📤 Upload** - Upload toàn bộ project lên Pi
3. **🔧 Setup** - Install Python, Chrome, dependencies
4. **🔑 Token** - Generate KiotViet access token
5. **🔄 Services** - Setup systemd services + monitoring
6. **⏰ Scheduling** - Cron jobs cho automation
7. **✅ Verification** - Test everything works

**Thời gian:** ~10-20 phút (tùy tốc độ mạng)

## 📊 Tự động hóa sau deployment

### Services chạy 24/7:
- **kiotviet-integration**: Main app service
- **kiotviet-monitor**: Health monitoring + auto-restart
- **xvfb**: Virtual display cho Selenium

### Scheduled tasks:
- **Data sync**: Mỗi 2 giờ
- **Token refresh**: Hằng ngày lúc 2 AM
- **Log cleanup**: Hằng tuần
- **Health check**: Mỗi 5 phút

## 🚨 Troubleshooting

### Lỗi SSH connection:
```powershell
# Test kết nối
ping 116.102.136.220
ssh pi@116.102.136.220 echo "test"
```

### Service không start:
```powershell
python remote_debug.py logs
python remote_debug.py restart
```

### Token generation failed:
```powershell
python remote_debug.py token
python remote_debug.py shell
# Trong Pi shell:
cd kiotviet-integration
source venv/bin/activate
python scripts/kiotviet_auto_token_enhanced.py
```

### Memory issues:
```powershell
python remote_debug.py status
python remote_debug.py shell
# Trong Pi shell:
free -h
sudo reboot
```

## 📞 Support Commands

```powershell
# Comprehensive status
python remote_debug.py status

# Real-time monitoring
python remote_debug.py monitor  

# Configuration review
python remote_debug.py config

# Update application
python remote_debug.py update

# Emergency shell access
python remote_debug.py shell
```

## 🎯 Success Indicators

Sau khi deploy thành công, bạn sẽ thấy:
- ✅ All services active
- ✅ Token file exists
- ✅ Cron jobs scheduled
- ✅ Data files created
- ✅ Logs working

## 📱 Next Steps

1. **Monitor first sync**: `python remote_debug.py logs --follow`
2. **Check output files**: SSH vào Pi và check `~/kiotviet-integration/data/output/`
3. **Setup Azure Blob** (optional): Edit .env trên Pi
4. **Monitor regularly**: `python remote_debug.py status`

---

**🎉 Sau khi chạy xong, KiotViet integration sẽ tự động sync data từ KiotViet API mỗi 2 giờ, 24/7!**