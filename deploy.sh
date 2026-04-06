#!/bin/bash
# CyberGate 一键部署脚本 - Ubuntu
# 用法: bash deploy.sh [服务器IP]
# 示例: bash deploy.sh 45.207.215.17

set -e

SERVER_IP=${1:-"your_server_ip"}
DOMAIN="http://$SERVER_IP"

echo "======================================"
echo "  CyberGate 部署脚本"
echo "  目标服务器: $SERVER_IP"
echo "======================================"

# ── 1. 系统依赖 ────────────────────────────────────────────────
echo "[1/6] 安装系统依赖..."
apt-get update -qq
apt-get install -y python3 python3-pip nodejs npm nginx git curl wget

# ── 2. 克隆代码 ────────────────────────────────────────────────
echo "[2/6] 拉取代码..."
cd /opt
if [ -d "cybergate" ]; then
    cd cybergate && git pull
else
    git clone https://github.com/Killjat/cybergate.git
    cd cybergate
fi

# ── 3. 后端依赖 ────────────────────────────────────────────────
echo "[3/6] 安装后端依赖..."
cd /opt/cybergate/backend
pip3 install -r requirements.txt

# 修改后端 CORS 允许服务器 IP
sed -i "s|http://localhost:3000|http://$SERVER_IP|g" main.py

# ── 4. 前端构建 ────────────────────────────────────────────────
echo "[4/6] 构建前端..."
cd /opt/cybergate/frontend
REACT_APP_API_URL="http://$SERVER_IP:8080" npm install --silent
REACT_APP_API_URL="http://$SERVER_IP:8080" npm run build

# ── 5. 配置 Nginx ──────────────────────────────────────────────
echo "[5/6] 配置 Nginx..."
cat > /etc/nginx/sites-available/cybergate << EOF
server {
    listen 80;
    server_name $SERVER_IP;

    # 前端静态文件
    root /opt/cybergate/frontend/build;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cybergate /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── 6. 配置 systemd 服务 ───────────────────────────────────────
echo "[6/6] 配置后端服务..."
cat > /etc/systemd/system/cybergate.service << EOF
[Unit]
Description=CyberGate Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cybergate/backend
ExecStart=/usr/bin/python3 -c "
import uvicorn, asyncio, sys
sys.path.insert(0, '.')
from main import app
async def run():
    config = uvicorn.Config(app, host='127.0.0.1', port=8080)
    await uvicorn.Server(config).serve()
asyncio.run(run())
"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cybergate
systemctl restart cybergate

# ── 完成 ───────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  部署完成！"
echo "  访问地址: http://$SERVER_IP"
echo "  后端 API: http://$SERVER_IP/api"
echo ""
echo "  查看后端日志: journalctl -u cybergate -f"
echo "  重启后端:     systemctl restart cybergate"
echo "======================================"
