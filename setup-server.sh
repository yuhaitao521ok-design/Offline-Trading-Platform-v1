#!/bin/bash

# 服务器部署脚本
# 用途：自动配置后端、Nginx、系统服务等
# 使用：chmod +x setup-server.sh && ./setup-server.sh

set -e

BACKEND_PATH="/var/www/trading-platform/backend"
DIST_PATH="/var/www/trading-platform/dist"
DOMAIN="${1:-your_server_ip}"

echo "=========================================="
echo "   交易平台服务器部署脚本"
echo "=========================================="
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 此脚本需要 root 权限，请使用 sudo 运行"
    exit 1
fi

# 第一步：安装系统依赖
echo "📦 [1/5] 安装系统依赖..."
apt update
apt install -y python3 python3-pip python3-venv nginx || echo "⚠️  部分依赖安装失败"

# 第二步：配置 Python 虚拟环境
echo "🐍 [2/5] 配置 Python 虚拟环境..."
if [ -d "$BACKEND_PATH" ]; then
    cd "$BACKEND_PATH"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ 虚拟环境创建完成"
    fi
    
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        echo "📥 安装 Python 依赖..."
        pip install -r requirements.txt
        echo "✅ Python 依赖安装完成"
    else
        echo "⚠️  未找到 requirements.txt"
    fi
else
    echo "❌ 后端文件夹不存在：$BACKEND_PATH"
    exit 1
fi

# 第三步：配置 Nginx
echo "🌐 [3/5] 配置 Nginx..."
cat > /etc/nginx/sites-available/trading-platform << EOF
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN;

    # 日志
    access_log /var/log/nginx/trading-platform.access.log;
    error_log /var/log/nginx/trading-platform.error.log;

    # 静态文件服务（前端）
    location / {
        root $DIST_PATH;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
EOF

# 启用 Nginx 配置
if [ -L "/etc/nginx/sites-enabled/trading-platform" ]; then
    rm /etc/nginx/sites-enabled/trading-platform
fi
ln -s /etc/nginx/sites-available/trading-platform /etc/nginx/sites-enabled/

# 测试 Nginx 配置
if nginx -t; then
    systemctl restart nginx
    echo "✅ Nginx 配置完成"
else
    echo "❌ Nginx 配置有问题"
    exit 1
fi

# 第四步：创建系统服务
echo "⚙️  [4/5] 配置后端系统服务..."
cat > /etc/systemd/system/trading-backend.service << 'EOF'
[Unit]
Description=Trading Platform Backend
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/var/www/trading-platform/backend
ExecStart=/var/www/trading-platform/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 启用和启动服务
systemctl daemon-reload
systemctl enable trading-backend.service
systemctl start trading-backend.service
echo "✅ 后端服务配置完成"

# 第五步：验证
echo "✔️  [5/5] 验证部署..."
sleep 2

# 检查后端
if curl -s http://127.0.0.1:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端运行正常"
else
    echo "⚠️  后端可能未准备好，检查日志："
    echo "  journalctl -u trading-backend.service -n 20"
fi

# 检查 Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 运行正常"
else
    echo "❌ Nginx 未运行"
fi

# 检查前端
if [ -d "$DIST_PATH" ]; then
    echo "✅ 前端文件已部署"
else
    echo "⚠️  前端文件夹不存在：$DIST_PATH"
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "📍 访问地址："
echo "   http://$DOMAIN"
echo ""
echo "📋 常用命令："
echo "   查看后端状态：systemctl status trading-backend.service"
echo "   查看后端日志：journalctl -u trading-backend.service -f"
echo "   重启后端：systemctl restart trading-backend.service"
echo "   重启 Nginx：systemctl restart nginx"
echo ""
echo "更新代码后，重新部署前端："
echo "   在本地运行: npm run build"
echo "   上传 dist 文件夹到服务器"
echo "   重启 Nginx: systemctl restart nginx"
