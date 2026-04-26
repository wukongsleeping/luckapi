#!/bin/bash
# ================================
# LuckApi 自动上传部署脚本
# ================================
# 用法:
#   bash upload.sh              # 上传全部文件并部署
#   bash upload.sh deploy       # 仅执行远程部署（跳过上传）
#   bash upload.sh migrate      # 仅执行数据库备份和迁移
# ================================

set -e

# ---------- 配置 ----------
SERVER_HOST="49.235.160.154"
SERVER_USER="ubuntu"
SERVER_PATH="/home/ubuntu/python"
DOMAIN="your-domain.com"
MYSQL_DB_PASSWORD="fendou123"
REDIS_PASSWORD="ChangeMeSecureRedisPassword"
SERVER_PASSWORD="${SERVER_PASSWORD:-}"  # 从环境变量读取，或手动填入

# SSH 认证配置（支持密钥或密码）
SSH_CMD() {
    local target="$1"; shift
    local ssh_args="-T -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 $target $@"
    if [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "${SERVER_PASSWORD}" ssh $ssh_args
    else
        ssh $ssh_args
    fi
}

# 当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ---------- 函数 ----------

log_info() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1" >&2
}

log_step() {
    echo ""
    echo "━━━ $1 ━━━"
}

# 上传文件到服务器
upload_files() {
    log_step "上传项目文件到服务器..."
    
    if [ -n "$SERVER_PASSWORD" ]; then
        SSHPASS="$SERVER_PASSWORD" sshpass -e rsync -avz --delete \
            -e "ssh -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60" \
            --exclude='.git/' \
            --exclude='node_modules/' \
            --exclude='backend/__pycache__/' \
            --exclude='backend/venv/' \
            --exclude='backend/.venv/' \
            --exclude='frontend/dist/' \
            --exclude='.env' \
            --exclude='*.pyc' \
            --exclude='__pycache__/' \
            --exclude='backend/.pytest_cache/' \
            --exclude='backend/.ruff_cache/' \
            --exclude='*.sh' \
            --exclude='migrate.sh' \
            "$PROJECT_ROOT/" \
            "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
    else
        rsync -avz --delete \
            -e "ssh -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60" \
            --exclude='.git/' \
            --exclude='node_modules/' \
            --exclude='backend/__pycache__/' \
            --exclude='backend/venv/' \
            --exclude='backend/.venv/' \
            --exclude='frontend/dist/' \
            --exclude='.env' \
            --exclude='*.pyc' \
            --exclude='__pycache__/' \
            --exclude='backend/.pytest_cache/' \
            --exclude='backend/.ruff_cache/' \
            --exclude='*.sh' \
            --exclude='migrate.sh' \
            "$PROJECT_ROOT/" \
            "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/"
    fi \
    
    log_step "文件上传完成"
}

# 在服务器上执行部署命令
remote_deploy() {
    log_step "在服务器上执行部署..."
    
    if [ -n "$SERVER_PASSWORD" ]; then
        export SSHPASS="$SERVER_PASSWORD"
    fi
    
    sshpass -e ssh -T -o StrictHostKeyChecking=no -o TCPKeepAlive=yes -o ServerAliveInterval=60 \
        "${SERVER_USER}@${SERVER_HOST}" << 'REMOTE_SCRIPT'
set -e

PROJECT_DIR="/home/ubuntu/python"
DOMAIN="your-domain.com"
MYSQL_DB_PASSWORD="fendou123"
REDIS_PASSWORD="ChangeMeSecureRedisPassword"

echo "📍 工作目录: $PROJECT_DIR"

# ---------- 1. 安装系统依赖（如果尚未安装）----------
echo ""
echo "📦 检查系统依赖..."

missing_deps=()

# 检查 MySQL
if ! command -v mysql &> /dev/null; then
    missing_deps+=("mysql")
fi

# 检查 Redis
if ! command -v redis-server &> /dev/null; then
    missing_deps+=("redis")
fi

# 检查 Nginx
if ! command -v nginx &> /dev/null; then
    missing_deps+=("nginx")
fi

# 检查 Python
if ! command -v python3 &> /dev/null || ! python3 -c "import sys; assert sys.version_info >= (3, 8)" &> /dev/null; then
    missing_deps+=("python3")
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    missing_deps+=("nodejs")
fi

# 检查 Git
if ! command -v git &> /dev/null; then
    missing_deps+=("git")
fi

if [ ${#missing_deps[@]} -gt 0 ]; then
    echo "🔧 安装缺失的系统依赖: ${missing_deps[*]}"
    sudo apt update
    sudo apt install -y mysql-server redis-server nginx \
        python3 python3-venv python3-pip \
        build-essential libmysqlclient-dev libffi-dev \
        git curl
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    sudo systemctl enable --now mysql redis-server nginx 2>/dev/null || true
else
    echo "✅ 系统依赖已满足"
fi

# ---------- 2. 配置后端环境变量 ----------
echo ""
echo "📝 配置后端环境变量..."

cat > "$PROJECT_DIR/backend/.env" << EOF
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=${MYSQL_DB_PASSWORD}
MYSQL_DATABASE=luckapi

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

# JWT & Secret
SECRET_KEY=$(python3 -c "
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
" 2>/dev/null || echo "ChangeMe64CharsMinimumSecureRandomKey")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=2880

# Proxy
PROXY_PREFIX=/api/v1

# Features
ENABLE_QA_RECORDS=false

# CORS
ALLOWED_ORIGINS=https://${DOMAIN},https://${DOMAIN}/admin

# Debug
LUCKAPI_DEBUG=0
EOF

echo "✅ 后端 .env 配置完成"

# ---------- 3. 配置 Nginx ----------
echo ""
echo "🔧 配置 Nginx..."

# 部署优化的站点配置
sudo tee /etc/nginx/sites-available/luckapi > /dev/null << 'NGINX_CONF'
server {
    listen 80;
    server_name your-domain.com;
    
    root /home/ubuntu/python/frontend/dist;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Admin API 代理
    location /admin/api/ {
        proxy_pass http://127.0.0.1:9090/admin/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy API 代理
    location /v1/ {
        proxy_pass http://127.0.0.1:9090/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONF

# 部署主配置（启用 gzip 压缩）
sudo tee /etc/nginx/nginx.conf > /dev/null << 'NGINX_MAIN'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 2048;
    multi_accept on;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_buffers 16 8k;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/x-javascript
        application/xml
        application/xml+rss
        application/vnd.ms-fontobject
        application/x-font-ttf
        font/opentype
        image/svg+xml
        image/x-icon;

    # 代理缓存
    proxy_cache_path /var/cache/nginx/luckyadmin levels=1:2 keys_zone=luckyadmin:10m max_size=500m inactive=60m use_temp_path=off;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
NGINX_MAIN

# 创建缓存目录
sudo mkdir -p /var/cache/nginx/luckyadmin
sudo chown www-data:www-data /var/cache/nginx/luckyadmin

# 启用 nginx 配置
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/luckapi /etc/nginx/sites-enabled/

# 设置目录权限
chmod 755 /home/ubuntu
chmod -R 755 /home/ubuntu/python
chown -R www-data:www-data /home/ubuntu/python/frontend/dist

# 测试并重启 nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx 配置完成"

# ---------- 4. 部署后端 ----------
echo ""
echo "🐍 部署后端服务..."

# 激活 conda luck 环境
export PATH="/home/ubuntu/miniconda3/bin:/home/ubuntu/miniconda3/envs/luck/bin:$PATH"
source /home/ubuntu/miniconda3/etc/profile.d/conda.sh 2>/dev/null || true
conda activate luck 2>/dev/null || true

# 检查并安装依赖
cd "$PROJECT_DIR/backend"
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# 停止可能运行的旧进程
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 2

# 部署 systemd 服务配置
sudo tee /etc/systemd/system/luckapi-backend.service > /dev/null << 'SERVICE'
[Unit]
Description=LuckApi Backend Service (FastAPI)
After=network.target mysql.service redis-server.service

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/python/backend
Environment="PATH=/home/ubuntu/miniconda3/envs/luck/bin"
EnvironmentFile=/home/ubuntu/python/backend/.env

ExecStart=/home/ubuntu/miniconda3/envs/luck/bin/uvicorn main:app \
    --host 127.0.0.1 \
    --port 9090 \
    --workers 2 \
    --loop uvloop \
    --http httptools

Restart=always
RestartSec=10
LimitNOFILE=65535
OOMScoreAdjust=-500
NoNewPrivileges=true
PrivateTmp=true

StandardOutput=journal
StandardError=journal
SyslogIdentifier=luckapi-backend

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable luckapi-backend
sudo systemctl restart luckapi-backend

sleep 2
sudo systemctl status luckapi-backend --no-pager | grep -E "(Active|Loaded)"

echo "✅ 后端服务已启动"

# ---------- 5. 部署前端 ----------
echo ""
echo "🌐 部署前端..."

cd "$PROJECT_DIR/frontend"

if [ -d "node_modules" ]; then
    npm ci --production=false
else
    npm install
fi

npm run build

# 复制构建产物到 nginx 目录
sudo mkdir -p /home/ubuntu/python/frontend/dist
sudo cp -r dist/* /home/ubuntu/python/frontend/dist/

sudo nginx -t && sudo systemctl reload nginx

echo "✅ 前端已部署"

# ---------- 6. 初始化数据库 ----------
echo ""
echo "🗄️  初始化数据库..."

cd "$PROJECT_DIR/backend"
python3 db_init.py

echo "✅ 数据库初始化完成"

# ---------- 验证部署 ----------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 部署完成！"
echo "📍 前端: http://$DOMAIN (或使用 IP: $SERVER_HOST)"
echo "📍 API 文档: http://$DOMAIN/docs"
echo "📍 后端监听: 127.0.0.1:9090"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "后续步骤:"
echo "1. 配置域名并申请 SSL 证书:"
echo "   sudo certbot certonly --nginx -d your-domain.com"
echo "2. 更新 nginx 配置中的 server_name 和 SSL 路径"
echo "3. 防火墙开放 80/443 端口"

REMOTE_SCRIPT
    
    log_step "远程部署完成"
}

# 执行数据库备份和迁移
run_migrate() {
    log_step "在服务器上执行数据库备份和迁移..."
    
    ssh -T -o StrictHostKeyChecking=no -o TCPKeepAlive=yes \
        "${SERVER_USER}@${SERVER_HOST}" << 'REMOTE_SCRIPT'
set -e

PROJECT_DIR="/home/ubuntu/python"
BACKUP_DIR="/home/ubuntu/backups"
MYSQL_DB_PASSWORD="fendou123"

echo "📍 工作目录: $PROJECT_DIR"

# 创建备份目录
sudo mkdir -p "$BACKUP_DIR"
sudo chown "$USER":"$USER" "$BACKUP_DIR" 2>/dev/null || true

# 备份数据库
echo ""
echo "💾 备份数据库..."
BACKUP_FILE="$BACKUP_DIR/luckapi_$(date +%Y%m%d_%H%M%S).sql"

sudo mysqldump -u root -p"${MYSQL_DB_PASSWORD}" luckapi > "$BACKUP_FILE"

echo "✅ 数据库已备份到: $BACKUP_FILE"

# 执行 Alembic 迁移
echo ""
echo "🔄 执行数据库迁移..."

cd "$PROJECT_DIR/backend"

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 检查是否有 Alembic
if command -v alembic &> /dev/null; then
    alembic upgrade head
    echo "✅ Alembic 迁移完成"
else
    # 使用 db_init.py 进行表结构同步
    python3 db_init.py
    echo "✅ 数据库初始化完成（未检测到 Alembic）"
fi

# 清理旧备份（保留最近 7 天）
echo ""
echo "🧹 清理旧备份..."
find "$BACKUP_DIR" -name "luckapi_*.sql" -mtime +7 -delete 2>/dev/null || true
echo "✅ 清理完成"

REMOTE_SCRIPT
    
    log_step "数据库迁移完成"
}

# ---------- 主流程 ----------
main() {
    local action="${1:-deploy}"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   LuckApi 自动部署工具"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "服务器: ${SERVER_USER}@${SERVER_HOST}"
    echo "路径:   ${SERVER_PATH}"
    echo "操作:   ${action}"
    echo ""
    
    case "$action" in
        upload|deploy)
            # 上传 + 部署
            upload_files
            remote_deploy
            ;;
        migrate)
            # 仅执行数据库备份和迁移
            run_migrate
            ;;
        all)
            # 上传 + 部署 + 迁移
            upload_files
            remote_deploy
            run_migrate
            ;;
        *)
            echo "用法: $0 [deploy|migrate|all]"
            echo "  deploy  - 上传文件并执行部署（默认）"
            echo "  migrate - 执行数据库备份和迁移"
            echo "  all     - 上传 + 部署 + 迁移"
            exit 1
            ;;
    esac
    
    echo ""
    log_info "所有操作完成！"
}

main "$@"
