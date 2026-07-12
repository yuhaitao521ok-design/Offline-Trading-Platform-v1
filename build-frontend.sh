#!/bin/bash

# 本地快速构建脚本
# 用途：构建前端，准备部署

set -e

echo "🔨 开始构建前端..."
cd "$(dirname "$0")/frontend"

# 检查 Node.js
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装。请先安装 Node.js"
    exit 1
fi

# 安装依赖
echo "📦 安装 npm 依赖..."
npm install

# 构建
echo "🏗️  构建前端项目..."
npm run build

echo "✅ 前端构建完成！"
echo ""
echo "📁 构建输出目录：$(pwd)/dist"
echo ""
echo "下一步：将 dist 文件夹上传到服务器"
echo "  scp -r dist root@your_server_ip:/var/www/trading-platform/"
