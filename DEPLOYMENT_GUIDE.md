# 服务器部署指南

## 项目架构

- **前端**：Vue 3 + TypeScript + Vite（静态网站）
- **后端**：FastAPI + Python（API 服务器）
- **Web 服务器**：Nginx（反向代理 + 静态文件服务）

## 前置条件

- 已购买服务器（假设 Linux 系统，推荐 Ubuntu 20.04+）
- 有服务器的 SSH 访问权限
- 服务器已安装：Python 3.9+、Node.js 18+、Nginx

---

## 第一步：服务器基础配置

### 1.1 连接到服务器

```bash
ssh root@your_server_ip
# 或使用密钥
ssh -i /path/to/key root@your_server_ip
```

### 1.2 更新系统并安装必要工具

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nodejs npm nginx git wget curl
```

### 1.3 创建项目目录

```bash
mkdir -p /var/www/trading-platform
cd /var/www/trading-platform
```

---

## 第二步：本地构建前端

### 2.1 在你的开发机器上构建前端

```bash
cd d:\AI_Projects\Offline Trading Platform\frontend
npm install
npm run build
```

这会生成 `dist` 文件夹，包含所有静态文件。

### 2.2 将前端文件上传到服务器

**方式 A：使用 SCP（最简单）**

```bash
scp -r d:\AI_Projects\Offline Trading Platform\frontend\dist root@your_server_ip:/var/www/trading-platform/
```

**方式 B：使用 SFTP 或 WinSCP（Windows 用户友好）**
使用 WinSCP 连接服务器，将 `frontend/dist` 文件夹拖到 `/var/www/trading-platform/`

---

## 第三步：服务器后端配置

### 3.1 上传后端代码

```bash
# 在服务器上
cd /var/www/trading-platform
# 创建后端目录
mkdir backend
```

将本地 `backend` 文件夹上传到服务器的 `/var/www/trading-platform/backend`：

```bash
scp -r d:\AI_Projects\Offline Trading Platform\backend root@your_server_ip:/var/www/trading-platform/
```

### 3.2 安装 Python 依赖

```bash
cd /var/www/trading-platform/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3.3 测试后端是否正常

```bash
# 仍在虚拟环境中
cd /var/www/trading-platform/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

你应该看到 Uvicorn 服务器启动的日志。按 Ctrl+C 停止。

---

## 第四步：配置 Nginx

### 4.1 创建 Nginx 配置文件

```bash
cat > /etc/nginx/sites-available/trading-platform << 'EOF'
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your_server_ip;  # 或你的域名

    # 静态文件服务（前端）
    location / {
        root /var/www/trading-platform/dist;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由支持
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
EOF
```

### 4.2 启用配置并测试

```bash
# 创建软链接
ln -s /etc/nginx/sites-available/trading-platform /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

---

## 第五步：设置后端为系统服务（自动启动）

### 5.1 创建 Systemd 服务文件

```bash
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

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 启用并启动服务

```bash
# 重新加载 systemd
systemctl daemon-reload

# 启用开机自启
systemctl enable trading-backend.service

# 启动服务
systemctl start trading-backend.service

# 查看状态
systemctl status trading-backend.service
```

---

## 第六步：验证部署

### 6.1 检查后端是否运行

```bash
curl http://127.0.0.1:8000/health
```

如果项目有健康检查端点，应该看到成功响应。

### 6.2 访问前端

打开浏览器访问：

```
http://your_server_ip
```

### 6.3 测试 API 调用

```bash
curl http://your_server_ip/api/stock/search?keyword=AAPL
```

---

## 第七步：配置 HTTPS（可选但推荐）

### 7.1 安装 Let's Encrypt 证书

```bash
apt install -y certbot python3-certbot-nginx

# 申请证书（需要域名）
certbot --nginx -d your_domain.com
```

### 7.2 配置自动续期

```bash
systemctl enable certbot.timer
systemctl start certbot.timer
```

---

## 故障排查

### 问题 1：后端无法连接到数据源

- 检查 `backend/app/core/config.py` 的数据源配置
- 确保能访问 yfinance 和 akshare 的数据源

### 问题 2：Nginx 返回 502 Bad Gateway

```bash
# 检查后端是否运行
systemctl status trading-backend.service

# 查看后端日志
journalctl -u trading-backend.service -n 50
```

### 问题 3：前端 API 调用返回 CORS 错误

修改后端的 CORS 配置（`backend/app/main.py`）：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该改为具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 更新项目代码

### 更新前端

```bash
cd /var/www/trading-platform/frontend
npm install
npm run build
# 覆盖 dist 文件夹或新建 dist 并替换
```

### 更新后端

```bash
cd /var/www/trading-platform/backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart trading-backend.service
```

---

## 生产环境优化建议

1. **使用独立的应用用户**（而不是 root）
2. **配置日志系统**：使用 systemd journal 或 ELK Stack
3. **设置监控**：使用 Prometheus + Grafana
4. **使用进程管理器**：Gunicorn + Supervisor 替代 Uvicorn
5. **配置数据库备份**
6. **使用 CDN** 加速静态资源
7. **配置 WAF** 和防火墙规则
