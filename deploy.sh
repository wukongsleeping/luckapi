#!/bin/bash
set -e

echo "=== LuckApi 原生部署脚本 ==="
echo ""

PROJECT_DIR="/opt/LuckApi"
DOMAIN="your-domain.com"    # 修改为你的域名
EMAIL="your@email.com"     # 修改为你的邮箱

# ---------- 安装系统依赖（首次运行） ----------
install_system_deps() {
    echo "📦 安装系统依赖..."
    sudo apt update
    sudo apt install -y mysql-server-8.0 redis-server nginx \
        python3.10 python3.10-venv python3.10-dev python3-pip \
        build-essential libmysqlclient-dev libffi-dev \
        certbot python3-certbot-nginx git ufw \
        software-properties-common
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    sudo systemctl enable --now mysql redis-server nginx
}

# ---------- 数据库初始化 ----------
init_database() {
    echo "🗄️  初始化数据库..."
    sudo bash -c <<SQL
        mysql
CREATE DATABASE IF NOT EXISTS luckapi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'luckapi'@'localhost' IDENTIFIED BY '${MYSQL_DB_PASSWORD:-LuckApi@2025}';
GRANT ALL PRIVILEGES ON luckapi.* TO 'luckapi'@'localhost';
FLUSH PRIVILEGES;
SQL
    if [ -f backend/docker/init.sql ]; then
        mysql luckapi < backend/docker/init.sql
        echo "✅ 初始化 SQL 已执行"
    fi
}

# ---------- 后端部署 ----------
deploy_backend() {
    echo "🐍 部署后端..."
    cd "$PROJECT_DIR/backend"
    python3.10 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
    systemctl daemon-reload
    sudo systemctl enable --now luckapi-backend
    sudo systemctl restart luckapi-backend
    echo "✅ 后端已启动"
}

# ---------- 前端部署 ----------
deploy_frontend() {
    echo "🌐 部署前端..."
    cd "$PROJECT_DIR/frontend"
    npm ci
    npm run build
    sudo nginx -t
    sudo systemctl reload nginx
    echo "✅ 前端已部署"
}

# ---------- SSL 证书 ----------
setup_ssl() {
    echo "🔒 申请 SSL 证书..."
    sudo mkdir -p /var/www/certbot

    sudo tee /etc/nginx/sites-available/certbot << 'NGINX'
server {
    listen 80;
    server_name _;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
NGINX
    sudo ln -sf /etc/nginx/sites-available/certbot /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx

    certbot certonly --webroot \
        --webroot-path=/var/www/certbot \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --redirect

    sudo systemctl reload nginx
    echo "✅ SSL 证书已申请"

    # 自动续期
    (crontab -l 2>/dev/null | grep -v "certbot renew" ; \
     echo "0 3 * * 1 certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
}

# ---------- 防火墙 ----------
setup_firewall() {
    echo "🛡️  配置防火墙..."
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "y" | sudo ufw enable
    echo "✅ 防火墙已配置"
}

# ---------- 安全加固 ----------
hardening() {
    echo "🔐 安全加固..."

    # MySQL 只监听 localhost
    sudo sed -i 's/^bind-address.*/bind-address = 127.0.0.1/' /etc/mysql/mysql.conf.d/mysqld.cnf
    sudo systemctl restart mysql

    # Redis 密码
    if [ -n "$REDIS_PASSWORD" ]; then
        sudo sed -i "s/^# requirepass.*/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
        sudo sed -i 's/^bind.*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
        sudo systemctl restart redis-server
    fi
    echo "✅ 安全加固完成"
}

# ---------- 主流程 ----------
main() {
    echo ""
    echo "⚠️  目标服务器: $PROJECT_DIR"
    echo "⚠️  域名: $DOMAIN"
    echo ""
    read -p "确认部署？(y/N): " confirm
    if [ "$confirm" != "y" ]; then
        echo "❌ 取消部署"
        exit 0
    fi

    # 检查是否已有代码
    if [ ! -d "$PROJECT_DIR" ]; then
        git clone https://your-git-repo-url.git "$PROJECT_DIR"
    fi
    cd "$PROJECT_DIR"

    local step="${1:-all}"

    case "$step" in
        all)
            install_system_deps
            init_database
            deploy_backend
            deploy_frontend
            setup_firewall
            hardening
            setup_ssl
            ;;
        deps)    install_system_deps ;;
        db)      init_database ;;
        backend) deploy_backend ;;
        frontend) deploy_frontend ;;
        ssl)     setup_ssl ;;
        firewall) setup_firewall ;;
        *)       echo "用法: $0 [all|deps|db|backend|frontend|ssl|firewall]"; exit 1 ;;
    esac

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 部署完成！"
    echo "📍 https://$DOMAIN"
    echo "📍 API文档: https://$DOMAIN/docs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

main "$@"
