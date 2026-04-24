# 部署方案

LuckApi 私有云服务器部署文档（Ubuntu/Debian 裸机直接部署）。

---

## 一、WSL 环境准备

> 以下命令在 WSL2（Ubuntu）终端中执行。

```bash
# 1. 系统更新
apt update && apt upgrade -y

# 2. 安装基础工具
apt install -y curl wget git vim htop net-tools

# 3. Windows 防火墙开放端口（在 Windows PowerShell 中执行）
netsh advfirewall firewall add rule name="LuckApi Nginx" protocol=TCP dir=in localport=8080 action=allow
netsh advfirewall firewall add rule name="LuckApi Backend" protocol=TCP dir=in localport=8000 action=allow
```

---

## 二、安装 MySQL 8.0

```bash
# 直接部署
apt install -y mysql-server mysql-client

# 安全初始化（首次需设置 root 密码）
mysql_secure_installation

# 登录并初始化数据库
mysql -u root -p <<EOF
CREATE DATABASE luckapi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

# 验证
mysql -u root -p luckapi -e "SHOW TABLES;"
```

### MySQL 8.0 认证插件兼容

MySQL 8.0 密码认证插件默认为 `caching_sha2_password`，部分 Python 客户端可能不支持。如遇到连接问题，切换为 `mysql_native_password`：

```bash
mysql -u root -p <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'fendou';
FLUSH PRIVILEGES;
EOF
```

---

## 三、安装 Redis 7

```bash
apt install -y redis-server

# WSL2 没有 systemd，使用 service 命令启动
service redis-server start

# 可选：配置密码（编辑 /etc/redis/redis.conf）
# requirepass 替换为强密码
```

---

## 四、安装 Python 3.10+ 与环境

```bash
# 安装 Python 和 venv
# libmysqlclient-dev 是 asyncmy 驱动依赖
apt install -y python3.10 python3.10-venv python3.10-dev python3-pip libmysqlclient-dev

# 后端环境隔离
cd ~/LuckApi
python3 -m venv venv

# 激活虚拟环境（后续所有操作都需要先激活）
source venv/bin/activate

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 创建 .env 配置文件
cat > .env << EOF
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=fendou
MYSQL_DATABASE=luckapi
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
SECRET_KEY=luckapi-secret-key-change-this-in-production
EOF

# 初始化数据库
# 首次运行会自动创建默认管理员账户: admin / admin123
python db_init.py
```

> **提示**：打开新的终端窗口时，需要先 `cd ~/LuckApi && source venv/bin/activate` 激活虚拟环境。

---

## 五、启动服务

> WSL2 没有 systemd，使用 nohup 后台运行。启动前先激活虚拟环境：`cd ~/LuckApi && source venv/bin/activate`

### 启动后端

```bash
cd ~/LuckApi/backend
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/luckapi.log &

# 查看日志
tail -f /tmp/luckapi.log

# 停止
pkill -f "uvicorn main:app"
```

### 重启后端

```bash
pkill -f "uvicorn main:app"
cd ~/LuckApi/backend
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/luckapi.log &
tail -f /tmp/luckapi.log
```

### 开发模式（推荐本地调试）

```bash
cd ~/LuckApi/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 六、Node.js + 前端构建

```bash
# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 安装前端依赖并构建
cd ~/LuckApi/frontend
npm install
npm run build

# 构建产物在 dist/，复制到 Nginx 目录
mkdir -p /var/www/luckapi/frontend
cp -r dist/* /var/www/luckapi/frontend/
```

---

## 七、Nginx 配置（核心反向代理）

```bash
apt install -y nginx

# 站点配置
tee /etc/nginx/sites-available/luckapi << 'EOF'
server {
    listen 8080;
    server_name _;

    root /var/www/luckapi/frontend;
    index index.html;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 代理 API（流式传输需要长超时 + 关闭 buffer）
    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 管理 API 反向代理
    location /admin/api/ {
        proxy_pass http://127.0.0.1:8000/admin/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
        proxy_send_timeout 10s;
    }

    # Swagger 文档（仅开发环境开放）
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
EOF

# 启用站点并测试
rm -f /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/luckapi /etc/nginx/sites-enabled/
nginx -t
nginx -s reload
```

> **注意**：Nginx 监听端口为 **8080**，访问地址为 `http://localhost:8080`

---

## 八、UniApp 移动端打包部署

详见 `uniapp/README.md`。

- 使用 HBuilderX 发行 → 云打包生成 APK
- H5 版：发行 → 网站-H5手机版，将 `dist/build/h5/` 发布内容放置到 `/var/www/luckapi/mobile/`
- Nginx 配置增加 `/mobile/` 反向代理

---

## 九、Nginx 最终参考配置

完整合并配置文件，可直接覆盖 `/etc/nginx/sites-available/luckapi`。

**改动说明**（相比第七节）：增加移动端 `/mobile/` 路径、关闭 `/v1/` 的 buffer（流式传输必需）、优化 `/admin/api/` 的超时避免阻塞。

```nginx
server {
    listen 8080;
    server_name _;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    root /var/www/luckapi/frontend;
    index index.html;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # SPA 路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 代理 API（流式传输：关闭 buffer + 长超时）
    location /v1/ {
        proxy_pass http://127.0.0.1:8000/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 管理 API（连接超时 10s 避免阻塞）
    location /admin/api/ {
        proxy_pass http://127.0.0.1:8000/admin/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
        proxy_send_timeout 10s;
    }

    # Swagger 文档
    location ~ ^/(docs|redoc|openapi\.json)$ {
        proxy_pass http://127.0.0.1:8000$uri;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 移动端 H5
    location /mobile/ {
        alias /var/www/luckapi/mobile/;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 隐藏文件禁止访问
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

---

## 十、访问地址汇总

| 服务 | 地址 |
|------|------|
| 前端管理面板 | `http://localhost:8080/` |
| 后端 API | `http://localhost:8080/admin/api/` |
| 代理接口 | `http://localhost:8080/v1/` |
| Swagger 文档 | `http://localhost:8080/docs`（仅内网） |
| 移动端 H5 | `http://localhost:8080/mobile/` |
| 移动端 APK | HBuilderX 云打包下载 |

---

## 十一、日常运维命令

```bash
# 后端日志
tail -f /tmp/luckapi.log

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# 后端重启（先激活虚拟环境）
pkill -f "uvicorn main:app"
cd ~/LuckApi/backend
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/luckapi.log &

# Nginx 重载
nginx -s reload
```

---

## 十二、自动备份脚本

```bash
tee /usr/local/bin/luckapi-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/luckapi/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -pfendou luckapi > $BACKUP_DIR/luckapi_$DATE.sql
find $BACKUP_DIR -name "luckapi_*.sql" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/luckapi-backup.sh

# 添加定时任务（每天凌晨 2 点自动备份）
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/luckapi-backup.sh") | crontab -
```

---

## 部署检查清单

- [ ] WSL2 Ubuntu 环境已安装并更新
- [ ] Windows 防火墙已开放 8080 和 8000 端口
- [ ] MySQL 8.0 运行，数据库 `luckapi` 已创建
- [ ] MySQL 认证插件已切换为 `mysql_native_password`
- [ ] Redis 7 运行 (`service redis-server status`)
- [ ] Python venv 激活，依赖安装完成
- [ ] `.env` 配置正确（MySQL root/fendou，SECRET_KEY）
- [ ] 运行 `python db_init.py`（自动创建默认管理员: admin/admin123）
- [ ] 记录打印的 API Key，首次使用前修改默认密码
- [ ] 后端 nohup 进程正常运行 (`tail -f /tmp/luckapi.log`)
- [ ] Nginx 配置测试通过（`nginx -t`）
- [ ] 前端构建成功，静态资源放到 `/var/www/luckapi/frontend/`
- [ ] 访问 `http://localhost:8080/` 显示前端页面
- [ ] 访问 `http://localhost:8080/admin/api/` 能到后端
- [ ] 移动端打包完成，H5 静态资源上传
- [ ] Windows 防火墙策略生效
