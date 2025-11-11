# KiotViet Integration - PowerShell Deployment Script for Windows
# This script handles deployment from Windows to Raspberry Pi 4

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$false)]
    [string]$RetailerId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$BranchId = ""
)

# Colors for PowerShell output
$Red = "Red"
$Green = "Green" 
$Yellow = "Yellow"
$Blue = "Cyan"
$Purple = "Magenta"

function Write-Log {
    param([string]$Message, [string]$Color = $Blue)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor $Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️ $Message" -ForegroundColor $Blue
}

# Configuration
$PI_IP = "116.102.136.220"
$PI_USER = "pi"
$PROJECT_NAME = "kiotviet-integration"

Write-Log "🚀 Starting KiotViet Integration deployment to Raspberry Pi 4..." $Purple
Write-Log "📡 Target: $PI_USER@$PI_IP" $Blue
Write-Log "👤 KiotViet User: $Username" $Blue

# Check if we're in the correct directory
$CurrentDir = Get-Location
if (-not (Test-Path ".\deploy\fully_automated_deploy.sh")) {
    Write-Error "Please run this script from the kiotviet-integration project root directory"
    Write-Info "Current directory: $CurrentDir"
    Write-Info "Expected files: .\deploy\fully_automated_deploy.sh"
    exit 1
}

# Update .env file with provided credentials
Write-Log "⚙️ Creating environment configuration..." $Blue

$envContent = @"
# KiotViet Credentials - Auto-generated $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
KIOTVIET_USERNAME=$Username
KIOTVIET_PASSWORD=$Password
KIOTVIET_RETAILER_ID=$RetailerId
KIOTVIET_BRANCH_ID=$BranchId

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

# Remote monitoring
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_PORT=8080
"@

Set-Content -Path ".env" -Value $envContent
Write-Success "Environment configuration created"

# Test SSH connectivity
Write-Log "🔍 Testing SSH connection..." $Blue
try {
    $sshTest = ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$PI_USER@$PI_IP" "echo 'SSH OK'" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "SSH connection successful"
    } else {
        Write-Warning "SSH connection test failed - continuing anyway"
        Write-Info "You may need to setup SSH keys or check network connectivity"
    }
} catch {
    Write-Warning "SSH test failed: $($_.Exception.Message)"
}

# Check for required tools
Write-Log "🛠️ Checking deployment tools..." $Blue

# Check for WSL or Git Bash
$bashFound = $false
$deployCommand = ""

# Try WSL first
try {
    wsl --list --quiet | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "WSL detected - using WSL for deployment"
        $bashFound = $true
        if ([string]::IsNullOrEmpty($RetailerId) -or [string]::IsNullOrEmpty($BranchId)) {
            $deployCommand = "wsl bash deploy/fully_automated_deploy.sh `"$Username`" `"$Password`""
        } else {
            $deployCommand = "wsl bash deploy/fully_automated_deploy.sh `"$Username`" `"$Password`" `"$RetailerId`" `"$BranchId`""
        }
    }
} catch {
    Write-Info "WSL not available"
}

# Try Git Bash if WSL not available
if (-not $bashFound) {
    $gitBashPaths = @(
        "${env:ProgramFiles}\Git\bin\bash.exe",
        "${env:ProgramFiles(x86)}\Git\bin\bash.exe",
        "${env:LOCALAPPDATA}\Programs\Git\bin\bash.exe"
    )
    
    foreach ($bashPath in $gitBashPaths) {
        if (Test-Path $bashPath) {
            Write-Success "Git Bash found at: $bashPath"
            $bashFound = $true
            if ([string]::IsNullOrEmpty($RetailerId) -or [string]::IsNullOrEmpty($BranchId)) {
                $deployCommand = "`"$bashPath`" deploy/fully_automated_deploy.sh `"$Username`" `"$Password`""
            } else {
                $deployCommand = "`"$bashPath`" deploy/fully_automated_deploy.sh `"$Username`" `"$Password`" `"$RetailerId`" `"$BranchId`""
            }
            break
        }
    }
}

if (-not $bashFound) {
    Write-Error "Neither WSL nor Git Bash found"
    Write-Info "Please install one of the following:"
    Write-Info "  1. WSL (Windows Subsystem for Linux): https://docs.microsoft.com/en-us/windows/wsl/install"
    Write-Info "  2. Git for Windows (includes Git Bash): https://git-scm.com/download/win"
    Write-Info ""
    Write-Info "Alternative: Manual PowerShell deployment (experimental):"
    Write-Info "  python remote_debug.py shell"
    exit 1
}

# Run pre-deployment check
Write-Log "🔍 Running pre-deployment validation..." $Blue
try {
    python pre_deploy_check.py
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Pre-deployment check found issues, but continuing..."
    }
} catch {
    Write-Warning "Could not run pre-deployment check: $($_.Exception.Message)"
}

# Execute deployment
Write-Log "🚀 Starting deployment process..." $Purple
Write-Info "Command: $deployCommand"
Write-Info "This may take 10-20 minutes depending on network speed and Pi performance..."

try {
    Invoke-Expression $deployCommand
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment completed successfully!"
    } else {
        Write-Error "Deployment failed with exit code: $LASTEXITCODE"
        Write-Info "Check the output above for error details"
        exit 1
    }
} catch {
    Write-Error "Deployment execution failed: $($_.Exception.Message)"
    exit 1
}

# Post-deployment verification
Write-Log "🔍 Running post-deployment verification..." $Blue
Start-Sleep -Seconds 5

try {
    python remote_debug.py status
    Write-Success "Post-deployment check completed"
} catch {
    Write-Warning "Could not run post-deployment check: $($_.Exception.Message)"
    Write-Info "You can manually check status with: python remote_debug.py status"
}

# Show completion summary
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Purple
Write-Host "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor $Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Purple
Write-Host ""
Write-Host "🎯 Target: $PI_USER@$PI_IP" -ForegroundColor $Blue
Write-Host "👤 KiotViet User: $Username" -ForegroundColor $Blue
Write-Host "📁 Project Path: /home/$PI_USER/$PROJECT_NAME" -ForegroundColor $Blue
Write-Host ""
Write-Host "🛠️ Remote Management Commands:" -ForegroundColor $Yellow
Write-Host "  python remote_debug.py status    - Check system status" -ForegroundColor $Blue
Write-Host "  python remote_debug.py logs      - View application logs" -ForegroundColor $Blue
Write-Host "  python remote_debug.py restart   - Restart services" -ForegroundColor $Blue
Write-Host "  python remote_debug.py shell     - Open SSH shell" -ForegroundColor $Blue
Write-Host "  python remote_debug.py monitor   - Monitoring dashboard" -ForegroundColor $Blue
Write-Host ""
Write-Host "⏰ The system will automatically:" -ForegroundColor $Green
Write-Host "  • Sync data every 2 hours" -ForegroundColor $Blue
Write-Host "  • Refresh tokens daily at 2 AM" -ForegroundColor $Blue
Write-Host "  • Monitor and restart services if needed" -ForegroundColor $Blue
Write-Host "  • Clean up old logs weekly" -ForegroundColor $Blue
Write-Host ""
Write-Host "🆘 If you need help:" -ForegroundColor $Yellow
Write-Host "  1. Check logs: python remote_debug.py logs --follow" -ForegroundColor $Blue
Write-Host "  2. Restart if needed: python remote_debug.py restart" -ForegroundColor $Blue
Write-Host "  3. Manual sync: python remote_debug.py sync" -ForegroundColor $Blue
Write-Host ""
Write-Host "Your KiotViet integration is now running 24/7! 🚀" -ForegroundColor $Green