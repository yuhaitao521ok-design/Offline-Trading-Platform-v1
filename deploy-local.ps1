# 本地构建和上传脚本（Windows PowerShell）
# 用途：一键构建前端、准备后端，并上传到服务器
# 使用：在 PowerShell 中运行：.\deploy-local.ps1

param(
    [string]$ServerIP = "your_server_ip",
    [string]$ServerUser = "root"
)

$ProjectRoot = "d:\AI_Projects\Offline Trading Platform"
$Frontend = "$ProjectRoot\frontend"
$Backend = "$ProjectRoot\backend"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   交易平台本地构建和上传脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查参数
if ($ServerIP -eq "your_server_ip") {
    Write-Host "❌ 请提供服务器 IP 地址" -ForegroundColor Red
    Write-Host "使用方法：.\deploy-local.ps1 -ServerIP 192.168.1.100" -ForegroundColor Yellow
    exit 1
}

# 步骤 1: 检查环境
Write-Host "🔍 [1/4] 检查环境..." -ForegroundColor Cyan
$checks = @()

# 检查 Node.js
$nodeCheck = (node -v 2>$null)
if ($nodeCheck) {
    Write-Host "  ✅ Node.js: $nodeCheck" -ForegroundColor Green
} else {
    Write-Host "  ❌ Node.js 未找到" -ForegroundColor Red
    exit 1
}

# 检查 npm
$npmCheck = (npm -v 2>$null)
if ($npmCheck) {
    Write-Host "  ✅ npm: $npmCheck" -ForegroundColor Green
} else {
    Write-Host "  ❌ npm 未找到" -ForegroundColor Red
    exit 1
}

# 检查项目目录
if ((Test-Path $Frontend) -and (Test-Path $Backend)) {
    Write-Host "  ✅ 项目目录存在" -ForegroundColor Green
} else {
    Write-Host "  ❌ 项目目录不存在" -ForegroundColor Red
    exit 1
}

# 步骤 2: 构建前端
Write-Host ""
Write-Host "🏗️  [2/4] 构建前端..." -ForegroundColor Cyan

try {
    Push-Location $Frontend
    
    Write-Host "  📥 安装依赖..." -ForegroundColor Yellow
    npm install 2>&1 | ForEach-Object { Write-Host "     $_" }
    
    Write-Host "  🔨 构建项目..." -ForegroundColor Yellow
    npm run build 2>&1 | ForEach-Object { Write-Host "     $_" }
    
    if (Test-Path "$Frontend\dist") {
        Write-Host "  ✅ 前端构建成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 构建失败：dist 文件夹未生成" -ForegroundColor Red
        exit 1
    }
    
    Pop-Location
} catch {
    Write-Host "  ❌ 构建失败：$_" -ForegroundColor Red
    exit 1
}

# 步骤 3: 准备后端
Write-Host ""
Write-Host "📦 [3/4] 检查后端..." -ForegroundColor Cyan

if (Test-Path "$Backend\requirements.txt") {
    Write-Host "  ✅ requirements.txt 存在" -ForegroundColor Green
} else {
    Write-Host "  ❌ requirements.txt 未找到" -ForegroundColor Red
    exit 1
}

# 步骤 4: 上传到服务器
Write-Host ""
Write-Host "📤 [4/4] 上传文件到服务器..." -ForegroundColor Cyan

try {
    $distSource = "$Frontend\dist"
    $backendSource = "$Backend"
    $target = "${ServerUser}@${ServerIP}:/var/www/trading-platform"
    
    Write-Host "  📁 上传前端 (dist)..." -ForegroundColor Yellow
    Write-Host "     scp -r `"$distSource`" `"$target/`"" -ForegroundColor Gray
    scp -r "$distSource" "$target/" 2>&1 | ForEach-Object { Write-Host "     $_" }
    
    Write-Host "  📁 上传后端..." -ForegroundColor Yellow
    Write-Host "     scp -r `"$backendSource`" `"$target/`"" -ForegroundColor Gray
    scp -r "$backendSource" "$target/" 2>&1 | ForEach-Object { Write-Host "     $_" }
    
    Write-Host "  ✅ 文件上传完成" -ForegroundColor Green
    
} catch {
    Write-Host "  ❌ 上传失败：$_" -ForegroundColor Red
    exit 1
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 本地构建和上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "下一步，在服务器上运行部署脚本：" -ForegroundColor Yellow
Write-Host "  ssh root@$ServerIP" -ForegroundColor Cyan
Write-Host "  chmod +x /tmp/setup-server.sh" -ForegroundColor Cyan
Write-Host "  /tmp/setup-server.sh $ServerIP" -ForegroundColor Cyan
Write-Host ""

Write-Host "或者复制以下命令在本地 PowerShell 中运行：" -ForegroundColor Yellow
Write-Host "  ssh root@$ServerIP 'chmod +x /tmp/setup-server.sh && /tmp/setup-server.sh'" -ForegroundColor Cyan
