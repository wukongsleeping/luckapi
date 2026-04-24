<!-- README.md - LuckApi API Gateway Platform -->

# LuckApi

> 自建 AI 模型代理网关 — 轻量、安全、开源

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](./LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-36cf5d)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.0-42b883)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)

[![GitHub Stars](https://img.shields.io/github/stars/luckapi/luckapi?style=social)](https://github.com/luckapi/luckapi)
[![GitHub Issues](https://img.shields.io/github/issues/luckapi/luckapi)](https://github.com/luckapi/luckapi/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/luckapi/luckapi)](https://github.com/luckapi/luckapi/pulls)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/luckapi/luckapi)](https://github.com/luckapi/luckapi)

---

## 什么是 LuckApi？

LuckApi 是一个 **开源的 AI 模型代理网关**，基于 OpenAI 兼容接口，让你能：

1. **统一管理**多模型 API 密钥的代理和转发
2. **用户管理**支持用户分级、角色控制、余额统计
3. **流量管控**API Key 认证、IP 白名单、限流保护
4. **实时监控**SSE 实时推送、审计日志、Q&A 记录导出

适用于：自托管 LLM 服务、企业内部 AI 网关、多模型统一管理、API 成本管控。

---

## 快速开始

### Docker 一键部署（推荐）

```bash
git clone https://github.com/luckapi/luckapi.git
cd luckapi
docker-compose up -d
```

访问：
- 🌐 **前端** http://localhost:80
- 📖 **API 文档** http://localhost:8000/docs
- 📡 **代理接口** http://localhost:8000/v1/chat/completions

### 原生服务器部署

[安装文档 →](./INSTALL.md)

```bash
# 前置：MySQL 8.0 + Redis 7 + Python 3.10+ + Nginx
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库连接

# 初始化数据库（创建默认管理员 admin/admin123）
python db_init.py

# 启动后端
uvicorn main:app --host 127.0.0.1 --port 8000

# 前端
cd ../frontend
npm install && npm run build
```

---

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (端口 8080)                  │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │  SPA     │  │ /admin/api │  │  /v1/ (流式)     │ │
│  │ 静态资源  │  │ 管理面板 API│  │ 代理转发         │ │
│  └──────────┘  └────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────┐
│                     FastAPI (端口 8000)               │
│  ┌────────────────────────────────────────────────┐  │
│  │ 中间件: CORS → 审计 → 限流 → 安全检查           │  │
│  └────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ 用户管理    │  │ 模型管理    │  │ 代理路由    │  │
│  │ JWT 认证     │  │ CRUD CRUD   │  │ 流式转发    │  │
│  └─────────────┘  └─────────────┘  └──────┬──────┘  │
└─────────────────────────┬─────────────────────────────┘
                          │               │
              ┌───────────┴──┐    ┌───────┴───────┐
              │  MySQL 8 /    │    │  Redis 7      │
              │  PostgreSQL   │    │  缓存 / 限流   │
              └──────────────┘    └───────────────┘
```

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 🔐 **用户管理** | 创建/编辑/删除用户，查看余额、用量统计 |
| 🤖 **模型绑定** | 为用户绑定多个上游模型接口，按需路由 |
| 🔑 **API Key** | 自动生成用户专属 API Key，支持更换，Fernet 加密存储 |
| 🛡️ **IP 白名单** | 用户级 IP 白名单限制 |
| 📊 **限流保护** | Redis 基于 API Key 的限流，支持分布式部署 |
| 📝 **审计日志** | 所有 API 调用实时审计，支持 Q&A 记录导出 (JSONL) |
| 🔄 **流式转发** | SSE / Streaming 支持，tenacity 自动重试 |
| 📱 **移动端** | UniApp 客户端，深色主题，原生体验 |
| 📲 **SSE 实时推送** | 代理请求状态实时 WebSocket/SSE 推送 |

---

## 代理接口用法

```bash
# 标准 OpenAI 兼容接口
curl https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

兼容接口规范：
- `POST /v1/chat/completions` — 聊天对话（兼容 ChatGPT API）
- `POST /v1/completions` — 文本补全
- `GET  /v1/models` — 列出可用模型

---

## 技术栈

**后端**：FastAPI 0.115+ · SQLAlchemy 2.0 (async)  · Pydantic v2 · asyncmy · Redis · aiohttp · tenacity  
**前端**：Vue 3 SFC · Vite · Pinia · Element Plus · Vue Router · Axios  
**移动端**：UniApp · Pinia · 深色主题（与 Web 一致）  
**部署**：Docker Compose / Nginx / systemd

---

## 部署方案

| 方案 | 说明 | 适用场景 |
|------|------|---------|
| [Docker Compose](./docker-compose.yml) | 一条命令起全部 | 快速体验、中小部署 |
| [原生服务器](./INSTALL.md) | 分步脚本部署 | 私有云、WSL、生产环境 |
| [一键部署脚本](./deploy.sh) | 含 SSL 证书、防火墙 | 全新服务器裸机部署 |

---

## 项目结构

```
luckapi/
├── backend/              # Python FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置 / 加密 / 安全
│   │   ├── db/           # 数据库会话 / Redis
│   │   ├── middleware/   # 中间件
│   │   ├── models/       # SQLAlchemy ORM
│   │   ├── schemas/      # Pydantic v2
│   │   └── notification.py  # SSE 实时推送
│   ├── db_init.py        # 数据库初始化
│   └── requirements.txt
├── frontend/             # Vue 3 管理面板
│   └── src/
│       ├── api/          # Axios 请求封装
│       ├── views/        # 页面组件
│       ├── components/   # 通用组件
│       ├── store/        # Pinia 状态管理
│       └── router/       # 路由配置
├── uniapp/               # UniApp 移动端
├── nginx/                # Nginx 生产配置
├── docker-compose.yml    # Docker 编排
├── deploy.sh             # 一键部署脚本
└── INSTALL.md            # 详细安装文档
```

---

## 对比

| 特性 | LuckApi | 自建代理脚本 | 商业 API 网关 |
|------|---------|-------------|---------------|
| 用户管理 | ✅ | ❌ | ❌ |
| 模型路由 | ✅ | 需手写 | ❌ |
| 限流保护 | ✅ | ❌ | ✅ |
| 审计日志 | ✅ | ❌ | ❌ |
| 流量统计 | ✅ | ❌ | ✅ |
| 移动端 | ✅ | ❌ | ❌ |
| 开源免费 | ✅ | ✅ | 💰 |
| 部署方式 | Docker / 原生 | Python | 云托管 |

---

## 路线图

- [x] 用户 / 模型 CRUD
- [x] API Key 自动生成 + Fernet 加密
- [x] Redis 限流 + 审计日志
- [x] SSE 实时推送
- [x] Q&A 记录导出
- [x] UniApp 移动端
- [ ] 模型负载均衡
- [ ] Token 用量统计 & 计费
- [ ] GraphQL API
- [ ] 多租户支持

---

## 开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

---

## 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。

如有问题，请 [提交 Issue](https://github.com/luckapi/luckapi/issues) 或发起 [Discussion](https://github.com/luckapi/luckapi/discussions)。

---

## 许可证

本项目采用 [Apache 2.0 许可证](./LICENSE)。
