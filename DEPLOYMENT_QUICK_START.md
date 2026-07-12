# 部署快速参考

## 📋 部署检查清单

### 本地准备（Windows 开发机）

- [ ] 确认项目文件完整
- [ ] 运行 `npm run build` 生成前端构建
- [ ] 确认 `backend/requirements.txt` 包含所有依赖
- [ ] 准备服务器访问信息（IP 或域名、SSH 密钥）

### 服务器准备（假设 Linux Ubuntu）

- [ ] 服务器已联网且能访问外网（安装 npm/pip 包）
- [ ] 已安装 SSH（用于上传文件）
- [ ] 记录服务器 IP 地址
- [ ] 准备好 SSH 密钥或密码

### 部署步骤

- [ ] 上传前端构建文件到 `/var/www/trading-platform/dist`
- [ ] 上传后端代码到 `/var/www/trading-platform/backend`
- [ ] 在服务器上运行 `setup-server.sh`
- [ ] 测试访问：`http://your_server_ip`
- [ ] 测试 API：`curl http://your_server_ip/api/stock/search?keyword=AAPL`

---

## 🚀 三步快速部署

### 第 1 步：本地构建前端（Windows CMD 或 PowerShell）

```powershell
# 进入前端目录
cd "d:\AI_Projects\Offline Trading Platform\frontend"

# 安装依赖并构建
npm install
npm run build

# 输出：dist 文件夹已生成
```

### 第 2 步：上传文件到服务器

**如果使用 PowerShell（Windows）：**

```powershell
# 上传前端（dist 文件夹）
$serverIP = "your_server_ip"
scp -r "d:\AI_Projects\Offline Trading Platform\frontend\dist" "root@$($serverIP):/var/www/trading-platform/"

# 上传后端
scp -r "d:\AI_Projects\Offline Trading Platform\backend" "root@$($serverIP):/var/www/trading-platform/"

# 上传部署脚本
scp "d:\AI_Projects\Offline Trading Platform\setup-server.sh" "root@$($serverIP):/tmp/"
```

**如果使用 SSH 连接到服务器后（Linux）：**

```bash
cd /var/www/trading-platform
# 创建目录
mkdir -p /var/www/trading-platform
```

### 第 3 步：在服务器上运行部署脚本

```bash
# SSH 连接到服务器
ssh root@your_server_ip

# 进入脚本所在目录
cd /tmp

# 运行部署脚本
chmod +x setup-server.sh
./setup-server.sh

# 或者指定域名（如果有）
./setup-server.sh your_domain.com
```

---

## 🐛 常见问题及解决方案

### Q1: 上传文件时 SCP 命令报错

**问题：**`Permission denied` 或 `不能连接到服务器`

**解决：**

- 检查 IP 地址是否正确
- 确认 SSH 服务在服务器上运行：`systemctl status ssh`
- 如果使用密钥，检查密钥权限：`chmod 600 /path/to/key`

### Q2: `npm: 无法识别的命令`

**问题：** Windows 上 npm 不可用

**解决：**

- 下载安装 Node.js：https://nodejs.org/
- 重启 PowerShell 或 CMD

### Q3: 后端启动失败 - `ModuleNotFoundError`

**问题：** Python 模块未找到

**解决：**

```bash
cd /var/www/trading-platform/backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart trading-backend.service
```

### Q4: 访问 `http://your_server_ip` 得到 502 Bad Gateway

**问题：** Nginx 无法连接到后端

**解决：**

```bash
# 检查后端服务状态
systemctl status trading-backend.service

# 查看详细错误日志
journalctl -u trading-backend.service -n 50

# 手动测试后端
curl http://127.0.0.1:8000/docs
```

### Q5: API 调用返回 CORS 错误

**问题：** 跨域资源共享限制

**解决：**
修改 `backend/app/main.py`：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为 ["http://your_domain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

然后重启后端：

```bash
systemctl restart trading-backend.service
```

---

## 📊 部署后的日常维护

### 查看日志

```bash
# 查看后端日志（实时）
journalctl -u trading-backend.service -f

# 查看后端日志（最后 50 行）
journalctl -u trading-backend.service -n 50

# 查看 Nginx 访问日志
tail -f /var/log/nginx/trading-platform.access.log

# 查看 Nginx 错误日志
tail -f /var/log/nginx/trading-platform.error.log
```

### 重启服务

```bash
# 重启后端
systemctl restart trading-backend.service

# 重启 Nginx
systemctl restart nginx

# 重启所有服务
systemctl restart trading-backend.service && systemctl restart nginx
```

### 更新代码

```bash
# 更新后端
cd /var/www/trading-platform/backend
source venv/bin/activate
git pull  # 如果使用 git
pip install -r requirements.txt
systemctl restart trading-backend.service

# 更新前端（本地）
cd d:\AI_Projects\Offline Trading Platform\frontend
git pull
npm install
npm run build

# 上传新的 dist 文件夹
scp -r dist root@your_server_ip:/var/www/trading-platform/

# Nginx 自动重新加载（或手动）
systemctl restart nginx
```

### 监控服务器健康

```bash
# 检查磁盘使用情况
df -h

# 检查内存使用情况
free -h

# 检查 CPU 使用情况
top

# 检查服务运行状态
systemctl status trading-backend.service
systemctl status nginx
```

---

## 🔒 生产环境建议

### 1. 使用 HTTPS（Let's Encrypt 免费证书）

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your_domain.com
systemctl enable certbot.timer
```

### 2. 配置防火墙

```bash
# 只允许必要的端口
ufw enable
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
```

### 3. 设置备份

```bash
# 定期备份数据库和配置文件
0 2 * * * tar -czf /backup/trading-$(date +\%Y\%m\%d).tar.gz /var/www/trading-platform
```

### 4. 监控和告警

- 安装 monitoring 工具（Prometheus + Grafana）
- 配置 log aggregation（ELK Stack）
- 设置告警规则

---

## 📞 需要帮助？

如果遇到问题：

1. 查看相关日志：`journalctl` 或 Nginx 日志
2. 确认所有依赖都已安装
3. 检查网络连接和防火墙规则
4. 参考 DEPLOYMENT_GUIDE.md 的完整指南
